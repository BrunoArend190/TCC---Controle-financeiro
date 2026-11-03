"""Inicia a API em modo de desenvolvimento.

Uso (na pasta backend):
    python run.py

Equivale a: .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
Se for chamado por outro Python (sem o .venv ativo), reinicia sozinho usando o Python do .venv.
"""
import subprocess
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
PYTHON_VENV = PASTA / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

if __name__ == "__main__":
    if Path(sys.prefix).resolve() != (PASTA / ".venv").resolve():
        if not PYTHON_VENV.exists():
            sys.exit("Ambiente virtual não encontrado. Crie com: python -m venv .venv && pip install -r requirements.txt")
        try:
            sys.exit(subprocess.call([str(PYTHON_VENV), __file__], cwd=PASTA))
        except KeyboardInterrupt:
            sys.exit(0)

    import uvicorn

    uvicorn.run("app.main:app", port=8000, reload=True, app_dir=str(PASTA))
