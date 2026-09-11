# konsultasifiqih.com — situs statis

Versi statis dari 239 artikel arsip `konsultasifiqih.com`, siap dipasang di
domainnya sendiri lewat **Cloudflare Pages**. Tidak butuh hosting berbayar,
tidak butuh PHP/WordPress, tidak butuh Google Apps Script.

| | |
|---|---|
| Artikel | 239 halaman HTML tersendiri |
| Kategori | 27 |
| Gambar | 114 (ikut di dalam situs, bukan menumpang Drive) |
| Total | 421 berkas, 14,1 MB (ZIP 8,3 MB) |
| Hasil build | `keluaran/` |
| Paket unggah | `konsultasifiqih-situs.zip` |

## Kenapa statis, bukan Apps Script

Web app Apps Script **tidak bisa dipasang di domain sendiri** — URL-nya permanen
di `script.google.com`. Google tidak menyediakan domain kustom untuk web app.
Jadi isinya dipindahkan ke situs statis yang bisa diarahkan ke domain mana pun.

Untungnya versi statis ini lebih baik dari sisi mana pun: **URL artikel persis
seperti situs aslinya** (`/nama-artikel/`), jadi tautan lama yang beredar dan
sisa indeks Google tetap hidup. Ditambah `sitemap.xml`, RSS, JSON-LD, Open
Graph, dan halaman yang bisa dibaca tanpa JavaScript — semuanya mustahil di
dalam iframe Apps Script.

## Keadaan domain saat ini

| | |
|---|---|
| Registrar | CV. Rumahweb Indonesia — berlaku sampai **26 Juli 2027** |
| Nameserver | `dns1.namecheaphosting.com`, `dns2.namecheaphosting.com` |
| A record | `198.54.116.42` (Namecheap, **akun suspended**) |
| MX | `mx1/2/3-hosting.jellyfish.systems` (email Namecheap) |

Yang dikelola Rumahweb hanya **pendaftaran domain**. DNS dan hosting web ada di
Namecheap, dan akun itulah yang mati. Karena domainnya masih milik Anda,
tinggal dialihkan ke Cloudflare.

## Langkah pemasangan

Langkah-langkah ini butuh login akun Anda, jadi harus Anda yang menjalankan.

**1. Buat akun Cloudflare** (gratis) di `dash.cloudflare.com`.

**2. Tambahkan domain.** Menu *Add a site* → ketik `konsultasifiqih.com` →
pilih paket **Free**. Cloudflare akan memindai DNS lama dan memberi **dua
nameserver**, bentuknya seperti `andy.ns.cloudflare.com`.

**3. Ganti nameserver di Rumahweb.** Masuk clientarea Rumahweb → *Domains* →
*My Domains* → pilih konsultasifiqih.com → *Nameservers* → pilih **Use custom
nameservers**, hapus `dns1/dns2.namecheaphosting.com`, isi dua nameserver
Cloudflare tadi → simpan. Aktifnya biasanya 15 menit–24 jam.

**4. Hapus A record lama.** Di Cloudflare → *DNS*, cari record `A` yang menunjuk
`198.54.116.42` lalu **hapus**. Kalau dibiarkan, pengunjung masih melihat
halaman "Account Suspended".

**5. Unggah situsnya.** Cloudflare → *Workers & Pages* → *Create* → tab
**Pages** → *Upload assets* → beri nama proyek (misal `konsultasifiqih`) →
seret berkas **`konsultasifiqih-situs.zip`** (atau isi folder `keluaran/`) →
*Deploy*. Setelah jadi, situs langsung bisa dicek di alamat sementara
`konsultasifiqih.pages.dev`.

**6. Pasang domainnya.** Di proyek Pages → *Custom domains* → *Set up a custom
domain* → isi `konsultasifiqih.com`. Ulangi untuk `www.konsultasifiqih.com`.
Cloudflare membuat DNS record dan sertifikat HTTPS sendiri.

Selesai. Situs hidup di `https://konsultasifiqih.com` dengan HTTPS gratis.

## Yang perlu diperhatikan

- **Email.** MX sekarang mengarah ke email Namecheap yang kemungkinan ikut mati.
  Saat memindai DNS, Cloudflare biasanya menyalin MX lama — kalau Anda **masih**
  memakai email `@konsultasifiqih.com`, pastikan record MX-nya ikut terbawa
  sebelum mengganti nameserver. Kalau sudah tidak dipakai, abaikan saja.
- **Jangan hapus domainnya di Rumahweb.** Yang diganti hanya nameserver;
  pendaftaran domain tetap di Rumahweb dan tetap perlu diperpanjang 2027.
- Ikon media sosial di kepala/kaki masih `href="#"` karena akunnya tidak ada di
  arsip. Kirim tautannya kalau mau diisi.

> **Panduan pemasangan langkah per langkah ada di [PANDUAN.md](PANDUAN.md)** —
> lengkap dengan perintah siap salin, penanda "berhasil kalau…" di tiap
> tahap, dan daftar penanganan bila macet. Bagian di bawah ini ringkasannya.

## Menulis lewat peramban (dari HP juga bisa)

Setelah disiapkan sekali, Anda menulis artikel di
`konsultasifiqih.com/admin/` — editor sungguhan dengan pratinjau, unggah
gambar, dan pilihan kategori. Simpan → Cloudflare membangun ulang situs
sendiri. Komputer ini tidak perlu dibuka lagi.

Alurnya: **editor → simpan ke GitHub → Cloudflare Pages bangun ulang → situs
terbarui.** Karena itu perlu repositori GitHub dan satu Worker kecil untuk
proses masuk; GitHub tidak mengizinkan login dilakukan murni dari peramban.

### 1. Naikkan folder ini ke GitHub

Buat repositori baru (boleh privat) bernama `konsultasifiqih`, lalu:

```bash
git init
git add .
git commit -m "Situs konsultasifiqih.com"
git branch -M main
git remote add origin https://github.com/NAMA-ANDA/konsultasifiqih.git
git push -u origin main
```

`keluaran/` dan berkas ZIP sudah diabaikan lewat `.gitignore` — yang naik hanya
bahan mentahnya (±10 MB).

### 2. Sambungkan ke Cloudflare Pages

Cloudflare → *Workers & Pages* → *Create* → **Pages** → *Connect to Git* →
pilih repositori tadi, lalu isi:

| Kolom | Isi |
|---|---|
| Framework preset | None |
| Build command | `pip install -r requirements.txt && python bangun_situs.py` |
| Build output directory | `keluaran` |

Sejak ini, setiap perubahan di GitHub otomatis membangun ulang situs.

> Kalau sebelumnya Anda sudah membuat proyek Pages lewat unggah ZIP, buat
> proyek **baru** yang tersambung Git, lalu pindahkan custom domain-nya.

### 3. Buat OAuth App di GitHub

GitHub → *Settings* → *Developer settings* → *OAuth Apps* → *New OAuth App*:

| Kolom | Isi |
|---|---|
| Application name | `konsultasifiqih CMS` |
| Homepage URL | `https://konsultasifiqih.com` |
| Authorization callback URL | `https://konsultasifiqih-oauth.NAMA-ANDA.workers.dev/callback` |

Simpan **Client ID**, lalu *Generate a new client secret* dan simpan
**Client Secret**-nya.

### 4. Pasang Worker untuk proses masuk

Cloudflare → *Workers & Pages* → *Create* → **Worker** → beri nama
`konsultasifiqih-oauth` → *Deploy* → *Edit code* → hapus isinya, tempel
seluruh isi [`oauth-worker/worker.js`](oauth-worker/worker.js) → *Deploy*.

Lalu di Worker itu: *Settings* → *Variables and Secrets* → tambah dua secret:

| Nama | Isi |
|---|---|
| `GITHUB_CLIENT_ID` | Client ID dari langkah 3 |
| `GITHUB_CLIENT_SECRET` | Client Secret dari langkah 3 |

Catat alamat Worker-nya (`https://konsultasifiqih-oauth.NAMA-ANDA.workers.dev`)
dan pastikan sama persis dengan callback URL di langkah 3.

### 5. Isi situs.json

Sunting `situs.json` di akar repositori:

```json
{
  "repo_github": "NAMA-ANDA/konsultasifiqih",
  "cabang": "main",
  "oauth_base_url": "https://konsultasifiqih-oauth.NAMA-ANDA.workers.dev"
}
```

Simpan dan push. Cloudflare membangun ulang, dan
`konsultasifiqih.com/admin/` siap dipakai.

### Kalau langkah 3–5 terasa merepotkan

Lewati saja. Dengan langkah 1–2 selesai, artikel tetap bisa ditambah dari
peramban mana pun: buka repositori di github.com → folder `tulisan/` →
*Add file* → *Create new file* → beri nama `judul-artikel.md` → tulis isinya
dengan format di bawah → *Commit*. Cloudflare langsung membangun ulang.
Tampilannya memang kotak teks biasa, tapi jalan dari HP sekalipun.

## Menulis artikel baru (dari komputer ini)

Artikel baru ditulis sebagai berkas **Markdown** di folder `tulisan/`. Tiga
perintah, tanpa WordPress dan tanpa basis data.

**1. Buat drafnya**

```bash
py artikel_baru.py "Hukum Bermain Catur"
```

Terbentuk `tulisan/hukum-bermain-catur.md` berisi kerangka siap isi. Alamat
artikelnya nanti `konsultasifiqih.com/hukum-bermain-catur/` — diambil dari nama
berkasnya.

**2. Tulis isinya.** Buka berkas itu dengan Notepad atau editor apa pun:

```markdown
---
judul: Hukum Bermain Catur
tanggal: 2026-09-12
penulis: Ustadz Dr. Awwaluz Zikri, Lc. MA
kategori: Fikih Muamalat, Hikmah
gambar: catur.jpg
draf: tidak
---

Isi artikel di sini. **Tebal**, *miring*, [tautan](https://contoh.com),
daftar pakai tanda minus, kutipan pakai tanda lebih besar.
```

| Kepala | Keterangan |
|---|---|
| `judul` | wajib |
| `tanggal` | `YYYY-MM-DD`; menentukan urutan di beranda |
| `penulis` | bebas |
| `kategori` | pisahkan dengan koma; kategori baru dibuat otomatis |
| `gambar` | opsional, taruh berkasnya di `tulisan/gambar/` |
| `draf` | `ya` = belum terbit, `tidak` = ikut terbit |

Paragraf berbahasa Arab tidak perlu ditandai apa pun — cukup ditulis sebagai
paragraf tersendiri, otomatis dibuat rata kanan dan diperbesar.

**3. Bangun dan unggah**

```bash
py bangun_situs.py
py paketkan.py
```

Lalu seret `konsultasifiqih-situs.zip` ke Cloudflare Pages → proyek
konsultasifiqih → *Create deployment*.

Artikel baru otomatis muncul di beranda, halaman Blog, halaman kategorinya,
arsip per tahun, `sitemap.xml`, RSS, dan indeks pencarian. Tidak ada yang perlu
didaftarkan manual.

> **Perhatian:** baris `penulis` secara bawaan berisi nama Ustadz Dr. Awwaluz
> Zikri. Isi hanya dengan tulisan yang benar-benar beliau tulis atau setujui —
> jangan menerbitkan jawaban fikih atas nama beliau tanpa izin.

## Memperbarui isi lama

Artikel arsip ada di `../konsultasifiqih-arsip/artikel.json`. Untuk mengubah
tampilan, sunting `sumber/gaya.css`. Setelah itu jalankan ulang
`py bangun_situs.py` dan `py paketkan.py`.

## Isi folder

| | |
|---|---|
| `artikel_baru.py` | buat draf artikel baru |
| `bangun_situs.py` | generator situs |
| `paketkan.py` | bungkus `keluaran/` jadi ZIP |
| `situs.json` | nama repo GitHub + alamat OAuth (untuk editor `/admin/`) |
| `tulisan/` | artikel baru (Markdown) + `tulisan/gambar/` |
| `data/` | arsip 239 artikel + 116 gambar (sumber bangunan) |
| `sumber/gaya.css` | seluruh tampilan |
| `sumber/situs.js` | mode gelap, pencarian, gambar cadangan |
| `sumber/admin.html` | halaman editor Decap CMS |
| `oauth-worker/` | Worker Cloudflare untuk proses masuk GitHub |
| `requirements.txt` | dependensi build di Cloudflare (`markdown`) |
| `keluaran/` | situs jadi — hasil build, tidak masuk Git |
| `keluaran/_redirects` | 214 pengalihan URL lama WordPress |
| `keluaran/_headers` | aturan cache Cloudflare |

## Pengalihan URL lama

`_redirects` menjaga tautan lama tetap hidup: `/category/*` → `/kategori/*`,
`/tag/*` dan `/page/*` → `/blog/`, `/author/*` → `/tentang-kami/`,
`/2014/*`…`/2027/*` → `/arsip/`, `/about/` → `/tentang-kami/`, `/feed/` →
`/feed.xml`, plus **189 halaman lampiran gambar** (`/artikel/nama-gambar/`)
dialihkan ke artikel induknya.

Semuanya ditulis eksplisit, bukan pola bebas seperti `/:induk/:anak/`, supaya
tidak menimpa halaman asli seperti `/kategori/hikmah/` atau `/blog/2/`.
