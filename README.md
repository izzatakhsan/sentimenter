# **Sentimenter — Analisis Sentimen IndoBERT**

Sentimenter adalah aplikasi web modern berbasis **Flask** yang memanfaatkan kekuatan model **IndoBERT** (`crypter70/IndoBERT-Sentiment-Analysis`) dari Hugging Face untuk melakukan **analisis sentimen teks berbahasa Indonesia**.

Aplikasi ini dikembangkan untuk memfasilitasi analisis sentimen secara instan, baik untuk teks tunggal (input manual) maupun secara massal (batch upload) menggunakan berkas CSV/Excel, dengan visualisasi data yang interaktif dan penyimpanan riwayat analisis berbasis cloud.

Live demo aplikasi ini dapat diakses pada: **[s.id/sentimenter](https://s.id/sentimenter)**

---

## 🚀 **Fitur Utama**

### 1. **Analisis Sentimen Teks Tunggal**
* Memprediksi emosi/sentimen di balik kalimat bahasa Indonesia secara real-time.
* Hasil klasifikasi dikelompokkan menjadi 3 kelas: **Positif**, **Netral**, dan **Negatif**.

### 2. **Analisis Berkas Massal (Batch Analysis)**
* Mengunggah berkas berformat **`.csv`** atau **`.xlsx`** (Excel).
* Pengguna dapat memilih kolom teks spesifik yang ingin dianalisis secara dinamis.
* Menghasilkan tabel hasil klasifikasi interaktif langsung di halaman web.
* Hasil analisis dapat diunduh kembali dalam format berkas `.csv`.

### 3. **Visualisasi Data Dinamis**
* **Diagram Interaktif (Chart.js)**: Menyajikan visualisasi Pie Chart dan Bar Chart untuk distribusi persentase sentimen.
* **Word Cloud**: Awan kata yang dihasilkan dari ekstraksi teks berkas masukan, disaring menggunakan *stopwords* bahasa Indonesia untuk memunculkan kata-kata kunci dominan.

### 4. **Sistem Autentikasi & Akun Pengguna**
* Fitur registrasi dan masuk (login) bagi pengguna untuk menyimpan pekerjaan mereka.
* Pengamanan enkripsi kata sandi menggunakan pustaka `werkzeug.security`.

### 5. **Penyimpanan Riwayat Analisis Cloud**
* Menyimpan hasil analisis massal (berkas, kolom, ringkasan statistik sentimen, word cloud, dan tabel hasil) ke database **PostgreSQL (Supabase)**.
* Pengguna terdaftar dapat melihat kembali daftar analisis terdahulu, memantau visualisasinya, mengunduh file hasil analisis lamanya, atau menghapus riwayat tersebut.

### 6. **Aspek Keamanan & Optimasi Produksi**
* **Rate Limiting (`flask-limiter`)**: Mencegah spamming atau brute-force requests per alamat IP.
* **CSRF Protection (`flask-wtf`)**: Melindungi formulir aplikasi dari ancaman Cross-Site Request Forgery.
* **Lazy Loading Model**: Menunda pemuatan model deep learning IndoBERT hingga dibutuhkan (saat inferensi pertama kali) untuk mempercepat waktu startup awal server.
* **Proxy Support (`ProxyFix`)**: Konfigurasi agar rate limiter dan keamanan session membaca IP client asli saat dideploy di balik reverse proxy (seperti di Hugging Face Spaces).

---

## 🛠️ **Teknologi yang Digunakan**

* **Core Backend & Routing**: Python 3.9+, Flask
* **Deep Learning (NLP)**: PyTorch, Hugging Face Transformers (`IndoBERT`)
* **Analisis & Manipulasi Data**: Pandas, OpenPyXL
* **Pembuatan Visualisasi**: Matplotlib, WordCloud, Chart.js (Frontend)
* **Penyimpanan Data**: PostgreSQL / Supabase DB (melalui `psycopg2`)
* **Keamanan**: WTForms CSRF, Flask-Limiter, Werkzeug Security
* **Deployment**: Docker, Gunicorn

---

## 📁 **Struktur Proyek**

```text
/sentimenter
│
├── /static/
│   ├── /css/
│   │   └── style.css            # Desain kustom bertema Neo-Brutalism
│   └── /images/
│       ├── ikn.png              # Gambar data dashboard statis IKN
│       ├── whoosh.png           # Gambar data dashboard statis Whoosh
│       └── logo-sentimenter.png # Favicon website
│
├── /templates/
│   ├── layout.html              # Kerangka dasar web & navigasi
│   ├── home.html                # Halaman landing
│   ├── dashboard.html           # Halaman visualisasi data sentimen statis
│   ├── analysis.html            # Halaman utama analisis teks tunggal & file
│   ├── history.html             # Daftar riwayat analisis pengguna (login required)
│   ├── history_detail.html      # Tampilan detail riwayat analisis tersimpan
│   ├── login.html               # Form masuk akun
│   ├── register.html            # Form daftar akun baru
│   └── about.html               # Halaman informasi developer & aplikasi
│
├── app.py                       # Routing Flask, rate limit, dan alur aplikasi utama
├── model.py                     # Manajemen model IndoBERT, lazy load, inferensi, & wordcloud
├── database.py                  # Penghubung PostgreSQL, inisialisasi tabel, query CRUD user & riwayat
├── .env.example                 # Contoh templat variabel lingkungan
├── Dockerfile                   # Konfigurasi container docker Hugging Face Spaces
├── Procfile                     # Konfigurasi deployment Heroku/sejenisnya
├── requirements.txt             # Daftar dependensi Python
└── README.md                    # Dokumentasi proyek
```

---

## 🔧 **Cara Menjalankan Aplikasi Secara Lokal**

### **1. Unduh Kode Sumber**
Lakukan clone repositori ini atau salin seluruh isi direktori proyek ke dalam komputer Anda.

### **2. Buat & Aktifkan Virtual Environment**
Sangat disarankan menggunakan virtual environment agar pustaka tidak berbenturan.

```bash
# Membuat virtual environment
python -m venv venv

# Mengaktifkan (Windows PowerShell)
.\venv\Scripts\activate

# Mengaktifkan (Windows CMD)
venv\Scripts\activate

# Mengaktifkan (macOS / Linux)
source venv/bin/activate
```

### **3. Pasang Dependensi**
Pasang pustaka-pustaka Python yang diperlukan:
```bash
pip install -r requirements.txt
```
> **Catatan**: Unduhan pustaka `torch` (PyTorch) berukuran cukup besar dan proses instalasi mungkin memakan waktu beberapa menit.

### **4. Konfigurasi Variabel Lingkungan**
Salin berkas `.env.example` menjadi `.env` baru:
```bash
cp .env.example .env
```
Buka file `.env` tersebut dan sesuaikan nilai variabelnya:
* `SECRET_KEY`: String acak panjang untuk mengenkripsi cookie session.
* `DATABASE_URL`: URI koneksi database PostgreSQL Anda (misal dari proyek Supabase).

### **5. Jalankan Aplikasi**
Jalankan server pengembangan Flask:
```bash
flask run
```
Atau jika menggunakan python langsung:
```bash
python app.py
```
Aplikasi akan mendeteksi skema database dan otomatis membuat tabel `users` serta `analyses` jika belum terbentuk sebelumnya. Pada eksekusi pertama kali, aplikasi akan mengunduh bobot model IndoBERT (~400 MB) dari Hugging Face ke folder cache lokal komputer Anda secara otomatis.

### **6. Akses Aplikasi**
Buka peramban (browser) Anda dan akses alamat berikut:
```text
http://127.0.0.1:5000
```

---

## 🐳 **Deployment dengan Docker**

Proyek ini dilengkapi dengan `Dockerfile` yang telah dikustomisasi dan dioptimalkan agar dapat berjalan langsung di Hugging Face Spaces atau server VPS menggunakan Docker.

### **Menjalankan Container secara Lokal**
1. **Bangun Docker Image**:
   ```bash
   docker build -t sentimenter-app .
   ```
   *Selama proses build, model IndoBERT akan diunduh dan disimpan di dalam image agar startup container menjadi instan saat dijalankan.*

2. **Jalankan Container**:
   ```bash
   docker run -p 7860:7860 --env-file .env sentimenter-app
   ```
3. **Buka Aplikasi**:
   Akses melalui `http://localhost:7860`.

---

## 👥 **Profil Pengembang**
Website ini dikembangkan oleh **BRIN devs**, sekumpulan mahasiswa Sains Data yang bersemangat mengeksplorasi implementasi praktis teknologi kecerdasan buatan, pemrosesan bahasa alami (NLP), dan analisis data untuk memecahkan tantangan dunia nyata.