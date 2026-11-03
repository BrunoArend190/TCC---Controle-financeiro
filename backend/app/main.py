import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import engine
from app.routers import auth, categorias, despesas, orcamentos, recorrentes, relatorios
from app.services.extracao import ollama_disponivel

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Gestão Financeira Pessoal com OCR",
    description="API do TCC: registro de despesas com extração automática de comprovantes via NuExtract3.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(despesas.router)
app.include_router(recorrentes.router)
app.include_router(orcamentos.router)
app.include_router(relatorios.router)


@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse("/docs")


@app.get("/health", tags=["Sistema"])
def health():
    """Verifica se o banco de dados e o Ollama (NuExtract3) estão acessíveis."""
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
        banco = True
    except Exception:
        banco = False
    return {"banco": banco, "ollama": ollama_disponivel(), "modelo": get_settings().nuextract_modelo}
