# Generator Formulir Dukcapil F-2.01 A (Stateless & AI-Assisted)

Aplikasi web modern berbasis **FastAPI**, **PyMuPDF**, dan **AI (Local Ollama / Smart Regex)** untuk mengekstrak data mentah hasil copy-paste (termasuk hasil **Ctrl+A acak dari SIAK Terpusat**, SIMRS RS, Puskesmas, WA, dll.) dan secara otomatis mencetak formulir resmi **F-2.01 A (Pelaporan Pencatatan Sipil di Dalam Wilayah NKRI)** menjadi dokumen PDF siap cetak.

Sistem ini didesain **100% Stateless & Zero-Storage** — tidak ada database dan tidak ada data kependudukan (NIK/KK) yang disimpan ke disk/server, menjamin kepatuhan penuh terhadap **UU No. 27 Tahun 2022 tentang Perlindungan Data Pribadi (UU PDP)**.

---

## 🤝 Panduan Setup & Menjalankan untuk Tim (Kolaborator)

Project ini didesain agar sangat mudah dijalankan di komputer mana pun tanpa konflik konfigurasi environment (`.venv` bersifat lokal dan otomatis terabaikan di Git melalui `.gitignore`).

---

### 🐳 Opsi 1: Menggunakan Docker (Rekomendasi Utama - Paling Mudah)
Jika teman Anda memiliki **Docker Desktop** terpasang, mereka **tidak perlu menginstall Python sama sekali**:

1. Buka Terminal / CMD / PowerShell di dalam folder project ini.
2. Jalankan perintah:
   ```bash
   docker compose up -d
   ```
   *(Atau `docker compose up --build -d` jika baru saja pull pembaruan kode).*
3. Buka peramban di: 👉 **[http://localhost:8000](http://localhost:8000)**
4. Untuk menghentikan: `docker compose down`

---

### ⚡ Opsi 2: Windows 1-Click Launcher (Sangat Praktis untuk Windows)
Jika teman Anda menggunakan Windows dan memiliki Python:

1. Pastikan Python 3.10+ sudah terpasang dan dicentang opsi *"Add Python to PATH"*.
2. Cukup **Klik Ganda (Double Click)** file **`run.bat`**.
3. **`run.bat` secara otomatis akan:**
   - Mendeteksi apakah folder `.venv` sudah ada. Jika belum, otomatis membuat `.venv` lokal baru untuk perangkat teman Anda.
   - Mengaktifkan `.venv`.
   - Menginstall seluruh library dari `requirements.txt` secara otomatis.
   - Membuka browser ke `http://localhost:8000` dan menyalakan server!

---

### 💻 Opsi 3: Manual Terminal Setup (VS Code / Terminal / Linux / Mac)
Jika teman Anda terbiasa menggunakan terminal manual:

**Windows (PowerShell / Command Prompt):**
```bash
# 1. Buat virtual environment lokal
python -m venv .venv

# 2. Aktifkan virtual environment
# Jika PowerShell:
.\.venv\Scripts\Activate.ps1
# Jika Command Prompt (CMD):
.venv\Scripts\activate.bat

# 3. Pasang semua pustaka
pip install -r requirements.txt

# 4. Jalankan aplikasi
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

> [!NOTE]
> **Mengapa file `.venv` dan `pyvenv.cfg` tidak di-share ke Git?**
> File `pyvenv.cfg` dan seluruh folder `.venv` berisi path absolut spesifik ke user & direktori sistem operasi komputer Anda (misal: `C:\Users\KicenZeus\...`). Jika folder tersebut dipush ke Git dan di-clone oleh teman Anda, Python mereka akan error karena direktori tersebut tidak ada di komputer mereka. Oleh sebab itu, setiap komputer harus membuat `.venv` lokalnya sendiri (yang kini sudah diotomatisasi penuh oleh `run.bat` atau Docker).

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
