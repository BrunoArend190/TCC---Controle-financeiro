from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Categoria, Despesa, Usuario
from app.schemas import Comparativo, FraseComparativo, Resumo, TotalPorCategoria, TotalPorMes
from app.security import get_usuario_atual
from app.services.recorrencia import lancar_pendentes

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/resumo", response_model=Resumo)
def resumo(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    lancar_pendentes(db, usuario)
    filtros = [Despesa.id_usuario == usuario.id_usuario]
    if data_inicio:
        filtros.append(Despesa.data_despesa >= data_inicio)
    if data_fim:
        filtros.append(Despesa.data_despesa <= data_fim)

    total, quantidade = db.execute(
        select(func.coalesce(func.sum(Despesa.valor), 0), func.count()).where(*filtros)
    ).one()

    por_categoria = db.execute(
        select(Categoria.nome, func.sum(Despesa.valor).label("total"))
        .join(Categoria, Categoria.id_categoria == Despesa.id_categoria)
        .where(*filtros)
        .group_by(Categoria.nome)
        .order_by(func.sum(Despesa.valor).desc())
    ).all()

    mes = func.to_char(Despesa.data_despesa, "YYYY-MM")
    por_mes = db.execute(
        select(mes.label("mes"), func.sum(Despesa.valor).label("total")).where(*filtros).group_by(mes).order_by(mes)
    ).all()

    return Resumo(
        total=Decimal(total),
        quantidade=quantidade,
        por_categoria=[TotalPorCategoria(categoria=nome, total=t) for nome, t in por_categoria],
        por_mes=[TotalPorMes(mes=m, total=t) for m, t in por_mes],
    )


VARIACAO_MINIMA = 5  # variações menores que 5% não geram frase
MAX_FRASES = 5
MES_PASSADO = "no mesmo período do mês passado"


def _moeda(valor: Decimal) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _variacao(atual: Decimal, anterior: Decimal) -> tuple[int, str]:
    percentual = round(abs(atual - anterior) / anterior * 100)
    return percentual, "a mais" if atual > anterior else "a menos"


def _totais_por_categoria(db: Session, usuario: Usuario, inicio: date, fim: date) -> dict[str, Decimal]:
    linhas = db.execute(
        select(Categoria.nome, func.sum(Despesa.valor))
        .join(Categoria, Categoria.id_categoria == Despesa.id_categoria)
        .where(Despesa.id_usuario == usuario.id_usuario, Despesa.data_despesa.between(inicio, fim))
        .group_by(Categoria.nome)
    ).all()
    return {nome: total for nome, total in linhas}


@router.get("/comparativo", response_model=Comparativo)
def comparativo(usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    """Compara o mês atual com o mesmo período do mês anterior, para não penalizar o mês em andamento."""
    lancar_pendentes(db, usuario)
    hoje = date.today()
    ano, mes = (hoje.year - 1, 12) if hoje.month == 1 else (hoje.year, hoje.month - 1)
    fim_anterior = date(ano, mes, min(hoje.day, monthrange(ano, mes)[1]))
    atuais = _totais_por_categoria(db, usuario, hoje.replace(day=1), hoje)
    anteriores = _totais_por_categoria(db, usuario, date(ano, mes, 1), fim_anterior)
    total_atual = sum(atuais.values(), Decimal(0))
    total_anterior = sum(anteriores.values(), Decimal(0))

    frases: list[FraseComparativo] = []
    if total_anterior and total_atual:
        percentual, sentido = _variacao(total_atual, total_anterior)
        if percentual >= VARIACAO_MINIMA:
            frases.append(
                FraseComparativo(
                    tipo="aumento" if total_atual > total_anterior else "queda",
                    texto=f"No total, você gastou {percentual}% {sentido} do que {MES_PASSADO}.",
                )
            )

    # as categorias com maior diferença em reais aparecem primeiro
    categorias = sorted(
        atuais.keys() | anteriores.keys(),
        key=lambda c: abs(atuais.get(c, Decimal(0)) - anteriores.get(c, Decimal(0))),
        reverse=True,
    )
    for categoria in categorias:
        atual = atuais.get(categoria, Decimal(0))
        anterior = anteriores.get(categoria, Decimal(0))
        if not anterior:
            frases.append(
                FraseComparativo(
                    tipo="aumento",
                    texto=f"Você gastou {_moeda(atual)} em {categoria}, sem gastos nessa categoria {MES_PASSADO}.",
                )
            )
        elif not atual:
            frases.append(
                FraseComparativo(
                    tipo="queda",
                    texto=f"Você ainda não gastou em {categoria} este mês; {MES_PASSADO} foram {_moeda(anterior)}.",
                )
            )
        else:
            percentual, sentido = _variacao(atual, anterior)
            if percentual >= VARIACAO_MINIMA:
                frases.append(
                    FraseComparativo(
                        tipo="aumento" if atual > anterior else "queda",
                        texto=f"Você gastou {percentual}% {sentido} em {categoria} do que {MES_PASSADO}.",
                    )
                )

    return Comparativo(total_atual=total_atual, total_anterior=total_anterior, frases=frases[:MAX_FRASES])
