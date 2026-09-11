# Panduan pemasangan konsultasifiqih.com — langkah per langkah

Panduan ini ditulis untuk komputer Anda apa adanya. Yang sudah dicek:

| | |
|---|---|
| Git | **terpasang** (versi 2.49.0) |
| Git Credential Manager | **ada** — `git push` cukup login lewat peramban, tidak perlu token |
| Identitas Git | **sudah diatur** (`allawimandan` / ajengansubang@gmail.com) |
| GitHub CLI (`gh`) | tidak ada — tidak dipakai di panduan ini |
| Python di Cloudflare | tersedia 3.13.3 + pip, sama dengan komputer ini |

Perkiraan waktu: **40–60 menit**, sudah termasuk menunggu propagasi.

Nama tombol di GitHub dan Cloudflare kadang bergeser sedikit. Kalau tulisan di
layar tidak persis sama, cari yang maknanya sama — alurnya tetap.

> **Tidak ada lagi yang perlu Anda ganti.** Username GitHub
> (`allawimandan`) dan subdomain Cloudflare (`ajengansubang.workers.dev`)
> sudah terisi di seluruh perintah dan alamat di bawah.

---

## Bagian 0 — Persiapan ✅ SELESAI

### 0.1 Akun GitHub

Sudah ada: **`allawimandan`**. Username ini sudah diisikan ke seluruh
perintah di bawah, jadi blok perintahnya bisa disalin apa adanya.

### 0.2 Kenalkan identitas ke Git

Sudah dikerjakan. Nilainya sekarang:

```bash
git config --global user.name "allawimandan"
git config --global user.email "ajengansubang@gmail.com"
```

Nama itu yang muncul sebagai penulis tiap perubahan di GitHub. Kalau ingin
nama asli, jalankan ulang baris pertama dengan nama Anda.

---

## Bagian 1 — Naikkan situs ke GitHub ✅ SELESAI

### 1.1 Buat repositori kosong

1. Buka `github.com` → klik tanda **+** di kanan atas → **New repository**
2. **Repository name:** `konsultasifiqih`
3. Pilih **Private** (boleh juga Public — isinya memang untuk umum)
4. Sebaiknya **jangan** centang *Add a README file* — kalau terlanjur
   tercentang, riwayatnya perlu digabung dulu sebelum bisa dikirim
   (ini yang terjadi kemarin dan sudah dibereskan).
5. Klik **Create repository**

### 1.2 Kirim berkasnya

Di Command Prompt, masuk ke folder situs lalu jalankan berurutan:

```bash
cd C:\Users\maman.a\proyekchatbot\konsultasifiqih-situs
git init
git add .
git commit -m "Situs arsip konsultasifiqih.com"
git branch -M main
git remote add origin https://github.com/allawimandan/konsultasifiqih.git
git push -u origin main
```

Pada `git push` yang pertama, akan **muncul jendela peramban** meminta login
GitHub. Masuk dan izinkan. Setelah itu tidak ditanya lagi.

Yang naik ±10 MB. Folder `keluaran/` dan berkas ZIP sengaja tidak ikut — itu
hasil build, nanti dibuat ulang oleh Cloudflare.

**Berhasil kalau:** halaman repositori di GitHub sudah berisi `bangun_situs.py`,
folder `data/`, `sumber/`, `tulisan/`, dan `README.md`.

---

## Bagian 2 — Sambungkan ke Cloudflare Pages ← MULAI DI SINI

Bagian ini menggantikan cara unggah ZIP. Setelah ini, setiap perubahan di
GitHub otomatis membangun ulang situs.

### 2.1 Buat proyek Pages

1. Buka `dash.cloudflare.com`
2. Menu kiri → **Workers & Pages** → tombol biru **Create application**
3. Pada panel *Make something new*, pilih **Connect GitHub**
   (bukan *Upload your static files* — itu cara ZIP yang lama)
4. Izinkan Cloudflare mengakses akun GitHub Anda; boleh pilih
   *Only select repositories* → centang `konsultasifiqih` saja
5. Pilih repositori `konsultasifiqih`, lanjutkan ke pengaturan build

### 2.2 Isi pengaturan build

| Kolom | Isi |
|---|---|
| Project name | `konsultasifiqih` |
| Production branch | `main` |
| Framework preset | **None** |
| Build command | `pip install -r requirements.txt && python bangun_situs.py` |
| Build output directory | `keluaran` |

Klik **Save and Deploy**. Build pertama makan waktu 1–3 menit.

**Berhasil kalau:** statusnya *Success*, dan alamat
`konsultasifiqih.pages.dev` sudah menampilkan situsnya lengkap dengan artikel.

> Kalau build gagal dengan pesan soal Python, buka *Settings* → *Variables and
> Secrets* → tambah variabel `PYTHON_VERSION` berisi `3.13.3`, lalu *Retry
> deployment*.

### 2.3 Pindahkan domainnya

Kalau sebelumnya Anda sudah membuat proyek Pages dari unggahan ZIP, domainnya
masih menempel di proyek lama. Lepas dulu:

1. Buka proyek Pages yang **lama** → *Custom domains* → hapus
   `konsultasifiqih.com` dan `www.konsultasifiqih.com`
2. Buka proyek Pages yang **baru** → *Custom domains* → **Set up a custom
   domain** → isi `konsultasifiqih.com` → ulangi untuk `www.konsultasifiqih.com`

Cloudflare mengurus DNS dan sertifikat HTTPS sendiri.

**Berhasil kalau:** `https://konsultasifiqih.com` membuka situsnya, bukan
halaman "Account Suspended".

> Sampai di sini situs Anda **sudah hidup dan sudah bisa ditambah artikel**
> lewat GitHub (lihat Bagian 6B). Bagian 3–5 hanya untuk mendapat editor yang
> lebih enak. Boleh dikerjakan lain hari.

---

## Bagian 3 — Daftarkan OAuth App di GitHub (5 menit)

Langkah ini dan berikutnya dibutuhkan karena GitHub **tidak mengizinkan login
dilakukan murni dari peramban** — harus ada server kecil yang memegang rahasia.

Tentukan dulu nama Worker-nya. Pakai `konsultasifiqih-oauth`. Alamatnya nanti:

```
https://konsultasifiqih-oauth.ajengansubang.workers.dev
```

Subdomain `ajengansubang` sudah dipastikan dari dasbor Cloudflare Anda
(**Workers & Pages** → panel *Account details*). Alamat di atas dipakai di
dua tempat — Bagian 3.1 dan Bagian 5.1 — dan harus sama persis.

### 3.1 Buat OAuth App

1. GitHub → klik foto profil (kanan atas) → **Settings**
2. Gulir ke bawah, menu kiri paling bawah → **Developer settings**
3. **OAuth Apps** → **New OAuth App**
4. Isi:

| Kolom | Isi |
|---|---|
| Application name | `konsultasifiqih CMS` |
| Homepage URL | `https://konsultasifiqih.com` |
| Authorization callback URL | `https://konsultasifiqih-oauth.ajengansubang.workers.dev/callback` |

5. **Register application**

### 3.2 Ambil dua kuncinya

- **Client ID** langsung terlihat di halaman itu — salin
- Klik **Generate a new client secret** → salin **segera**, karena setelah
  halaman ditutup tidak bisa dilihat lagi

Simpan keduanya sementara di Notepad.

> Client Secret itu setara kata sandi. Jangan ditempel ke mana pun selain
> kolom rahasia di Cloudflare pada Bagian 4.

---

## Bagian 4 — Pasang Worker untuk login (10 menit)

### 4.1 Buat Worker

1. Cloudflare → **Workers & Pages** → **Create** → tab **Workers**
2. Beri nama persis: `konsultasifiqih-oauth`
3. **Deploy** (isinya masih contoh bawaan, tidak apa-apa)
4. Klik **Edit code**
5. Hapus seluruh isi editor, lalu tempel **seluruh isi berkas**
   `oauth-worker/worker.js` dari folder situs ini
6. Klik **Deploy**

**Berhasil kalau:** membuka
`https://konsultasifiqih-oauth.ajengansubang.workers.dev` di peramban
menampilkan tulisan *"Server OAuth Decap CMS untuk konsultasifiqih.com."*

Kalau yang muncul *"Worker belum diberi GITHUB_CLIENT_ID…"*, berarti Worker-nya
sudah benar — tinggal isi rahasianya di langkah berikut.

### 4.2 Isi dua rahasia

1. Di Worker itu → **Settings** → **Variables and Secrets**
2. **Add** → pilih tipe **Secret** (bukan Text/plaintext):

| Nama variabel | Isi |
|---|---|
| `GITHUB_CLIENT_ID` | Client ID dari langkah 3.2 |
| `GITHUB_CLIENT_SECRET` | Client Secret dari langkah 3.2 |

3. **Deploy** / **Save** supaya berlaku

**Berhasil kalau:** membuka alamat Worker sekarang menampilkan
*"Server OAuth Decap CMS…"*, bukan lagi pesan "belum diberi".

---

## Bagian 5 — Hubungkan editornya (5 menit)

### 5.1 Sunting situs.json

Buka `situs.json` di folder situs ini (Notepad cukup), isi tiga nilainya:

```json
{
  "repo_github": "allawimandan/konsultasifiqih",
  "cabang": "main",
  "oauth_base_url": "https://konsultasifiqih-oauth.ajengansubang.workers.dev"
}
```

Perhatikan: `oauth_base_url` **tanpa** `/callback` dan **tanpa** garis miring di
ujung. Baris `_catatan` boleh dihapus atau dibiarkan.

### 5.2 Kirim perubahannya

```bash
cd C:\Users\maman.a\proyekchatbot\konsultasifiqih-situs
git add situs.json
git commit -m "Isi pengaturan editor"
git push
```

Cloudflare otomatis membangun ulang (1–3 menit).

**Berhasil kalau:** `https://konsultasifiqih.com/admin/` menampilkan tombol
**Login with GitHub** — bukan pesan "Editor belum disiapkan".

---

## Bagian 6 — Menulis artikel

### 6A. Lewat editor (setelah Bagian 3–5 selesai)

1. Buka `https://konsultasifiqih.com/admin/`
2. **Login with GitHub** → jendela izin muncul → **Authorize**
3. **New Artikel**
4. Isi Judul, Tanggal, Kategori, dan Isi artikel
5. Gambar sampul: klik kolom Gambar → **Upload** → pilih berkas
6. Selama **Simpan sebagai draf** masih menyala, artikel **tidak** tampil di
   situs. Matikan kalau sudah siap terbit.
7. **Publish** → **Publish now**

Cloudflare membangun ulang sendiri; 1–3 menit kemudian artikel sudah tayang.

Paragraf berbahasa Arab cukup ditulis sebagai paragraf tersendiri — otomatis
dibuat rata kanan dan diperbesar.

### 6B. Lewat GitHub langsung (tanpa Bagian 3–5)

Bisa dari HP juga:

1. Buka repositori di `github.com` → folder **`tulisan`**
2. **Add file** → **Create new file**
3. Nama berkas: `judul-artikel.md` (huruf kecil, pisah dengan tanda minus —
   ini jadi alamatnya: `konsultasifiqih.com/judul-artikel/`)
4. Isi dengan format ini:

```markdown
---
judul: Hukum Bermain Catur
tanggal: 2026-09-12
penulis: Ustadz Dr. Awwaluz Zikri, Lc. MA
kategori: Fikih Muamalat
draf: tidak
---

Isi artikel di sini.
```

5. **Commit changes**

### 6C. Lewat komputer ini

```bash
py artikel_baru.py "Judul Artikel"
```

Sunting berkas yang terbentuk di `tulisan/`, lalu:

```bash
git add .
git commit -m "Artikel baru"
git push
```

---

## Kalau macet

| Gejala | Sebabnya biasanya |
|---|---|
| `git push` ditolak, "repository not found" | Username di alamat remote salah, atau repositori belum dibuat. Cek: `git remote -v` |
| `git push` minta password terus | Ketik `git config --global credential.helper manager` lalu ulangi push |
| Build Cloudflare gagal, "No such file bangun_situs.py" | Build output directory atau build command salah ketik. Cek Bagian 2.2 |
| Build gagal menyebut `markdown` | Build command-nya belum memuat `pip install -r requirements.txt` |
| `/admin/` bilang "Editor belum disiapkan" | `situs.json` belum terisi, atau perubahannya belum di-push |
| Klik Login, jendela terbuka lalu tak terjadi apa-apa | Callback URL di GitHub (Bagian 3.1) tidak sama persis dengan alamat Worker |
| Login gagal, "State tidak cocok" | Coba lagi dengan jendela baru; biasanya karena popup lama masih terbuka |
| Artikel sudah di-publish tapi belum tampil | Masih `draf: ya`, atau build belum selesai — cek tab *Deployments* di Pages |
| Situs masih "Account Suspended" | Record A lama `198.54.116.42` belum dihapus di DNS Cloudflare |

---

## Ringkasan alamat

| Keperluan | Alamat |
|---|---|
| Situs | `https://konsultasifiqih.com` |
| Editor | `https://konsultasifiqih.com/admin/` |
| Alamat sementara Pages | `https://konsultasifiqih.pages.dev` |
| Worker login | `https://konsultasifiqih-oauth.ajengansubang.workers.dev` |
| Repositori | `https://github.com/allawimandan/konsultasifiqih` |
