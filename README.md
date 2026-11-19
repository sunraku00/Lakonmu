# Generator Formulir Dukcapil F-2.01 A (AI Lokal Ollama & Stateless Extractor)

Aplikasi web modern berbasis **FastAPI**, **PyMuPDF**, dan **AI Lokal Ollama** untuk mengekstrak data mentah hasil copy-paste dari berbagai situs (SIMRS, Puskesmas, portal kesehatan, chat, dll.) dan secara otomatis mengisi serta men-generate formulir resmi **F-2.01 A (Pelaporan Pencatatan Sipil di Dalam Wilayah NKRI)** menjadi dokumen PDF siap cetak.

Sistem ini dikonfigurasikan secara khusus untuk **menggunakan AI Lokal (Ollama)** sebagai mesin utama pemrosesan teks, menjamin **100% data kependudukan (NIK, KK, nama warga) bersifat privat, offline, dan sesuai dengan amanat UU No. 27 Tahun 2022 tentang Perlindungan Data Pribadi (UU PDP)**.

---

## 💻 Panduan Konfigurasi AI Lokal Ollama

### 1. Instalasi Ollama di Windows
1. Unduh installer Ollama untuk Windows dari situs resmi:
   👉 **[https://ollama.com/download](https://ollama.com/download)**
2. Jalankan file `OllamaSetup.exe` hingga selesai. Ollama akan otomatis berjalan di latar belakang pada alamat `http://localhost:11434`.

### 2. Mengunduh & Menjalankan Model AI Lokal
Buka Terminal / PowerShell / Command Prompt dan jalankan salah satu model berikut:

* **Pilihan 1 (Paling Direkomendasikan untuk Bahasa Indonesia & Format JSON):**
  ```bash
  ollama run qwen2.5:7b
  ```
* **Pilihan 2 (Model Sangat Ringan untuk PC / Laptop Tanpa GPU Khusus):**
  ```bash
  ollama run qwen2.5:3b
  ```
  atau
  ```bash
  ollama run llama3.2:3b
  ```
* **Pilihan 3 (Standar Internasional):**
  ```bash
  ollama run llama3.1:8b
  ```

### 3. Integrasi Otomatis dengan Aplikasi Ini
* Saat aplikasi web dibuka di `http://localhost:8000`, sistem akan secara otomatis mengecek status server Ollama lokal (`http://localhost:11434`).
* Jika Ollama aktif, daftar seluruh model yang terinstal di komputer Anda akan otomatis muncul di dropdown pilihan model.
* **Fitur Fallback Aman:** Jika Ollama belum sempat dijalankan saat Anda mengklik tombol *"Generate PDF"*, sistem secara cerdas akan otomatis menggunakan **Smart Regex Parser bawaan** sehingga pembuatan formulir PDF tetap berhasil tanpa macet!

---

## 🚀 Fitur Utama Sistem

1. **Konfigurasi Utama: Local AI (Ollama)**:
   - Menggunakan model lokal (seperti `qwen2.5:7b`) untuk mengekstrak entitas data secara cerdas tanpa internet.
2. **Satu Textarea & Satu Tombol Generate PDF**:
   - Cukup tempelkan teks mentah apa adanya, lalu tekan tombol **"Generate PDF F-2.01 A"**.
3. **Stateless & Zero Data Storage (Jaminan Privasi)**:
   - **Tidak ada database** dan **tidak ada file data pribadi yang disimpan**.
   - Seluruh pemrosesan (ekstraksi teks $\rightarrow$ manipulasi template PDF $\rightarrow$ streaming PDF) berlangsung murni **in-memory (RAM)** dan langsung di-download ke perangkat pengguna.
4. **Template Resmi Sesuai Permendagri F-2.01 A**:
   - Dokumen output di-stamp langsung di atas template resmi `F-2.01 A.pdf` dengan presisi tinggi:
     - NIK dan Nomor KK dicetak rapi pada 16 kotak grid karakter resmi Dukcapil.
     - Tanda centang vektor otomatis pada pilihan peristiwa (Kelahiran, Kematian, Lahir Mati), jenis kelamin, fasilitas kesehatan, dll.
5. **Pratinjau Langsung & Editor Interaktif**:
   - PDF dapat langsung dilihat di halaman web (*embedded viewer*) dan diunduh dengan 1 klik.
   - Tab editor interaktif memungkinkan peninjauan dan penyuntingan data hasil deteksi AI sebelum meng-generate ulang PDF.

---

## 🛠️ Cara Menjalankan Aplikasi

1. **Cara Cepat (Windows)**:
   Klik dua kali file `run.bat` di folder proyek ini.
2. **Cara Terminal / PowerShell**:
   ```powershell
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```
3. Buka peramban (browser) di alamat:
   ```
   http://localhost:8000
   ```

---

## 📁 Struktur File
- `main.py` : Server FastAPI yang melayani UI web dan endpoint API ekstraksi serta pembuatan PDF.
- `pdf_engine.py` : Mesin pengisi template formulir F-2.01 A berbasis PyMuPDF dengan koordinat presisi.
- `extractor.py` : Mesin ekstraksi data (Gemini API, Ollama, OpenAI, dan Smart Regex fallback).
- `static/index.html` : Antarmuka web single-page responsif dengan Tailwind CSS.
- `F-2.01 A.pdf` : Template resmi Formulir Pelaporan Pencatatan Sipil di Wilayah NKRI.
- `run.bat` : Script peluncur cepat 1-klik untuk Windows.
