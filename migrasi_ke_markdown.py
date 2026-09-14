# -*- coding: utf-8 -*-
"""Pindahkan 239 artikel arsip dari data/artikel.json menjadi tulisan/<slug>.md
supaya bisa disunting di editor /admin/ (Decap CMS).

    py migrasi_ke_markdown.py              tulis artikel yang belum punya berkas .md
    py migrasi_ke_markdown.py --timpa-isi  tulis ulang ISI semua berkas .md arsip,
                                           front-matter yang sudah ada dibiarkan

PERINGATAN: --timpa-isi menimpa suntingan isi yang dibuat lewat editor. Pakai
hanya sebelum artikel mulai disunting.

Nama berkas = slug lama, jadi alamat artikel di situs tidak berubah.
"""
import json, os, re, subprocess, sys

import yaml
from markdownify import markdownify

import bangun_situs as B   # dipakai hanya untuk bersihkan() dan kunci_gambar()

AKAR = B.AKAR
DATA = os.path.join(AKAR, "data")
TULISAN = os.path.join(AKAR, "tulisan")
GAMBAR_TULISAN = os.path.join(TULISAN, "gambar")
GAMBAR_ARSIP = os.path.join(DATA, "gambar")

IFRAME = re.compile(r'<iframe\b[^>]*\bsrc="([^"]+)"[^>]*>(?:\s*</iframe>)?', re.I)

# Di arsip, penomoran sering berupa TEKS biasa di awal paragraf ("1. Malam
# Nishfu ..."), bukan <ol>. Kalau dibiarkan, Markdown mengubahnya jadi daftar
# otomatis yang nomornya mulai ulang dari 1 setiap kali diselingi paragraf lain.
# "1)" aman di Python-Markdown, tapi editor Decap (CommonMark) membacanya
# sebagai daftar dan bisa menulis ulang saat disimpan. Keduanya di-escape: 1\.
# Hanya di awal paragraf / sesudah <br>, jadi <ol> asli tetap daftar.
AWAL_BERNOMOR = re.compile(
    r'((?:<p\b[^>]*>|<br\s*/?>)\s*(?:<(?:strong|b|em|i)\b[^>]*>\s*)*)(\d{1,3})([.)])(?=\s|&nbsp;|\xa0)',
    re.I)
TANDA = "QZESCAPEQZ"


def ke_markdown(isi_html):
    video = []
    for src in IFRAME.findall(isi_html):
        if src.startswith("//"):
            src = "https:" + src
        if src not in video:
            video.append(src)

    h = IFRAME.sub("", isi_html)
    h = re.sub(r'<p>\s*</p>', '', h)
    h = AWAL_BERNOMOR.sub(lambda m: m.group(1) + m.group(2) + TANDA + m.group(3), h)

    teks = markdownify(h, heading_style="ATX", bullets="-", strip=["iframe"])
    teks = teks.replace(TANDA, "\\")
    teks = re.sub(r'\n{3,}', '\n\n', teks).strip()
    return teks, video


def main():
    timpa_isi = "--timpa-isi" in sys.argv[1:]
    os.makedirs(GAMBAR_TULISAN, exist_ok=True)

    arsip = json.load(open(os.path.join(DATA, "artikel.json"), encoding="utf-8"))
    gambar_lokal = json.load(open(os.path.join(DATA, "gambar_lokal.json"), encoding="utf-8"))
    peta_gambar = json.load(open(os.path.join(DATA, "peta_gambar.json"), encoding="utf-8"))

    baru, isi_ditimpa, dilewati, dipindah, hilang = 0, 0, [], 0, []

    for r in arsip:
        slug = r["slug"]
        berkas = gambar_lokal.get(slug, "")
        kunci = B.kunci_gambar((peta_gambar.get(slug) or {}).get("asli", ""))
        badan, video = ke_markdown(B.bersihkan(r["isi_html"], slug, berkas, kunci))
        tujuan = os.path.join(TULISAN, slug + ".md")

        if os.path.exists(tujuan):
            if not timpa_isi:
                dilewati.append(slug)
                continue
            lama = open(tujuan, encoding="utf-8").read()
            m = re.match(r'^(---\n.*?\n---\n)', lama, re.S)
            if not m:
                sys.exit("Front-matter %s tidak terbaca — dihentikan, tidak ada yang ditimpa." % tujuan)
            with open(tujuan, "w", encoding="utf-8", newline="\n") as f:
                f.write(m.group(1) + "\n" + badan + "\n")
            isi_ditimpa += 1
            continue

        gambar = ""
        if berkas:
            asal = os.path.join(GAMBAR_ARSIP, berkas)
            akhir = os.path.join(GAMBAR_TULISAN, berkas)
            if os.path.exists(akhir):
                gambar = "/gambar/" + berkas
            elif os.path.exists(asal):
                subprocess.run(["git", "mv", asal, akhir], check=True, cwd=AKAR)
                gambar = "/gambar/" + berkas
                dipindah += 1
            else:
                hilang.append(slug)

        kepala = {
            "judul": r["judul"],
            "tanggal": (r["tanggal_terbit"] or "")[:10],
            # jam asli untuk mengurutkan artikel yang terbit di hari yang sama
            "waktu_terbit": r["tanggal_terbit"] or "",
            "penulis": r["penulis"],
            "kategori": list(r["kategori"] or ["Artikel"]),
            "gambar": gambar,
            "video": " ".join(video),
            "draf": False,
        }
        yml = yaml.safe_dump(kepala, allow_unicode=True, sort_keys=False,
                             default_flow_style=False, width=10000)
        with open(tujuan, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\n" + yml + "---\n\n" + badan + "\n")
        baru += 1

    print("Artikel baru ditulis : %d" % baru)
    print("Isi ditimpa          : %d%s" % (isi_ditimpa, "" if timpa_isi else "  (pakai --timpa-isi)"))
    print("Sudah ada, dilewati  : %d" % len(dilewati))
    print("Gambar dipindahkan   : %d" % dipindah)
    print("Gambar tak ketemu    : %d %s" % (len(hilang), hilang[:5]))


if __name__ == "__main__":
    main()
