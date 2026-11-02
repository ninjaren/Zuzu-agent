@echo off
cd /d "%~dp0"

echo 1/4 啟動 Ollama 服務...
set OLLAMA_KEEP_ALIVE=3600
start "" ollama serve

echo 2/4 等待服務就緒...
timeout /t 3 /nobreak >nul

echo 3/4 拉取模型（已有則跳過）...
ollama pull qwen3:8b
ollama pull nomic-embed-text

echo 4/4 啟動 Web 介面...
explorer http://127.0.0.1:5000
python app.py
pause
