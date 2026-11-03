"""Cria o banco (se não existir) e aplica database/schema.sql.

Uso (na pasta backend, com o venv ativo):
    python scripts/criar_banco.py
"""
import sys
from pathlib import Path

import psycopg
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402

SCHEMA = Path(__file__).resolve().parent.parent / "database" / "schema.sql"


def main() -> None:
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    info = psycopg.conninfo.conninfo_to_dict(url)
    nome_banco = info.get("dbname")

    # 1) cria o banco conectando no banco administrativo "postgres"
    with psycopg.connect(**{**info, "dbname": "postgres"}, autocommit=True) as conexao:
        existe = conexao.execute("SELECT 1 FROM pg_database WHERE datname = %s", (nome_banco,)).fetchone()
        if existe:
            print(f"Banco '{nome_banco}' já existe.")
        else:
            conexao.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8'").format(sql.Identifier(nome_banco)))
            print(f"Banco '{nome_banco}' criado.")

    # 2) aplica o schema se as tabelas ainda não existem
    with psycopg.connect(url) as conexao:
        if conexao.execute("SELECT to_regclass('public.usuario')").fetchone()[0]:
            print("Tabelas já existem; schema não reaplicado.")
            return
        conexao.execute(SCHEMA.read_text(encoding="utf-8"))
        print("Schema aplicado com sucesso.")


if __name__ == "__main__":
    main()
