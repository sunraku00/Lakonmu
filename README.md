# Generator Formulir Dukcapil F-2.01 A (Stateless & AI-Assisted)

Aplikasi web modern berbasis **FastAPI**, **PyMuPDF**, dan **AI (Local Ollama / Smart Regex)** untuk mengekstrak data mentah hasil copy-paste (termasuk hasil **Ctrl+A acak dari SIAK Terpusat**, SIMRS RS, Puskesmas, WA, dll.) dan secara otomatis mencetak formulir resmi **F-2.01 A (Pelaporan Pencatatan Sipil di Dalam Wilayah NKRI)** menjadi dokumen PDF siap cetak.

Sistem ini didesain **100% Stateless & Zero-Storage** — tidak ada database dan tidak ada data kependudukan (NIK/KK) yang disimpan ke disk/server, menjamin kepatuhan penuh terhadap **UU No. 27 Tahun 2022 tentang Perlindungan Data Pribadi (UU PDP)**.

---

## 🐳 Cara Menjalankan dengan Docker (Paling Mudah)

Pihak lain atau server deployment cukup memiliki **Docker & Docker Compose** terinstal di komputernya.

### 1. Jalankan Aplikasi
Buka Terminal / Command Prompt / PowerShell di folder ini, lalu jalankan:

```bash
docker compose up -d
```
*(Atau `docker compose up` jika ingin melihat log server langsung di terminal).*

### 2. Buka Aplikasi di Browser
Buka peramban di:
👉 **[http://localhost:8000](http://localhost:8000)**

### 3. Menghentikan Aplikasi
```bash
docker compose down
```

---

## 💻 Cara Menjalankan Tanpa Docker (Native Python)

Jika ingin menjalankan langsung di sistem host:

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Jalankan Server:**
   * Di Windows: Cukup klik ganda file `run.bat`
   * Atau via terminal:
     ```bash
     python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
     ```
3. Buka **[http://localhost:8000](http://localhost:8000)** di browser.

---

## 🚀 Fitur Unggulan

1. **Pemilihan 3 Peristiwa Langsung (Kelahiran, Lahir Mati, Kematian)**:
   - Tombol selektor cepat di bagian atas yang langsung mengarahkan template PDF resmi:
     - **Kelahiran** $\rightarrow$ Halaman 1 (Page 0)
     - **Lahir Mati** $\rightarrow$ Halaman 2 (Page 1)
     - **Kematian** $\rightarrow$ Halaman 3 (Page 2)
2. **5 Kotak Input Khusus + 1 Kotak Global**:
   - `1. DATA PERISTIWA` (Bayi / Lahir Mati / Jenazah / RS / Puskesmas)
   - `2. DATA PELAPOR` (Nama, NIK, No. KK, Umur, Pekerjaan, Alamat, Hubungan)
   - `3. DATA ORANG TUA` (Tersedia sub-toggle: Gabung vs Pisah Ayah & Ibu)
   - `4. DATA SAKSI I` (Nama, NIK, Umur, Pekerjaan, Alamat)
   - `5. DATA SAKSI II` (Nama, NIK, Umur, Pekerjaan, Alamat)
   - *Opsi toggle ke 1 Kotak Global jika seluruh teks disatukan dalam satu salinan.*
3. **Tahan Banting Terhadap Data Acak SIAK (Ctrl+A)**:
   - Mampu mengekstrak data tabel SIAK yang terpisah tab (`\t`), label yang terbalik (`3174... NIK`, `38 Tahun Umur`), nama yang mendahului NIK, dan memilah baris Kepala Keluarga vs Istri secara otomatis.
4. **Dukungan AI Ganda (Lokal & Offline)**:
   - **Local AI (Ollama)**: Menggunakan model lokal seperti `qwen2.5:7b` tanpa internet.
   - **Smart Regex Offline**: Berjalan 100% offline seketika tanpa perlu setup AI jika Ollama belum terpasang.
5. **Output PDF Resmi Dukcapil Sesuai Permendagri F-2.01 A**:
   - NIK & KK dicetak pada 16 kotak grid resmi.
   - Tanda centang vektor akurat pada jenis kelamin, jenis kelahiran, tempat dilahirkan, penolong, dll.

---

## 📁 Struktur File Proyek

```
Folder Baru/
├── Dockerfile                  # Spesifikasi container Docker Linux (Python 3.11-slim)
├── docker-compose.yml          # Konfigurasi orchestrasi 1-klik (docker compose up)
├── requirements.txt            # Daftar pustaka Python yang dibutuhkan
├── .dockerignore               # File filter agar build image Docker cepat & ringan
├── main.py                     # API FastAPI & penyaji web
├── extractor.py                # Engine ekstraksi AI Ollama & Smart Regex tahan teks acak
├── pdf_engine.py               # Engine pengisi formulir template PDF F-2.01 A
├── static/
│   └── index.html              # Antarmuka web responsif (Tailwind CSS)
├── Formulir F-2.01 A ... .pdf  # Template formulir resmi 3 halaman
├── run.bat                     # Peluncur cepat untuk Windows
└── README.md                   # Dokumentasi lengkap
```
