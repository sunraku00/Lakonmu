@echo off
title Generator Formulir F-2.01 A Dukcapil (Ollama AI)
color 0B

echo =======================================================================
echo   GENERATOR FORMULIR F-2.01 A DUKCAPIL (1-CLICK AUTO LAUNCHER)
echo =======================================================================
echo.

:: 1. Cek apakah Python terdeteksi di PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python tidak terdeteksi di sistem ini!
    echo Silakan unduh dan pasang Python (versi 3.10 ke atas) dari:
    echo https://www.python.org/downloads/
    echo PENTING: Pastikan centang "Add Python to PATH" saat instalasi.
    echo.
    pause
    exit /b 1
)

:: 2. Cek apakah folder .venv sudah ada di perangkat ini
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment (.venv) belum ada di perangkat ini.
    echo [INFO] Sedang membuat .venv baru secara otomatis...
    python -m venv .venv
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Gagal membuat virtual environment (.venv)!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment (.venv) berhasil dibuat.
    echo.
)

:: 3. Aktifkan virtual environment (.venv)
echo [INFO] Mengaktifkan virtual environment (.venv)...
call .venv\Scripts\activate.bat

:: 4. Cek kelengkapan pustaka/dependencies
python -c "import fastapi, pymupdf, reportlab" >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Mengunduh dan memasang library dari requirements.txt...
    echo (Proses ini hanya berjalan sekali saat pertama kali dijalankan)
    python -m pip install --upgrade pip >nul 2>nul
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Gagal memasang library. Pastikan komputer terhubung ke internet.
        pause
        exit /b 1
    )
    echo [SUCCESS] Semua library berhasil dipasang!
    echo.
)

:: 5. Siap menjalankan server
echo =======================================================================
echo   - Status Lingkungan: Virtual Environment (.venv) Aktif
echo   - Endpoint Server  : http://localhost:8000
echo   - Mode Ekstraksi   : Local Ollama / Smart Regex Offline (UU PDP Aman)
echo =======================================================================
echo   Membuka peramban ke http://localhost:8000 ...
start http://localhost:8000
echo   Menjalankan server FastAPI...
echo   Tekan Ctrl+C untuk menghentikan server kapan saja.
echo =======================================================================
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
