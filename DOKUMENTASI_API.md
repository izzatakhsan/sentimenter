# Dokumentasi API & Penerapan Keamanan

Panduan teknis antarmuka aplikasi pemrograman (API) dan implementasi keamanan pada sistem analisis sentimen IndoBERT **Sentimenter**.

Aplikasi **Sentimenter** adalah aplikasi web berbasis Flask yang digunakan untuk memprediksi sentimen (Positif, Netral, Negatif) dari masukan teks tunggal atau batch (melalui file CSV/Excel) dengan model pembelajaran mendalam (Deep Learning) IndoBERT (`crypter70/IndoBERT-Sentiment-Analysis`). Berkas historis analisis batch disimpan ke database PostgreSQL (Supabase).

---

## 🔌 API Endpoints

Berikut adalah spesifikasi teknis dari masing-masing API router yang digunakan pada aplikasi:

### 1. Halaman Utama (Home)
* **URL:** `/`
* **Method:** `GET`
* **Akses:** `Publik`
* **Deskripsi:** Merender dan menampilkan halaman beranda (landing page) aplikasi web.
* **Respons:**
  * **Tipe Konten:** `text/html`
  * **Isi:** Tampilan utama web yang memaparkan fitur umum Sentimenter.
* **Referensi Kode:** [app.py:L84-87](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 2. Dashboard Visualisasi
* **URL:** `/dashboard`
* **Method:** `GET`
* **Akses:** `Publik`
* **Deskripsi:** Menampilkan dashboard statistik sentimen yang bersifat statis untuk topik IKN dan Whoosh.
* **Respons:**
  * **Tipe Konten:** `text/html`
  * **Isi:** Halaman dashboard yang merender diagram sentimen IKN dan Whoosh menggunakan Chart.js.
* **Referensi Kode:** [app.py:L89-108](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 3. Halaman Analisis Sentimen
* **URL:** `/analysis`
* **Method:** `GET` | `POST`
* **Akses:** `Publik / Login`
* **Rate Limit:** `20 requests/minute`
* **Deskripsi:** Menangani proses formulir analisis sentimen, baik berupa teks tunggal atau unggahan file (CSV/Excel) secara massal.
* **Payload (POST - Teks Tunggal):**
  * `text_input` (String) - Kalimat yang ingin diklasifikasi sentimennya.
* **Payload (POST - File Upload):**
  * `text_column` (String) - Nama kolom teks di dalam berkas yang diunggah.
  * `file` (Berkas .csv / .xlsx) - Berkas tabel masukan. Maksimum 10MB.
* **Perilaku Sesi (Session Behavior):**
  * **Tamu (Guest):** Hasil CSV batch diunggah ke storage sementara lokal dan referensinya dimasukkan ke dalam session cookie untuk diunduh via `/download_temp`.
  * **Pengguna Terdaftar:** Data hasil langsung dikirim dan disimpan ke database PostgreSQL, sehingga tercatat permanen pada akun pengguna.
* **Referensi Kode:** [app.py:L110-208](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 4. Registrasi Akun Baru
* **URL:** `/register`
* **Method:** `GET` | `POST`
* **Akses:** `Publik (Tamu saja)`
* **Rate Limit:** `5 requests/minute`
* **Deskripsi:** Menangani pembuatan akun pengguna baru. Jika pengguna sudah login, sistem secara otomatis meredirect ke halaman beranda.
* **Payload (POST):**
  * `username` (String, Unik) - Nama pengguna baru.
  * `password` (String) - Kata sandi akun.
  * `confirm_password` (String) - Pengulangan kata sandi untuk kecocokan.
* **Referensi Kode:** [app.py:L210-240](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 5. Proses Masuk Pengguna
* **URL:** `/login`
* **Method:** `GET` | `POST`
* **Akses:** `Publik (Tamu saja)`
* **Rate Limit:** `5 requests/minute`
* **Deskripsi:** Melakukan otentikasi kredensial pengguna dan menginisialisasi sesi login.
* **Payload (POST):**
  * `username` (String) - Nama pengguna terdaftar.
  * `password` (String) - Kata sandi akun.
* **Respons:**
  * Jika sukses, kredensial user disimpan ke `session['user_id']` dan diarahkan ke Halaman Utama dengan flash message.
* **Referensi Kode:** [app.py:L242-266](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 6. Keluar Sesi
* **URL:** `/logout`
* **Method:** `GET`
* **Akses:** `Publik`
* **Deskripsi:** Menghapus dan membersihkan seluruh sesi pengguna yang aktif.
* **Respons:**
  * Melakukan eksekusi `session.clear()` lalu redirect ke Halaman Utama.
* **Referensi Kode:** [app.py:L268-273](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 7. Riwayat Analisis Pengguna
* **URL:** `/history`
* **Method:** `GET`
* **Akses:** `Login Diperlukan`
* **Deskripsi:** Menampilkan daftar ringkasan riwayat analisis batch yang pernah dijalankan oleh user.
* **Respons:**
  * **Tipe Konten:** `text/html`
  * **Isi:** Halaman yang merender daftar file, tanggal analisis, dan statistik rasio sentimen negatif/positif/netral.
* **Referensi Kode:** [app.py:L275-284](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 8. Detail Riwayat Analisis
* **URL:** `/history/<int:analysis_id>`
* **Method:** `GET`
* **Akses:** `Login Diperlukan`
* **Deskripsi:** Menampilkan rincian visualisasi (Word Cloud, Tabel Klasifikasi Data) dari satu instansi riwayat analisis batch yang tersimpan.
* **Respons:**
  * **Tipe Konten:** `text/html`
  * **Isi:** Halaman detail analisis berdasarkan `analysis_id`. Keamanan terisolasi penuh sehingga data tidak dapat disusupi user lain.
* **Referensi Kode:** [app.py:L286-298](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 9. Hapus Riwayat Analisis
* **URL:** `/history/<int:analysis_id>/delete`
* **Method:** `POST`
* **Akses:** `Login Diperlukan`
* **Deskripsi:** Menghapus data riwayat analisis tertentu dari database.
* **Respons:**
  * Redirect ke halaman `/history` disertai flash alert sukses/gagal.
* **Referensi Kode:** [app.py:L300-312](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 10. Unduh File Hasil Sementara (Tamu)
* **URL:** `/download_temp`
* **Method:** `GET`
* **Akses:** `Publik`
* **Deskripsi:** Mengunduh file CSV hasil pemrosesan sentimen sementara yang didefinisikan dalam folder uploads berdasarkan session token tamu.
* **Respons:**
  * **Tipe Konten:** `text/csv`
  * **Download Nama:** `[NamaFileAsli]_analisis.csv`
* **Referensi Kode:** [app.py:L314-331](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 11. Unduh File Hasil Riwayat (Login)
* **URL:** `/history/<int:analysis_id>/download`
* **Method:** `GET`
* **Akses:** `Login Diperlukan`
* **Deskripsi:** Mengunduh berkas CSV dari hasil analisis batch lama milik pengguna yang disimpan secara aman dalam database PostgreSQL.
* **Respons:**
  * **Tipe Konten:** `text/csv`
  * **Download Nama:** `[NamaFileAsli]_analisis.csv`
* **Referensi Kode:** [app.py:L333-352](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

### 12. Tentang Aplikasi
* **URL:** `/about`
* **Method:** `GET`
* **Akses:** `Publik`
* **Deskripsi:** Merender halaman penjelasan sistem dan pengembang aplikasi Sentimenter.
* **Referensi Kode:** [app.py:L354-357](https://github.com/izzatakhsan/sentimenter/blob/main/app.py)

---

## 🛡️ Penerapan Keamanan (Security)

Sistem Sentimenter dikonfigurasi menggunakan standar pengamanan web (OWASP top-10 mitigation) untuk mencegah celah eksploitasi data atau manipulasi server.

| Fitur Keamanan | Deskripsi | Referensi Kode |
| :--- | :--- | :--- |
| **Perlindungan CSRF** | Menggunakan pustaka `flask_wtf.csrf.CSRFProtect` secara global. Flask WTForms memvalidasi token CSRF unik yang disematkan dalam form HTML untuk memproses data pasca-submit (POST). | [app.py:L36](https://github.com/izzatakhsan/sentimenter/blob/main/app.py) |
| **Rate Limiting & ProxyFix** | Membatasi serangan DDoS / brute force login. Rute login & register dibatasi maks 5 req/menit, sedangkan inferensi AI dibatasi 20 req/menit. Dibuat adaptif via `ProxyFix` agar mengenali IP asli klien di balik reverse proxy. | [app.py:L23-24](https://github.com/izzatakhsan/sentimenter/blob/main/app.py) |
| **Sesi Cookie yang Aman** | Session Cookie dilindungi dengan tag `SESSION_COOKIE_HTTPONLY=True` untuk menangkal pencurian cookie via XSS, serta `SESSION_COOKIE_SAMESITE='Lax'` untuk menangkal CSRF. | [app.py:L32-33](https://github.com/izzatakhsan/sentimenter/blob/main/app.py) |
| **Keamanan Unggah File** | Membatasi ukuran berkas maks 10MB (`MAX_CONTENT_LENGTH`) untuk mencegah DoS. File dibatasi hanya ekstensi `.csv` dan `.xlsx` serta nama file dibersihkan menggunakan fungsi `secure_filename`. | [app.py:L29](https://github.com/izzatakhsan/sentimenter/blob/main/app.py) |
| **Hashing Kata Sandi** | Tidak pernah menyimpan password dalam bentuk plaintext. Menggunakan pustaka `werkzeug.security` dengan metode `generate_password_hash` (PBKDF2/scrypt) saat registrasi, serta dicocokkan via `check_password_hash` saat login. | [database.py:L78](https://github.com/izzatakhsan/sentimenter/blob/main/database.py) |
| **Pencegahan Serangan IDOR** | Mencegah modifikasi data orang lain secara ilegal. Setiap operasi data riwayat (baca detail, hapus, unduh) di filter menggunakan parameter ID Analisis DAN ID User yang sedang masuk secara bersamaan (`WHERE id = %s AND user_id = %s`). | [database.py:L202-208](https://github.com/izzatakhsan/sentimenter/blob/main/database.py) |
| **Pencegahan SQL Injection** | Menghindari pemakaian penggabungan string (string concatenation) pada penulisan query database. Library driver database `psycopg2` digunakan secara parameterized (menggunakan placeholder tuple `%s`). | [database.py:L109](https://github.com/izzatakhsan/sentimenter/blob/main/database.py) |
| **Kredensial Terenkripsi** | Semua parameter rahasia (seperti `DATABASE_URL` dan `SECRET_KEY`) dikelola melalui file `.env` eksternal menggunakan `python-dotenv`. Berkas ini dikecualikan dari Git (.gitignore). | [database.py:L10](https://github.com/izzatakhsan/sentimenter/blob/main/database.py) |
| **Keamanan Kontainer Docker** | Kontainer dikonfigurasi untuk berjalan dengan user non-root (UID 1000) bertajuk `user`, menghindari eskalasi akses root ke sistem operasi host di Hugging Face. | [Dockerfile:L14-17](https://github.com/izzatakhsan/sentimenter/blob/main/Dockerfile) |

---

## ⚙️ Cara Menjalankan & Pengujian Aplikasi

Berikut adalah langkah-langkah untuk menyiapkan dan menjalankan server pengujian API secara lokal:

### 1. Instalasi Dependensi
Instal pustaka Python yang dibutuhkan yang terdaftar dalam file `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Pengisian Environment File (.env)
Buat file baru bernama `.env` di direktori root program Anda:
```env
SECRET_KEY=kunci_rahasia_anda_yang_sangat_panjang_dan_aman
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

> [!WARNING]
> **Penting:** Gantilah nilai `[PASSWORD]` dan `[HOST]` sesuai kredensial koneksi database PostgreSQL / Supabase Anda yang valid.

### 3. Menjalankan Server Lokal
Jalankan perintah di bawah ini untuk memulai server Flask mode debug:
```bash
python app.py
```
Aplikasi web akan tersedia di tautan port lokal: [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

### 4. Menjalankan Mode Produksi (Production Gunicorn)
Untuk menjalankan aplikasi dengan load balancer yang stabil untuk environment produksi:
```bash
gunicorn -b 0.0.0.0:7860 app:app
```
