# Story Gym Dashboard

Dashboard YouTube Story Gym yang **diperbarui otomatis tiap 6 jam** oleh GitHub Actions, tanpa perlu komputer atau aplikasi Claude menyala.

- `scripts/fetch_stats.py` — mengambil data publik channel lewat YouTube Data API v3 (subscriber, penayangan, suka, komentar, komentar terbaru)
- `.github/workflows/update.yml` — menjalankan skrip tiap 6 jam, menyimpan riwayat, lalu menerbitkan dashboard
- `site/` — halaman dashboard (GitHub Pages)

## Pemasangan (sekali saja, ±30 menit)

### 1. Buat YouTube Data API key (gratis)
1. Buka https://console.cloud.google.com → login dengan akun Google channel.
2. Klik pilihan project di atas → **New Project** → nama `storygym-dashboard` → **Create**.
3. Menu **APIs & Services → Library** → cari **YouTube Data API v3** → **Enable**.
4. **APIs & Services → Credentials → Create credentials → API key**.
5. Klik **Edit API key** → bagian **API restrictions** → pilih **Restrict key** → centang **YouTube Data API v3** → **Save**.
6. Salin API key-nya. **Jangan bagikan ke siapa pun dan jangan tulis di file.**

### 2. Buat repository GitHub
1. Daftar/login di https://github.com.
2. Klik **+ → New repository** → nama `storygym-dashboard` → pilih **Public** (GitHub Pages gratis untuk repository publik) → **Create repository**.
3. Klik **uploading an existing file** → seret **semua isi** folder `storygym-dashboard` (folder `.github`, `scripts`, `site`, dan `README.md`) ke halaman → **Commit changes**.
   - Pastikan file `.github/workflows/update.yml` ikut terupload.

### 3. Simpan API key sebagai secret
**Settings → Secrets and variables → Actions → New repository secret**
- Name: `YOUTUBE_API_KEY`
- Secret: tempel API key → **Add secret**

### 4. Aktifkan izin dan GitHub Pages
- **Settings → Actions → General → Workflow permissions** → pilih **Read and write permissions** → **Save**.
- **Settings → Pages → Build and deployment → Source** → pilih **GitHub Actions**.

### 5. Jalankan pertama kali
**Actions → Update dashboard Story Gym → Run workflow**. Tunggu ±1 menit sampai centang hijau.

Dashboard tersedia di: `https://<username-github>.github.io/storygym-dashboard/`

## Catatan
- Jadwal: 08.00, 14.00, 20.00, 02.00 WITA. GitHub kadang menunda jadwal beberapa menit.
- Dashboard bersifat publik, tetapi hanya berisi data yang memang sudah publik di YouTube.
- Data khusus pemilik (misalnya "ditonton vs digeser", durasi tonton) belum termasuk; butuh YouTube Analytics API dengan login OAuth (tahap berikutnya).
- Kuota gratis YouTube API: 10.000 unit/hari. Setiap pembaruan memakai ±5 unit.
- Jika workflow merah: buka log di tab **Actions**. Pesan "YOUTUBE_API_KEY belum diisi" berarti langkah 3 belum dilakukan.
