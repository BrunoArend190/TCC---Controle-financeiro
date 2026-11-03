"""Lançamento automático das despesas recorrentes.

Não há processo agendado: as despesas vencidas são lançadas quando o usuário consulta
os dados. Assim, nada se perde se o sistema ficar dias (ou meses) desligado.
"""
from calendar import monthrange
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Despesa, DespesaRecorrente, StatusDespesa, Usuario


def _no_mes(ano: int, mes: int, dia: int) -> date:
    # dia 31 em um mês mais curto vira o último dia daquele mês
    return date(ano, mes, min(dia, monthrange(ano, mes)[1]))


def mes_seguinte(atual: date, dia: int) -> date:
    ano, mes = (atual.year + 1, 1) if atual.month == 12 else (atual.year, atual.month + 1)
    return _no_mes(ano, mes, dia)


def proxima_ocorrencia(dia: int, a_partir: date) -> date:
    """Primeira data com o dia informado que não seja anterior a `a_partir`."""
    candidata = _no_mes(a_partir.year, a_partir.month, dia)
    return candidata if candidata >= a_partir else mes_seguinte(a_partir, dia)


def lancar_pendentes(db: Session, usuario: Usuario) -> None:
    """Cria as despesas vencidas das recorrentes ativas do usuário."""
    hoje = date.today()
    # FOR UPDATE: o Dashboard faz chamadas simultâneas; só uma delas lança cada recorrente
    pendentes = db.scalars(
        select(DespesaRecorrente)
        .where(
            DespesaRecorrente.id_usuario == usuario.id_usuario,
            DespesaRecorrente.ativa.is_(True),
            DespesaRecorrente.proximo_lancamento <= hoje,
        )
        .with_for_update(of=DespesaRecorrente)
        .execution_options(populate_existing=True)
    ).unique().all()

    for recorrente in pendentes:
        while recorrente.proximo_lancamento <= hoje:
            db.execute(
                insert(Despesa)
                .values(
                    id_usuario=usuario.id_usuario,
                    id_categoria=recorrente.id_categoria,
                    valor=recorrente.valor,
                    data_despesa=recorrente.proximo_lancamento,
                    estabelecimento=recorrente.estabelecimento,
                    descricao=recorrente.descricao,
                    status_extracao=StatusDespesa.recorrente,
                    id_recorrente=recorrente.id_recorrente,
                )
                .on_conflict_do_nothing(constraint="uq_despesa_recorrente_data")
            )
            recorrente.proximo_lancamento = mes_seguinte(recorrente.proximo_lancamento, recorrente.dia_lancamento)
    db.commit()
