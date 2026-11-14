@echo off
rem Inicia o sistema completo: Ollama (NuExtract3), API (FastAPI), interface (Vite) e link publico (Cloudflare Tunnel).
rem Pode ser executado de qualquer pasta. Para encerrar, feche as janelas "API", "Frontend" e "Link publico".

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
rem    SEM_HMR=1 desliga o recarregamento automatico, que derrubava a pagina no celular pelo link publico
start "Frontend" cmd /k "cd /d "%RAIZ%frontend" && set SEM_HMR=1&& npm run dev"

rem 4) Link publico (Cloudflare Tunnel): o endereco https://....trycloudflare.com aparece na janela "Link publico"
where cloudflared >nul 2>nul
if errorlevel 1 (
    echo cloudflared nao encontrado: o sistema roda so localmente. Instale com: winget install Cloudflare.cloudflared
) else (
    start "Link publico" cmd /k "cloudflared tunnel --url http://localhost:5173"
)
