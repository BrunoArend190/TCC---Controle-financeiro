from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Despesa, Orcamento, Usuario
from app.routers.categorias import obter_categoria_visivel
from app.schemas import OrcamentoOut, OrcamentoSalvar
from app.security import get_usuario_atual
from app.services.recorrencia import lancar_pendentes

router = APIRouter(prefix="/orcamentos", tags=["Orçamentos"])

PERCENTUAL_ALERTA = 80  # a partir daqui o orçamento fica em alerta (RN17)


def _situacao(percentual: float) -> str:
    if percentual > 100:
        return "excedido"
    return "alerta" if percentual >= PERCENTUAL_ALERTA else "ok"


@router.get("", response_model=list[OrcamentoOut])
def listar(
    mes: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="AAAA-MM; padrão: mês atual"),
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    """Orçamentos do usuário com o gasto do mês; os mais comprometidos aparecem primeiro."""
    lancar_pendentes(db, usuario)
    hoje = date.today()
    ano, numero_mes = map(int, mes.split("-")) if mes else (hoje.year, hoje.month)
    inicio, fim = date(ano, numero_mes, 1), date(ano, numero_mes, monthrange(ano, numero_mes)[1])

    gastos = dict(
        db.execute(
            select(Despesa.id_categoria, func.sum(Despesa.valor))
            .where(Despesa.id_usuario == usuario.id_usuario, Despesa.data_despesa.between(inicio, fim))
            .group_by(Despesa.id_categoria)
        ).all()
    )
    orcamentos = db.scalars(select(Orcamento).where(Orcamento.id_usuario == usuario.id_usuario)).unique()

    resultado = []
    for orcamento in orcamentos:
        gasto = gastos.get(orcamento.id_categoria, Decimal(0))
        percentual = round(float(gasto / orcamento.valor_limite * 100), 1)
        resultado.append(
            OrcamentoOut(
                id_orcamento=orcamento.id_orcamento,
                categoria=orcamento.categoria,
                valor_limite=orcamento.valor_limite,
                gasto=gasto,
                restante=orcamento.valor_limite - gasto,
                percentual=percentual,
                situacao=_situacao(percentual),
            )
        )
    return sorted(resultado, key=lambda o: o.percentual, reverse=True)


@router.put("/{id_categoria}", status_code=status.HTTP_204_NO_CONTENT)
def definir(
    id_categoria: int,
    dados: OrcamentoSalvar,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    """Define o limite mensal da categoria (cada categoria tem no máximo um orçamento)."""
    obter_categoria_visivel(db, usuario, id_categoria)
    orcamento = db.scalar(
        select(Orcamento).where(Orcamento.id_usuario == usuario.id_usuario, Orcamento.id_categoria == id_categoria)
    )
    if orcamento:
        orcamento.valor_limite = dados.valor_limite
    else:
        db.add(Orcamento(id_usuario=usuario.id_usuario, id_categoria=id_categoria, valor_limite=dados.valor_limite))
    db.commit()


@router.delete("/{id_categoria}", status_code=status.HTTP_204_NO_CONTENT)
def remover(id_categoria: int, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    orcamento = db.scalar(
        select(Orcamento).where(Orcamento.id_usuario == usuario.id_usuario, Orcamento.id_categoria == id_categoria)
    )
    if orcamento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Orçamento não encontrado")
    db.delete(orcamento)
    db.commit()
