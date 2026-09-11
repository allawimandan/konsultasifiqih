# -*- coding: utf-8 -*-
"""Bungkus folder keluaran/ jadi ZIP untuk diseret ke Cloudflare Pages."""
import os, zipfile

AKAR = os.path.dirname(os.path.abspath(__file__))
KELUAR = os.path.join(AKAR, "keluaran")
ZIP = os.path.join(AKAR, "konsultasifiqih-situs.zip")

if not os.path.isdir(KELUAR):
    raise SystemExit("Folder keluaran/ belum ada. Jalankan dulu:  py bangun_situs.py")

if os.path.exists(ZIP):
    os.remove(ZIP)

n = 0
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for d, _, fs in os.walk(KELUAR):
        for f in sorted(fs):
            penuh = os.path.join(d, f)
            z.write(penuh, os.path.relpath(penuh, KELUAR))
            n += 1

print("Berkas : %d" % n)
print("Ukuran : %.1f MB" % (os.path.getsize(ZIP) / 1048576))
print("Paket  : %s" % ZIP)
print()
print("Unggah: dash.cloudflare.com -> Workers & Pages -> proyek konsultasifiqih")
print("        -> Create deployment -> seret berkas ZIP di atas.")
