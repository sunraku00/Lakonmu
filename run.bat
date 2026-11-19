@echo off
title Generator Formulir F-2.01 A Dukcapil (Ollama AI)
color 0B
echo =======================================================================
echo   GENERATOR FORMULIR F-2.01 A DUKCAPIL (AI LOKAL OLLAMA)
echo =======================================================================
echo   - Mode AI Utama  : Local Ollama (100%% Offline, Privat, UU PDP)
echo   - Default Model  : qwen2.5:7b (atau qwen2.5:3b / llama3.2)
echo   - Endpoint Server: http://localhost:8000
echo.
echo   * TIPS OLLAMA:
echo     Pastikan Ollama sudah berjalan dengan menjalankan perintah:
echo     ollama run qwen2.5:7b
echo.
echo     (Jika Ollama belum aktif, sistem otomatis beralih ke Smart Regex
echo      sehingga formulir tetap dapat di-generate tanpa error).
echo =======================================================================
echo   Membuka server web di http://localhost:8000 ...
echo   Tekan Ctrl+C untuk menghentikan server.
echo =======================================================================
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
