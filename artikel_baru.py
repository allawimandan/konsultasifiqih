# -*- coding: utf-8 -*-
"""Buat berkas draf artikel baru di folder tulisan/.

Pemakaian:
    py artikel_baru.py "Hukum Bermain Catur"
"""
import os, re, sys, unicodedata
from datetime import datetime

AKAR = os.path.dirname(os.path.abspath(__file__))
TULISAN = os.path.join(AKAR, "tulisan")


def slugkan(teks):
    t = unicodedata.normalize("NFKD", str(teks)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower() or "artikel-baru"


TEMPLAT = """---
judul: {judul}
tanggal: {tanggal}
penulis: Ustadz Dr. Awwaluz Zikri, Lc. MA
kategori: Fikih Ibadah
gambar:
draf: ya
---

Assalamualaikum Wr Wb.

Ustadz, (tulis pertanyaannya di sini).

**Jawaban:**

Waalaikum Salam Wr Wb.

(Tulis jawabannya di sini. Ini Markdown — **tebal**, *miring*,
[tautan](https://contoh.com), dan daftar pakai tanda minus.)

> Kutipan atau catatan penting ditulis begini.

Ayat atau hadis berbahasa Arab cukup ditulis satu paragraf sendiri,
nanti otomatis dibuat rata kanan:

لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ

Artinya: "(terjemahan)".

Wallahu a'lam bish-shawab.
"""


def main():
    if len(sys.argv) < 2:
        print('Pemakaian:  py artikel_baru.py "Judul Artikel"')
        return 1

    judul = " ".join(sys.argv[1:]).strip()
    slug = slugkan(judul)
    os.makedirs(os.path.join(TULISAN, "gambar"), exist_ok=True)
    jalur = os.path.join(TULISAN, slug + ".md")

    if os.path.exists(jalur):
        print("Sudah ada, tidak ditimpa:", jalur)
        return 1

    with open(jalur, "w", encoding="utf-8") as f:
        f.write(TEMPLAT.format(judul=judul, tanggal=datetime.now().strftime("%Y-%m-%d")))

    print("Draf dibuat :", jalur)
    print("Alamat nanti: /%s/" % slug)
    print()
    print("Langkah berikutnya:")
    print("  1. Sunting berkas itu (Notepad juga bisa).")
    print("  2. Kalau mau ada gambar: taruh di tulisan/gambar/, lalu tulis")
    print("     nama berkasnya di baris 'gambar:' pada kepala artikel.")
    print("  3. Ganti 'draf: ya' jadi 'draf: tidak' bila siap terbit.")
    print("  4. Jalankan:  py bangun_situs.py  lalu  py paketkan.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
