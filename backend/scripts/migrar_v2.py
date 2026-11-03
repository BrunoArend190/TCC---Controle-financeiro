"""Atualiza um banco já existente para a v2 (orçamentos e despesas recorrentes).

Só adiciona estruturas; nenhum dado é alterado. Pode ser executado mais de uma vez.
Uso (na pasta backend): .venv/Scripts/python.exe scripts/migrar_v2.py
"""
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402

SCHEMA = (Path(__file__).resolve().parent.parent / "database" / "schema.sql").read_text(encoding="utf-8")
SEPARADOR = "-- ---------------------------------------------------------------------\n"


def bloco(inicio: str, fim: str) -> str:
    """Recorta do schema.sql o trecho entre dois marcadores, evitando duplicar as definições."""
    i = SCHEMA.index(inicio)
    return SCHEMA[i : SCHEMA.index(fim, i)]


def main() -> None:
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as con:
        if con.execute("SELECT to_regclass('public.orcamento')").fetchone()[0]:
            print("Banco já está na v2.")
            return
        con.execute("ALTER TYPE status_despesa ADD VALUE IF NOT EXISTS 'recorrente'")
        con.commit()

        con.execute("DROP TRIGGER trg_valida_categoria_despesa ON despesa")
        con.execute("DROP FUNCTION fn_valida_categoria_despesa()")
        # função + tabelas despesa_recorrente e orcamento, exatamente como no schema.sql
        con.execute(bloco("CREATE FUNCTION fn_valida_categoria_usuario", SEPARADOR + "-- Tabela: despesa\n"))
        con.execute(bloco("CREATE TRIGGER trg_valida_categoria_despesa", SEPARADOR + "-- Tabela: comprovante"))
        con.execute(
            "ALTER TABLE despesa ADD COLUMN id_recorrente INTEGER NULL "
            "REFERENCES despesa_recorrente(id_recorrente) ON DELETE SET NULL"
        )
        con.execute("ALTER TABLE despesa ADD CONSTRAINT uq_despesa_recorrente_data UNIQUE (id_recorrente, data_despesa)")
    print("Banco atualizado para a v2.")


if __name__ == "__main__":
    main()
