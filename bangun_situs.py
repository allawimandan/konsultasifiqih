# -*- coding: utf-8 -*-
"""Bangun situs statis konsultasifiqih.com dari arsip Wayback.

URL artikel sengaja dipertahankan persis seperti situs aslinya (/nama-artikel/)
supaya tautan lama dan hasil indeks Google yang masih beredar tetap hidup.
Keluaran siap diunggah apa adanya ke Cloudflare Pages.
"""
import json, os, re, shutil, html as htmlmod, unicodedata
from datetime import datetime, timezone

AKAR = os.path.dirname(os.path.abspath(__file__))
ARSIP = os.path.join(AKAR, "data")      # data arsip ikut di dalam repo
SUMBER = os.path.join(AKAR, "sumber")
KELUAR = os.path.join(AKAR, "keluaran")

DOMAIN = "https://konsultasifiqih.com"
NAMA = "konsultasifiqih.com"
TAGLINE = "Konsultasi Syariah, Solusi Ibadah"
DESKRIPSI = ("Arsip artikel konsultasifiqih.com — tanya jawab fiqih asuhan "
             "Ustadz Dr. Awwaluz Zikri, Lc. MA.")
PER_HALAMAN = 24

BULAN = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli',
         'Agustus', 'September', 'Oktober', 'November', 'Desember']


# ---------------------------------------------------------------- alat bantu

def slugkan(teks):
    t = unicodedata.normalize("NFKD", str(teks)).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "lain"


def aman(s):
    return htmlmod.escape(str(s if s is not None else ""), quote=True)


def tanggal_panjang(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    if not m:
        return ""
    return "%d %s %s" % (int(m.group(3)), BULAN[int(m.group(2)) - 1], m.group(1))


def rfc822(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})", str(iso or ""))
    if not m:
        return ""
    dt = datetime(*[int(x) for x in m.groups()], tzinfo=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def tulis(jalur_relatif, isi):
    penuh = os.path.join(KELUAR, jalur_relatif)
    os.makedirs(os.path.dirname(penuh), exist_ok=True)
    with open(penuh, "w", encoding="utf-8") as f:
        f.write(isi)


# ---------------------------------------------------------------- pembersihan

ATRIBUT_BUANG = re.compile(
    r'\s+(?:class|id|style|width|height|srcset|sizes|decoding|itemprop|role'
    r'|data-[\w-]+|aria-[\w-]+|title|border|align|cellpadding|cellspacing)'
    r'\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)
TAG_BUANG = re.compile(r'</?(?:span|font|figure|figcaption|section|header|footer|nav|button)\b[^>]*>', re.I)
KOSONG = re.compile(r'<p>\s*(?:&nbsp;|\s)*</p>', re.I)
ARAB = re.compile(r'[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]')


def berat_arab(teks):
    huruf = re.sub(r'[\s\d\W_]', '', teks, flags=re.UNICODE)
    return len(ARAB.findall(huruf)) / len(huruf) if len(huruf) >= 8 else 0.0


def kunci_gambar(u):
    u = re.sub(r'^https?://', '', str(u or ""))
    u = re.sub(r'^i\d\.wp\.com/', '', u)
    u = re.sub(r'^www\.', '', u).split("?")[0]
    return u.lower()


def bersihkan(h, slug, berkas_gambar, kunci_utama):
    h = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', h, flags=re.S | re.I)
    h = ATRIBUT_BUANG.sub('', h)
    h = TAG_BUANG.sub('', h)
    h = re.sub(r'<div>', '<p>', h, flags=re.I)
    h = re.sub(r'</div>', '</p>', h, flags=re.I)
    for _ in range(4):
        h = KOSONG.sub('', h)
        h = re.sub(r'<p>\s*<p>', '<p>', h, flags=re.I)
        h = re.sub(r'</p>\s*</p>', '</p>', h, flags=re.I)
    h = re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', h, flags=re.I)

    # tautan lama ke domain sendiri -> tautan relatif (struktur URL-nya sama)
    h = re.sub(r'href="https?://(?:www\.)?konsultasifiqih\.com/([^"/?#]+)/?"',
               lambda m: 'href="/%s/"' % m.group(1), h, flags=re.I)
    # tautan keluar dibuka di tab baru
    h = re.sub(r'<a href="(https?://(?!konsultasifiqih\.com)[^"]+)"',
               r'<a href="\1" target="_blank" rel="noopener"', h, flags=re.I)

    # gambar dalam isi: pakai berkas lokal bila cocok, kalau tidak dibuang
    def ganti_img(m):
        src = m.group(1)
        if berkas_gambar and kunci_gambar(src) == kunci_utama:
            return '<img src="/gambar/%s" alt="" loading="lazy">' % berkas_gambar
        return ''
    h = re.sub(r'<img[^>]+src="([^"]+)"[^>]*>', ganti_img, h, flags=re.I)

    def tandai(m):
        polos = htmlmod.unescape(re.sub(r'<[^>]+>', '', m.group(1)))
        return '<p lang="ar">%s</p>' % m.group(1) if berat_arab(polos) > 0.5 else m.group(0)
    h = re.sub(r'<p>(.*?)</p>', tandai, h, flags=re.S)

    h = re.sub(r'[ \t]{2,}', ' ', h)
    return re.sub(r'\n{3,}', '\n\n', h).strip()


# ---------------------------------------------------------------- muat data

artikel = json.load(open(os.path.join(ARSIP, "artikel.json"), encoding="utf-8"))
halaman_statis = json.load(open(os.path.join(ARSIP, "halaman.json"), encoding="utf-8"))
gambar_lokal = json.load(open(os.path.join(ARSIP, "gambar_lokal.json"), encoding="utf-8"))
peta_gambar = json.load(open(os.path.join(ARSIP, "peta_gambar.json"), encoding="utf-8"))

LEWATI_HALAMAN = {"sample-page", "sample-page-2", "laman-contoh"}
halaman_statis = [h for h in halaman_statis if h["slug"] not in LEWATI_HALAMAN]

# catatan per artikel yang dipakai berulang kali
POS = []
for r in artikel:
    berkas = gambar_lokal.get(r["slug"], "")
    kunci = kunci_gambar((peta_gambar.get(r["slug"]) or {}).get("asli", ""))
    kat = (r["kategori"] or ["Artikel"])[0]
    ringkas = re.sub(r'\s+', ' ', r["isi_teks"])[:180].strip()
    if len(ringkas) == 180:
        ringkas = ringkas.rsplit(" ", 1)[0] + "…"
    POS.append({
        "slug": r["slug"], "judul": r["judul"], "tanggal": r["tanggal_terbit"],
        "penulis": r["penulis"], "kategori": r["kategori"] or ["Artikel"], "kat": kat,
        "ringkas": ringkas, "kata": r["jumlah_kata"], "video": r["jenis"] == "video",
        "gambar": berkas, "kunci_gambar": kunci,
        "isi": bersihkan(r["isi_html"], r["slug"], berkas, kunci),
        "teks": r["isi_teks"],
    })


# ------------------------------------------------- artikel baru (tulisan/*.md)

TULISAN = os.path.join(AKAR, "tulisan")
GAMBAR_BARU = os.path.join(TULISAN, "gambar")


def _bersih_nilai(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v.strip()


def _depan(teks):
    """Baca front-matter di antara dua garis '---'.

    Menerima gaya tulis tangan (`kategori: A, B`) maupun gaya yang ditulis
    editor web Decap (daftar YAML berbutir, boolean true/false, tanggal ISO).
    """
    m = re.match(r'^﻿?---\s*\n(.*?)\n---\s*\n?(.*)$', teks, re.S)
    if not m:
        return {}, teks

    kepala, kunci_kini = {}, None
    for baris in m.group(1).split("\n"):
        if not baris.strip() or baris.strip().startswith("#"):
            continue
        butir = re.match(r'^\s*-\s+(.*)$', baris)
        if butir and kunci_kini:                      # butir daftar YAML
            kepala.setdefault(kunci_kini + "__daftar", []).append(_bersih_nilai(butir.group(1)))
            continue
        if ":" in baris:
            k, v = baris.split(":", 1)
            kunci_kini = k.strip().lower()
            kepala[kunci_kini] = _bersih_nilai(v)
    # daftar YAML menang atas nilai kosong di baris kuncinya
    for k in [x for x in kepala if x.endswith("__daftar")]:
        kepala[k[:-9]] = ", ".join(kepala.pop(k))
    return kepala, m.group(2)


def _boolean(v):
    return str(v).strip().lower() in ("ya", "yes", "true", "1", "benar")


def _tanggal(v):
    """Terima 2026-09-12, 2026-09-12T08:00:00.000Z, atau kosong."""
    v = str(v or "").strip()
    if not v:
        return ""
    if re.match(r'^\d{4}-\d{2}-\d{2}$', v):
        return v + "T08:00:00+00:00"
    m = re.match(r'^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})', v)
    if m:
        return "%sT%s+00:00" % (m.group(1), m.group(2))
    return v


def siapkan_baru(h):
    """Rapikan HTML hasil Markdown: tandai paragraf Arab, tautan luar ke tab baru."""
    h = re.sub(r'<a href="(https?://(?!konsultasifiqih\.com)[^"]+)"',
               r'<a href="\1" target="_blank" rel="noopener"', h, flags=re.I)

    def tandai(m):
        polos = htmlmod.unescape(re.sub(r'<[^>]+>', '', m.group(1)))
        return '<p lang="ar">%s</p>' % m.group(1) if berat_arab(polos) > 0.5 else m.group(0)
    return re.sub(r'<p>(.*?)</p>', tandai, h, flags=re.S)


def muat_tulisan_baru():
    """Baca tulisan/*.md dan ubah jadi artikel, sejajar dengan artikel arsip."""
    if not os.path.isdir(TULISAN):
        return [], []
    try:
        import markdown as md_lib
    except ImportError:
        print("!! Pustaka 'markdown' belum terpasang. Jalankan:  py -m pip install markdown")
        return [], []

    baru, draf = [], []
    for nama in sorted(os.listdir(TULISAN)):
        if not nama.endswith(".md") or nama.startswith("_"):
            continue
        jalur = os.path.join(TULISAN, nama)
        kepala, badan = _depan(open(jalur, encoding="utf-8").read())
        slug = kepala.get("slug") or slugkan(os.path.splitext(nama)[0])

        if _boolean(kepala.get("draf", "")):
            draf.append(slug)
            continue

        judul = kepala.get("judul") or slug.replace("-", " ").title()
        tanggal = _tanggal(kepala.get("tanggal"))
        kategori = [k.strip() for k in (kepala.get("kategori") or "Fikih").split(",") if k.strip()]

        isi_html = siapkan_baru(md_lib.markdown(badan, extensions=["extra", "sane_lists"]))
        teks = htmlmod.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', isi_html))).strip()

        ringkas = kepala.get("ringkas") or teks[:180]
        if len(ringkas) >= 180:
            ringkas = ringkas.rsplit(" ", 1)[0] + "…"

        baru.append({
            "slug": slug, "judul": judul, "tanggal": tanggal,
            "penulis": kepala.get("penulis") or "Ustadz Dr. Awwaluz Zikri, Lc. MA",
            "kategori": kategori, "kat": kategori[0], "ringkas": ringkas,
            "kata": len(re.findall(r'\w+', teks)),
            # Decap menulis jalur penuh ("/gambar/catur.jpg"), tulis tangan cukup namanya
            "video": False, "gambar": os.path.basename(kepala.get("gambar", "").strip()),
            "kunci_gambar": "",
            "isi": isi_html, "teks": teks, "baru": True, "berkas": nama,
        })
    return baru, draf


TULISAN_BARU, DRAF = muat_tulisan_baru()
_slug_arsip = {p["slug"] for p in POS}
BENTROK = [p["slug"] for p in TULISAN_BARU if p["slug"] in _slug_arsip]
POS = [p for p in POS if p["slug"] not in {q["slug"] for q in TULISAN_BARU}] + TULISAN_BARU

POS.sort(key=lambda p: p["tanggal"] or "", reverse=True)
POPULER = sorted(POS, key=lambda p: -p["kata"])[:5]
TERBARU = POS[:5]

KATEGORI = {}
for p in POS:
    for k in p["kategori"]:
        KATEGORI.setdefault(k, []).append(p)
KAT_SLUG = {k: slugkan(k) for k in KATEGORI}


# ---------------------------------------------------------------- potongan HTML

IKON_JAM = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'

SOSIAL = {
    "Facebook": 'M22 12a10 10 0 1 0-11.6 9.9v-7h-2.5V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.4h-1.2c-1.2 0-1.6.8-1.6 1.6V12h2.7l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z',
    "Instagram": 'M12 2.2c3.2 0 3.6 0 4.9.1 1.2.1 1.8.2 2.2.4.6.2 1 .5 1.4.9.4.4.7.8.9 1.4.2.4.4 1 .4 2.2.1 1.3.1 1.7.1 4.9s0 3.6-.1 4.9c-.1 1.2-.2 1.8-.4 2.2-.2.6-.5 1-.9 1.4-.4.4-.8.7-1.4.9-.4.2-1 .4-2.2.4-1.3.1-1.7.1-4.9.1s-3.6 0-4.9-.1c-1.2-.1-1.8-.2-2.2-.4-.6-.2-1-.5-1.4-.9-.4-.4-.7-.8-.9-1.4-.2-.4-.4-1-.4-2.2C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.9c.1-1.2.2-1.8.4-2.2.2-.6.5-1 .9-1.4.4-.4.8-.7 1.4-.9.4-.2 1-.4 2.2-.4C8.4 2.2 8.8 2.2 12 2.2zm0 3.1A6.7 6.7 0 1 0 18.7 12 6.7 6.7 0 0 0 12 5.3zm0 11A4.3 4.3 0 1 1 16.3 12 4.3 4.3 0 0 1 12 16.3zm6.9-11.3a1.6 1.6 0 1 1-1.6-1.6 1.6 1.6 0 0 1 1.6 1.6z',
    "YouTube": 'M23 7.5a3 3 0 0 0-2.1-2.1C19 4.9 12 4.9 12 4.9s-7 0-8.9.5A3 3 0 0 0 1 7.5 31 31 0 0 0 .5 12 31 31 0 0 0 1 16.5a3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.5 31 31 0 0 0-.5-4.5zM9.8 15.3V8.7l5.7 3.3z',
    "X": 'M18.2 2.2h3.3l-7.2 8.3 8.5 11.3h-6.7l-5.2-6.9-6 6.9H1.6l7.7-8.9L1.2 2.2h6.8l4.7 6.3zm-1.2 17.7h1.9L7.1 4.2H5.1z',
    "TikTok": 'M16.6 5.8a4.8 4.8 0 0 1-1.1-3.1h-3.3v13.1a2.6 2.6 0 1 1-1.8-2.5V9.9a5.9 5.9 0 1 0 5.1 5.8V9.1a8.2 8.2 0 0 0 4.7 1.5V7.3a4.8 4.8 0 0 1-3.6-1.5z',
}


def ikon_sosial(kelas):
    return ('<nav class="%s" aria-label="Media sosial">' % kelas) + "".join(
        '<a href="#" aria-label="%s"><svg viewBox="0 0 24 24"><path d="%s"/></svg></a>' % (n, d)
        for n, d in SOSIAL.items()) + '</nav>'


def blok_gambar(p, kelas_ganti=""):
    if p["gambar"]:
        return ('<img src="/gambar/%s" alt="%s" loading="lazy" data-kategori="%s">'
                % (p["gambar"], aman(p["judul"]), aman(p["kat"])))
    n = 0
    for ch in p["slug"]:
        n = (n * 31 + ord(ch)) & 0xFFFFFFFF
    warna = [('#7b2d3f', '#de214a'), ('#1f3a5f', '#2f6f9f'), ('#2f5d50', '#4e9c81'),
             ('#5a3b7c', '#9a6bbf'), ('#6b4423', '#c08457'), ('#3a3f58', '#6b7299'),
             ('#7c3626', '#d2703f'), ('#26525c', '#4e909c')][n % 8]
    return ('<div class="ganti%s" style="background:linear-gradient(135deg,%s,%s)">'
            '<span>%s</span></div>' % (kelas_ganti, warna[0], warna[1], aman(p["kat"])))


def kartu(p):
    return ('<article class="kartu">'
            '<a class="kartu-gambar" href="/%s/">%s<span class="chip">%s</span>%s</a>'
            '<div class="kartu-isi"><h3><a href="/%s/">%s</a></h3>'
            '<span class="tanggal">%s%s</span><p>%s</p></div></article>'
            % (p["slug"], blok_gambar(p), aman(p["kat"]),
               ('<span class="tanda-video" aria-label="Artikel video">'
                '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>') if p["video"] else "",
               p["slug"], aman(p["judul"]), IKON_JAM, tanggal_panjang(p["tanggal"]),
               aman(p["ringkas"])))


def bilah_sisi():
    pop = "".join(
        '<li><div><a href="/%s/">%s</a><div class="tanggal">%s%s</div></div></li>'
        % (p["slug"], aman(p["judul"]), IKON_JAM, tanggal_panjang(p["tanggal"]))
        for p in POPULER)
    baru = "".join(
        '<li><a class="thumb" href="/%s/">%s</a><div><a href="/%s/">%s</a>'
        '<div class="tanggal">%s%s</div></div></li>'
        % (p["slug"], blok_gambar(p), p["slug"], aman(p["judul"]),
           IKON_JAM, tanggal_panjang(p["tanggal"]))
        for p in TERBARU)
    return ('<aside class="sisi">'
            '<section><h4>Populer</h4><ol class="populer">%s</ol></section>'
            '<section><h4>Terbaru</h4><ul class="ringkas">%s</ul></section>'
            '</aside>' % (pop, baru))


def penomoran(dasar, kini, total):
    if total <= 1:
        return ""
    def taut(n, teks=None, kelas=""):
        alamat = dasar if n == 1 else "%s%d/" % (dasar, n)
        if n == kini:
            return '<span class="kini">%s</span>' % (teks or n)
        return '<a href="%s"%s>%s</a>' % (alamat, (' class="%s"' % kelas) if kelas else "", teks or n)
    bagian = []
    if kini > 1:
        bagian.append(taut(kini - 1, "‹ Sebelumnya"))
    tampil = sorted({1, total, kini - 1, kini, kini + 1} & set(range(1, total + 1)))
    lalu = 0
    for n in tampil:
        if lalu and n - lalu > 1:
            bagian.append('<span class="antara">…</span>')
        bagian.append(taut(n))
        lalu = n
    if kini < total:
        bagian.append(taut(kini + 1, "Berikutnya ›"))
    return '<nav class="halaman-nav" aria-label="Penomoran halaman">%s</nav>' % "".join(bagian)


MENU = [("beranda", "Beranda", "/"), ("blog", "Blog", "/blog/"),
        ("kategori", "Kategori", "/kategori/"), ("tentang", "Tentang", "/tentang-kami/"),
        ("kontak", "Kontak", "/kontak/")]


def tata_letak(isi, judul, deskripsi, kanonik, aktif="", og_gambar="", jenis_og="website"):
    menu = "".join('<a href="%s"%s>%s</a>' % (u, ' class="aktif"' if k == aktif else "", n)
                   for k, n, u in MENU)
    kaki_kat = "".join(
        '<li><a href="/kategori/%s/">%s (%d)</a></li>' % (KAT_SLUG[k], aman(k), len(v))
        for k, v in sorted(KATEGORI.items(), key=lambda kv: -len(kv[1]))[:14])
    gambar_og = og_gambar or (DOMAIN + "/gambar/logo.png")

    return f"""<!DOCTYPE html>
<html lang="id" prefix="og: https://ogp.me/ns#">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{aman(judul)}</title>
<meta name="description" content="{aman(deskripsi)}">
<link rel="canonical" href="{aman(kanonik)}">
<meta property="og:type" content="{jenis_og}">
<meta property="og:site_name" content="{NAMA}">
<meta property="og:locale" content="id_ID">
<meta property="og:title" content="{aman(judul)}">
<meta property="og:description" content="{aman(deskripsi)}">
<meta property="og:url" content="{aman(kanonik)}">
<meta property="og:image" content="{aman(gambar_og)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/gambar/logo.png" type="image/png">
<link rel="alternate" type="application/rss+xml" title="{NAMA}" href="/feed.xml">
<link rel="stylesheet" href="/aset/gaya.css">
<script>try{{var t=localStorage.getItem('tema');if(t)document.documentElement.setAttribute('data-tema',t);}}catch(e){{}}</script>
</head>
<body>
<a class="lewati" href="#isi">Lompat ke isi</a>

<header class="kepala">
  <div class="wadah">
    <div class="kepala-atas">
      {ikon_sosial('sosial')}
      <a class="merek" href="/"><img src="/gambar/logo.png" alt="{NAMA}" width="88" height="88"></a>
      <div class="alat">
        <button id="tombol-tema" aria-label="Ganti mode gelap/terang" title="Mode gelap">
          <svg viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
        <button id="tombol-cari" aria-label="Cari artikel" title="Cari">
          <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        </button>
      </div>
    </div>
    <nav class="menu">{menu}</nav>
  </div>
  <div class="cari-kotak sembunyi" id="cari-kotak">
    <div class="wadah">
      <input type="search" id="cari" placeholder="Cari artikel… (judul, isi, kategori)" autocomplete="off">
    </div>
  </div>
</header>

<main id="isi">{isi}</main>

<footer class="kaki">
  <div class="wadah">
    <div class="kaki-kisi">
      <div class="kaki-merek">
        <img src="/gambar/logo.png" alt="{NAMA}" width="86" height="86" loading="lazy">
        <p>{DESKRIPSI}</p>
        {ikon_sosial('kaki-sosial')}
      </div>
      <div><h5>Kategori</h5><ul class="kaki-daftar dua">{kaki_kat}</ul></div>
      <div><h5>Link Penting</h5><ul class="kaki-daftar">
        <li><a href="/blog/">Blog</a></li>
        <li><a href="/kategori/">Kategori</a></li>
        <li><a href="/arsip/">Arsip per Tahun</a></li>
        <li><a href="/tentang-kami/">Tentang Kami</a></li>
        <li><a href="/kontak/">Kontak</a></li>
        <li><a href="/feed.xml">RSS</a></li>
      </ul></div>
    </div>
    <div class="kaki-bawah">
      <span>©Copyright {NAMA}. All Rights Reserved</span>
      <span>{len(POS)} artikel · arsip 2016–2026</span>
    </div>
  </div>
</footer>

<script src="/aset/situs.js" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------- halaman

def judul_bagian(teks):
    return '<div class="bagian-judul"><h2>%s</h2></div>' % aman(teks)


def buat_beranda():
    pilihan = [p for p in POS if p["gambar"]][:4] or POS[:4]
    dipakai = {p["slug"] for p in pilihan}
    syariah = [p for p in POS if p["slug"] not in dipakai and
               any(re.search(r'konsultasi|syariah|fikih|fiqih', k, re.I) for k in p["kategori"])][:4]
    terbaru = [p for p in POS if p["slug"] not in dipakai][:10]

    isi = ('<div class="wadah">'
           '<section class="bagian">%s<div class="kisi kisi-4">%s</div></section>'
           % (judul_bagian("Pilihan Penulis"), "".join(kartu(p) for p in pilihan)))
    if syariah:
        isi += ('<section class="bagian">%s<div class="kisi kisi-4">%s</div></section>'
                % (judul_bagian("Konsultasi Syariah"), "".join(kartu(p) for p in syariah)))
    isi += ('<section class="bagian susun"><div>%s<div class="kisi kisi-2">%s</div>'
            '<div class="tengah"><a class="tombol" href="/blog/">Lihat Semua Artikel</a></div></div>'
            '%s</section></div>'
            % (judul_bagian("Artikel Terbaru"), "".join(kartu(p) for p in terbaru), bilah_sisi()))

    tulis("index.html", tata_letak(
        isi, "%s - %s" % (NAMA, TAGLINE), DESKRIPSI, DOMAIN + "/", "beranda"))


def buat_daftar(daftar, dasar, judul, deskripsi, aktif="", catatan=""):
    """Halaman daftar artikel + penomoran. `dasar` diawali dan diakhiri '/'."""
    total = max(1, (len(daftar) + PER_HALAMAN - 1) // PER_HALAMAN)
    for n in range(1, total + 1):
        potongan = daftar[(n - 1) * PER_HALAMAN: n * PER_HALAMAN]
        tajuk = judul if n == 1 else "%s - Halaman %d" % (judul, n)
        kanonik = DOMAIN + dasar + ("" if n == 1 else "%d/" % n)
        catat = ('<p style="margin:-14px 0 22px;color:var(--meta);font-size:14px">%s</p>'
                 % aman(catatan)) if (catatan and n == 1) else ""
        isi = ('<div class="wadah"><section class="bagian susun"><div>%s%s'
               '<div class="kisi kisi-2">%s</div>%s</div>%s</section></div>'
               % (judul_bagian(tajuk), catat,
                  "".join(kartu(p) for p in potongan) or '<p>Belum ada artikel.</p>',
                  penomoran(dasar, n, total), bilah_sisi()))
        berkas = (dasar.strip("/") + "/index.html") if n == 1 \
            else "%s%d/index.html" % (dasar.lstrip("/"), n)
        tulis(berkas, tata_letak(isi, "%s - %s" % (tajuk, NAMA), deskripsi, kanonik, aktif))
    return total


def buat_kategori():
    kartu_kat = []
    for k, v in sorted(KATEGORI.items(), key=lambda kv: -len(kv[1])):
        contoh = next((p for p in v if p["gambar"]), v[0])
        gbr = ('<img src="/gambar/%s" alt="%s" loading="lazy">' % (contoh["gambar"], aman(k))
               if contoh["gambar"] else blok_gambar(contoh))
        kartu_kat.append(
            '<a class="kartu" href="/kategori/%s/"><span class="kartu-gambar">%s'
            '<span class="chip">%d artikel</span></span>'
            '<div class="kartu-isi"><h3>%s</h3></div></a>'
            % (KAT_SLUG[k], gbr, len(v), aman(k)))
    isi = ('<div class="wadah"><section class="bagian">%s'
           '<div class="kisi kisi-4">%s</div></section></div>'
           % (judul_bagian("Kategori"), "".join(kartu_kat)))
    tulis("kategori/index.html", tata_letak(
        isi, "Kategori - %s" % NAMA,
        "Daftar %d kategori artikel fiqih di %s." % (len(KATEGORI), NAMA),
        DOMAIN + "/kategori/", "kategori"))

    for k, v in KATEGORI.items():
        buat_daftar(v, "/kategori/%s/" % KAT_SLUG[k], k,
                    "Kumpulan %d artikel kategori %s di %s." % (len(v), k, NAMA), "kategori")


def buat_arsip():
    tahun = {}
    for p in POS:
        t = (p["tanggal"] or "")[:4]
        if t:
            tahun.setdefault(t, []).append(p)
    bagian = []
    for t in sorted(tahun, reverse=True):
        daftar = "".join('<li><a href="/%s/">%s</a></li>' % (p["slug"], aman(p["judul"]))
                         for p in tahun[t])
        bagian.append('<h3 style="margin:26px 0 10px">%s <span style="color:var(--meta);'
                      'font-weight:400;font-size:15px">(%d artikel)</span></h3>'
                      '<ul class="kaki-daftar dua" style="font-size:14.5px">%s</ul>'
                      % (t, len(tahun[t]), daftar))
    isi = ('<div class="wadah"><section class="bagian">%s%s</section></div>'
           % (judul_bagian("Arsip per Tahun"), "".join(bagian)))
    tulis("arsip/index.html", tata_letak(
        isi, "Arsip per Tahun - %s" % NAMA,
        "Seluruh %d artikel %s disusun per tahun terbit." % (len(POS), NAMA),
        DOMAIN + "/arsip/"))


IKON_WA = ('M12 2a10 10 0 0 0-8.6 15l-1.3 4.8 5-1.3A10 10 0 1 0 12 2zm5.8 14.2c-.2.7-1.2 1.3-1.9 '
           '1.4-.5.1-1.1.2-3.7-.8-3.1-1.3-5-4.4-5.2-4.6-.1-.2-1.2-1.6-1.2-3s.7-2.1 1-2.4c.3-.3.6-.4.8-.4h.6c.2 '
           '0 .4 0 .7.5l.9 2.2c.1.2.1.4 0 .6l-.4.6-.4.4c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.4 2.4 '
           '1.5.3.1.4.1.6-.1l.9-1c.2-.2.4-.2.6-.1l2.1 1c.3.1.4.2.5.3.1.2.1.8-.1 1.5z')


def buat_artikel():
    for i, p in enumerate(POS):
        sebelum = POS[i + 1] if i + 1 < len(POS) else None   # lebih lama
        sesudah = POS[i - 1] if i > 0 else None              # lebih baru

        terkait = [q for q in POS if q["slug"] != p["slug"] and p["kat"] in q["kategori"]][:3]
        for q in POS:
            if len(terkait) >= 3:
                break
            if q["slug"] != p["slug"] and q not in terkait:
                terkait.append(q)

        label = "".join('<a href="/kategori/%s/">%s</a>' % (KAT_SLUG[k], aman(k))
                        for k in p["kategori"] if k in KAT_SLUG)
        alamat = "%s/%s/" % (DOMAIN, p["slug"])

        nav = '<nav class="artikel-nav">'
        nav += (('<a href="/%s/"><small>Artikel sebelumnya</small>%s</a>'
                 % (sebelum["slug"], aman(sebelum["judul"]))) if sebelum
                else '<span class="kosong"></span>')
        nav += (('<a class="kanan" href="/%s/"><small>Artikel berikutnya</small>%s</a>'
                 % (sesudah["slug"], aman(sesudah["judul"]))) if sesudah
                else '<span class="kosong"></span>')
        nav += '</nav>'

        skema = json.dumps({
            "@context": "https://schema.org", "@type": "Article",
            "headline": p["judul"], "datePublished": p["tanggal"],
            "author": {"@type": "Person", "name": p["penulis"]},
            "publisher": {"@type": "Organization", "name": NAMA},
            "mainEntityOfPage": alamat,
            "image": (DOMAIN + "/gambar/" + p["gambar"]) if p["gambar"] else DOMAIN + "/gambar/logo.png",
            "articleSection": p["kat"], "inLanguage": "id",
        }, ensure_ascii=False)

        bagi = (
            '<span class="bagi">'
            '<a target="_blank" rel="noopener" href="https://wa.me/?text=%s" aria-label="Bagikan ke WhatsApp">'
            '<svg viewBox="0 0 24 24"><path d="%s"/></svg></a>'
            '<a target="_blank" rel="noopener" href="https://www.facebook.com/sharer/sharer.php?u=%s" aria-label="Bagikan ke Facebook">'
            '<svg viewBox="0 0 24 24"><path d="%s"/></svg></a>'
            '<a target="_blank" rel="noopener" href="https://twitter.com/intent/tweet?text=%s&amp;url=%s" aria-label="Bagikan ke X">'
            '<svg viewBox="0 0 24 24"><path d="%s"/></svg></a>'
            '</span>' % (
                aman(p["judul"] + " - " + alamat), IKON_WA,
                aman(alamat), SOSIAL["Facebook"],
                aman(p["judul"]), aman(alamat), SOSIAL["X"]))

        isi = (
            '<article>'
            '<div class="sampul">%s<div class="sampul-tirai"></div>'
            '<div class="sampul-teks"><div class="wadah"><span class="chip merah">%s</span></div></div></div>'
            '<div class="wadah">'
            '<nav class="remah"><a href="/">Beranda</a> &rsaquo; '
            '<a href="/kategori/%s/">%s</a> &rsaquo; <span>%s</span></nav>'
            '<section class="susun"><div>'
            '<h1 class="artikel-judul">%s</h1>'
            '<div class="artikel-meta">'
            '<span class="tanggal">%s%s</span><span class="pisah"></span>'
            '<span>%d kata</span><span class="pisah"></span>'
            '<span>%d menit baca</span><span class="pisah"></span>'
            '<span>%s</span>%s</div>'
            '<div class="tulisan">%s</div>'
            '<div class="label-kategori">%s</div>%s'
            '<div class="terkait">%s<div class="kisi" style="grid-template-columns:repeat(3,1fr)">%s</div></div>'
            '</div>%s</section></div>'
            '<script type="application/ld+json">%s</script></article>'
            % (blok_gambar(p), aman(p["kat"]),
               KAT_SLUG.get(p["kat"], "lain"), aman(p["kat"]), aman(p["judul"]),
               aman(p["judul"]), IKON_JAM, tanggal_panjang(p["tanggal"]),
               p["kata"], max(1, round(p["kata"] / 200)), aman(p["penulis"]), bagi,
               p["isi"] or '<p><em>Isi artikel ini tidak tersimpan lengkap di arsip.</em></p>',
               label, nav, judul_bagian("Artikel Terkait"),
               "".join(kartu(q) for q in terkait), bilah_sisi(), skema))

        tulis("%s/index.html" % p["slug"], tata_letak(
            isi, "%s - %s" % (p["judul"], NAMA), p["ringkas"], alamat, "",
            (DOMAIN + "/gambar/" + p["gambar"]) if p["gambar"] else "", "article"))


def buat_halaman_statis():
    judul_peta = {"tentang-kami": ("Tentang Kami", "tentang"),
                  "kontak": ("Kontak", "kontak"),
                  "kebijakan-data-pribadi": ("Kebijakan Data Pribadi", ""),
                  "ketentuan-penggunaan": ("Ketentuan Penggunaan", "")}
    for h in halaman_statis:
        judul, aktif = judul_peta.get(h["slug"], (h["judul"], ""))
        isi_bersih = bersihkan(h["isi_html"], h["slug"], "", "")
        isi = ('<div class="wadah"><section class="bagian">'
               '<h1 class="artikel-judul">%s</h1><div class="tulisan">%s</div></section></div>'
               % (aman(judul), isi_bersih))
        ringkas = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', isi_bersih))[:170].strip()
        tulis("%s/index.html" % h["slug"], tata_letak(
            isi, "%s - %s" % (judul, NAMA), ringkas,
            "%s/%s/" % (DOMAIN, h["slug"]), aktif))


def buat_cari():
    isi = ('<div class="wadah"><section class="bagian">%s'
           '<form action="/cari/" style="padding:0 0 8px">'
           '<input type="search" name="q" id="cari-kata" placeholder="Ketik kata kunci, lalu Enter…" '
           'autocomplete="off" style="width:100%%;max-width:560px;padding:12px 16px;'
           'border:1px solid var(--garis);border-radius:var(--radius);background:var(--bg);'
           'color:var(--body);font:inherit"></form>'
           '<p class="cari-status" id="cari-status">Memuat…</p>'
           '<div id="cari-hasil"></div></section></div>' % judul_bagian("Cari Artikel"))
    tulis("cari/index.html", tata_letak(
        isi, "Cari Artikel - %s" % NAMA,
        "Cari di seluruh %d artikel %s, sampai ke isi tulisannya." % (len(POS), NAMA),
        DOMAIN + "/cari/"))

    indeks = [{"s": p["slug"], "j": p["judul"], "k": p["kat"], "t": p["tanggal"],
               "r": p["ringkas"], "g": p["gambar"],
               "i": re.sub(r'\s+', ' ', p["teks"]).lower()} for p in POS]
    tulis("aset/cari.json", json.dumps(indeks, ensure_ascii=False, separators=(",", ":")))


def buat_404():
    isi = ('<div class="wadah"><div class="kosong"><h3>Halaman tidak ditemukan</h3>'
           '<p>Alamat yang Anda buka tidak ada di arsip ini.</p>'
           '<p style="margin-top:18px"><a class="tombol" href="/">Kembali ke beranda</a> '
           '<a class="tombol" href="/blog/">Lihat semua artikel</a></p></div></div>')
    tulis("404.html", tata_letak(isi, "Halaman tidak ditemukan - %s" % NAMA,
                                "Halaman tidak ditemukan.", DOMAIN + "/404.html"))


def buat_sitemap_dll():
    alamat = [(DOMAIN + "/", "1.0"), (DOMAIN + "/blog/", "0.8"),
              (DOMAIN + "/kategori/", "0.6"), (DOMAIN + "/arsip/", "0.5")]
    alamat += [("%s/kategori/%s/" % (DOMAIN, s), "0.5") for s in KAT_SLUG.values()]
    alamat += [("%s/%s/" % (DOMAIN, h["slug"]), "0.4") for h in halaman_statis]
    baris = "".join('<url><loc>%s</loc><priority>%s</priority></url>' % a for a in alamat)
    baris += "".join(
        '<url><loc>%s/%s/</loc><lastmod>%s</lastmod><priority>0.7</priority></url>'
        % (DOMAIN, p["slug"], (p["tanggal"] or "")[:10]) for p in POS)
    tulis("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % baris)

    tulis("robots.txt",
          "User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: %s/sitemap.xml\n" % DOMAIN)

    item = "".join(
        '<item><title>%s</title><link>%s/%s/</link><guid>%s/%s/</guid>'
        '<pubDate>%s</pubDate><category>%s</category><description>%s</description></item>'
        % (aman(p["judul"]), DOMAIN, p["slug"], DOMAIN, p["slug"],
           rfc822(p["tanggal"]), aman(p["kat"]), aman(p["ringkas"]))
        for p in POS[:30])
    tulis("feed.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">'
          '<channel><title>%s</title><link>%s/</link><description>%s</description>'
          '<language>id</language>%s</channel></rss>' % (NAMA, DOMAIN, aman(DESKRIPSI), item))

    buat_pengalihan()

    # Cloudflare Pages: aset boleh di-cache lama, HTML jangan
    tulis("_headers",
          "/aset/*\n  Cache-Control: public, max-age=31536000, immutable\n"
          "/gambar/*\n  Cache-Control: public, max-age=31536000, immutable\n"
          "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n")


def buat_admin():
    """Halaman /admin/ (Decap CMS) + config.yml yang ikut daftar kategori situs."""
    pengaturan = {}
    berkas = os.path.join(AKAR, "situs.json")
    if os.path.exists(berkas):
        pengaturan = json.load(open(berkas, encoding="utf-8"))

    repo = pengaturan.get("repo_github", "GANTI-USERNAME/konsultasifiqih")
    cabang = pengaturan.get("cabang", "main")
    oauth = (pengaturan.get("oauth_base_url", "https://GANTI-NAMA.workers.dev") or "").rstrip("/")

    pilihan_kategori = "\n".join(
        '          - "%s"' % k.replace('"', "'")
        for k in sorted(KATEGORI, key=lambda x: -len(KATEGORI[x])))

    config = """# Dihasilkan otomatis oleh bangun_situs.py — jangan disunting langsung.
# Ubah repo/OAuth lewat situs.json di akar repositori.
backend:
  name: github
  repo: %s
  branch: %s
  base_url: %s
  auth_endpoint: auth
  commit_messages:
    create: 'Artikel baru: {{slug}}'
    update: 'Perbarui artikel: {{slug}}'
    delete: 'Hapus artikel: {{slug}}'
    uploadMedia: 'Tambah gambar: {{path}}'
    deleteMedia: 'Hapus gambar: {{path}}'

locale: 'id'
media_folder: tulisan/gambar
public_folder: /gambar
publish_mode: simple

collections:
  - name: artikel
    label: Artikel
    label_singular: Artikel
    description: >-
      Artikel baru disimpan sebagai berkas Markdown di folder tulisan/.
      Selama "Simpan sebagai draf" masih aktif, artikel tidak tampil di situs.
    folder: tulisan
    create: true
    slug: '{{slug}}'
    extension: md
    format: yaml-frontmatter
    summary: '{{judul}}  ({{tanggal}})'
    sortable_fields: ['tanggal', 'judul']
    fields:
      - {name: judul, label: Judul, widget: string}
      - name: tanggal
        label: Tanggal terbit
        widget: datetime
        date_format: 'YYYY-MM-DD'
        time_format: false
        format: 'YYYY-MM-DD'
      - {name: penulis, label: Penulis, widget: string, default: 'Ustadz Dr. Awwaluz Zikri, Lc. MA'}
      - name: kategori
        label: Kategori
        widget: select
        multiple: true
        min: 1
        default: ['Fikih Ibadah']
        options:
%s
      - {name: gambar, label: Gambar sampul, widget: image, required: false, allow_multiple: false}
      - name: draf
        label: Simpan sebagai draf (belum tampil di situs)
        widget: boolean
        default: true
      - name: body
        label: Isi artikel
        widget: markdown
        hint: >-
          Paragraf berbahasa Arab cukup ditulis sebagai paragraf tersendiri —
          otomatis dibuat rata kanan dan diperbesar.
""" % (repo, cabang, oauth, pilihan_kategori)

    tulis("admin/config.yml", config)
    shutil.copy2(os.path.join(SUMBER, "admin.html"), os.path.join(KELUAR, "admin", "index.html"))
    return "GANTI-" in repo or "GANTI-" in oauth


def buat_pengalihan():
    """Alihkan pola URL WordPress lama supaya tautan & indeks Google lama tidak mati.

    Semua ditulis eksplisit — pola bebas seperti /:induk/:anak/ berisiko
    menutupi halaman asli seperti /kategori/hikmah/ atau /blog/2/.
    """
    baris = [
        "# URL lama WordPress -> susunan baru",
        "/about/  /tentang-kami/  301",
        "/kirim-pertanyaan/  /kontak/  301",
        "/sitemap/  /arsip/  301",
        "/feed/  /feed.xml  301",
        "/home/  /  301",
        "/category/*  /kategori/:splat  301",
        "/tag/*  /blog/  301",
        "/author/*  /tentang-kami/  301",
        "/page/*  /blog/  301",
    ]
    for t in range(2014, 2028):
        baris.append("/%d/*  /arsip/  301" % t)

    # halaman lampiran gambar: /nama-artikel/nama-gambar/ -> artikel induknya
    berkas_lampiran = os.path.join(ARSIP, "lampiran.json")
    lampiran = []
    if os.path.exists(berkas_lampiran):
        lampiran = [tuple(x) for x in json.load(open(berkas_lampiran, encoding="utf-8"))]
    if lampiran:
        baris.append("")
        baris.append("# halaman lampiran gambar -> artikel induknya")
        for induk, anak in sorted(lampiran):
            baris.append("/%s/%s/  /%s/  301" % (induk, anak, induk))

    tulis("_redirects", "\n".join(baris) + "\n")
    return len(baris)


def salin_aset():
    os.makedirs(os.path.join(KELUAR, "aset"), exist_ok=True)
    for n in ("gaya.css", "situs.js"):
        shutil.copy2(os.path.join(SUMBER, n), os.path.join(KELUAR, "aset", n))

    asal = os.path.join(ARSIP, "gambar")
    tujuan = os.path.join(KELUAR, "gambar")
    os.makedirs(tujuan, exist_ok=True)
    disalin, hilang = 0, []
    for p in POS:
        if not p["gambar"]:
            continue
        # artikel baru: cari dulu di tulisan/gambar/, baru ke arsip
        for folder in ((GAMBAR_BARU, asal) if p.get("baru") else (asal, GAMBAR_BARU)):
            sumber_gbr = os.path.join(folder, p["gambar"])
            if os.path.exists(sumber_gbr):
                shutil.copy2(sumber_gbr, os.path.join(tujuan, p["gambar"]))
                disalin += 1
                break
        else:
            hilang.append("%s -> %s" % (p["slug"], p["gambar"]))
    if hilang:
        print("!! gambar tidak ketemu (kartu memakai gradasi):")
        for h in hilang[:10]:
            print("   ", h)
    logo = os.path.join(asal, gambar_lokal.get("logo", "logo.png"))
    if os.path.exists(logo):
        shutil.copy2(logo, os.path.join(tujuan, "logo.png"))
    return disalin


# ---------------------------------------------------------------- jalankan

if __name__ == "__main__":
    if os.path.exists(KELUAR):
        shutil.rmtree(KELUAR)
    os.makedirs(KELUAR)

    buat_beranda()
    hal_blog = buat_daftar(POS, "/blog/", "Semua Artikel",
                           "Seluruh %d artikel arsip %s." % (len(POS), NAMA), "blog",
                           "%d artikel dari arsip konsultasifiqih.com" % len(POS))
    buat_kategori()
    buat_arsip()
    buat_artikel()
    buat_halaman_statis()
    buat_cari()
    buat_404()
    admin_belum_siap = buat_admin()
    buat_sitemap_dll()
    n_gambar = salin_aset()

    berkas = sum(len(f) for _, _, f in os.walk(KELUAR))
    besar = sum(os.path.getsize(os.path.join(d, f))
                for d, _, fs in os.walk(KELUAR) for f in fs)
    print("Artikel      : %d  (arsip %d + tulisan baru %d)"
          % (len(POS), len(POS) - len(TULISAN_BARU), len(TULISAN_BARU)))
    for p in TULISAN_BARU:
        print("   + /%s/  — %s" % (p["slug"], p["judul"]))
    if DRAF:
        print("   (draf, belum diterbitkan: %s)" % ", ".join(DRAF))
    if BENTROK:
        print("!! slug bentrok dgn arsip, versi baru yang dipakai: %s" % ", ".join(BENTROK))
    print("Kategori     : %d" % len(KATEGORI))
    print("Halaman blog : %d" % hal_blog)
    print("Gambar       : %d" % n_gambar)
    print("Total berkas : %d  (%.1f MB)" % (berkas, besar / 1048576))
    print("Keluaran     : %s" % KELUAR)
    if admin_belum_siap:
        print()
        print("Catatan: /admin/ (editor peramban) belum aktif — situs.json masih")
        print("         berisi nilai contoh. Lihat README bagian 'Menulis lewat peramban'.")
