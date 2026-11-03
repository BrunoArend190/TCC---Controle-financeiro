@echo off
rem Inicia o sistema completo: Ollama (NuExtract3), API (FastAPI) e interface (Vite).
rem Pode ser executado de qualquer pasta. Para encerrar, feche as janelas "API" e "Frontend".

set RAIZ=%~dp0

rem 1) Ollama: abre o aplicativo se ainda não estiver rodando
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
if errorlevel 1 (
    echo Iniciando o Ollama...
    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
)

rem 2) API em uma janela propria
start "API" cmd /k "cd /d "%RAIZ%backend" && .venv\Scripts\python.exe run.py"

rem 3) Frontend em outra janela (o Quasar abre o navegador sozinho)
start "Frontend" cmd /k "cd /d "%RAIZ%frontend" && npm run dev"
