from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DespesaRecorrente, Usuario
from app.routers.categorias import obter_categoria_visivel
from app.schemas import RecorrenteOut, RecorrenteSalvar
from app.security import get_usuario_atual
from app.services.recorrencia import lancar_pendentes, proxima_ocorrencia

router = APIRouter(prefix="/recorrentes", tags=["Despesas recorrentes"])


def _obter(db: Session, usuario: Usuario, id_recorrente: int) -> DespesaRecorrente:
    recorrente = db.get(DespesaRecorrente, id_recorrente)
    if recorrente is None or recorrente.id_usuario != usuario.id_usuario:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Despesa recorrente não encontrada")
    return recorrente


def _texto(valor: str | None) -> str | None:
    return (valor or "").strip() or None


@router.get("", response_model=list[RecorrenteOut])
def listar(usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    lancar_pendentes(db, usuario)
    consulta = (
        select(DespesaRecorrente)
        .where(DespesaRecorrente.id_usuario == usuario.id_usuario)
        .order_by(DespesaRecorrente.ativa.desc(), DespesaRecorrente.dia_lancamento)
    )
    return list(db.scalars(consulta).unique())


@router.post("", response_model=RecorrenteOut, status_code=status.HTTP_201_CREATED)
def criar(dados: RecorrenteSalvar, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    obter_categoria_visivel(db, usuario, dados.id_categoria)
    recorrente = DespesaRecorrente(
        id_usuario=usuario.id_usuario,
        id_categoria=dados.id_categoria,
        valor=dados.valor,
        estabelecimento=_texto(dados.estabelecimento),
        descricao=_texto(dados.descricao),
        dia_lancamento=dados.dia_lancamento,
        proximo_lancamento=proxima_ocorrencia(dados.dia_lancamento, date.today()),
        ativa=dados.ativa,
    )
    db.add(recorrente)
    db.commit()
    lancar_pendentes(db, usuario)  # se o dia escolhido for hoje, já lança
    db.refresh(recorrente)
    return recorrente


@router.put("/{id_recorrente}", response_model=RecorrenteOut)
def editar(
    id_recorrente: int,
    dados: RecorrenteSalvar,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    """As alterações valem para os próximos lançamentos; despesas já lançadas não mudam."""
    recorrente = _obter(db, usuario, id_recorrente)
    obter_categoria_visivel(db, usuario, dados.id_categoria)
    # ao mudar o dia ou reativar não se lançam meses passados
    if dados.dia_lancamento != recorrente.dia_lancamento or (dados.ativa and not recorrente.ativa):
        recorrente.proximo_lancamento = proxima_ocorrencia(dados.dia_lancamento, date.today())
    recorrente.id_categoria = dados.id_categoria
    recorrente.valor = dados.valor
    recorrente.estabelecimento = _texto(dados.estabelecimento)
    recorrente.descricao = _texto(dados.descricao)
    recorrente.dia_lancamento = dados.dia_lancamento
    recorrente.ativa = dados.ativa
    db.commit()
    lancar_pendentes(db, usuario)
    db.refresh(recorrente)
    return recorrente


@router.delete("/{id_recorrente}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(id_recorrente: int, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    """Encerra a recorrência; as despesas já lançadas permanecem no histórico."""
    db.delete(_obter(db, usuario, id_recorrente))
    db.commit()
