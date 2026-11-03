from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Categoria, Despesa, DespesaRecorrente, TipoCategoria, Usuario
from app.schemas import CategoriaCriar, CategoriaOut
from app.security import get_usuario_atual

router = APIRouter(prefix="/categorias", tags=["Categorias"])

CATEGORIA_FALLBACK = "Não categorizado"


def categorias_visiveis(db: Session, usuario: Usuario) -> list[Categoria]:
    """Categorias padrão do sistema + personalizadas do usuário."""
    consulta = (
        select(Categoria)
        .where(or_(Categoria.id_usuario.is_(None), Categoria.id_usuario == usuario.id_usuario))
        .order_by(Categoria.tipo, Categoria.nome)
    )
    return list(db.scalars(consulta))


def obter_categoria_visivel(db: Session, usuario: Usuario, id_categoria: int) -> Categoria:
    categoria = db.get(Categoria, id_categoria)
    if categoria is None or categoria.id_usuario not in (None, usuario.id_usuario):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada")
    return categoria


def _obter_personalizada(db: Session, usuario: Usuario, id_categoria: int) -> Categoria:
    categoria = obter_categoria_visivel(db, usuario, id_categoria)
    if categoria.tipo == TipoCategoria.padrao:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Categorias padrão não podem ser alteradas")
    return categoria


def _commit_nome_unico(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma categoria com esse nome")


@router.get("", response_model=list[CategoriaOut])
def listar(usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    return categorias_visiveis(db, usuario)


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar(dados: CategoriaCriar, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    nome = dados.nome.strip()
    if any(c.nome.lower() == nome.lower() for c in categorias_visiveis(db, usuario)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma categoria com esse nome")
    categoria = Categoria(id_usuario=usuario.id_usuario, nome=nome, tipo=TipoCategoria.personalizada)
    db.add(categoria)
    _commit_nome_unico(db)
    return categoria


@router.put("/{id_categoria}", response_model=CategoriaOut)
def editar(
    id_categoria: int,
    dados: CategoriaCriar,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    categoria = _obter_personalizada(db, usuario, id_categoria)
    categoria.nome = dados.nome.strip()
    _commit_nome_unico(db)
    return categoria


@router.delete("/{id_categoria}", status_code=status.HTTP_204_NO_CONTENT)
def remover(id_categoria: int, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    """Remove a categoria; despesas e recorrentes passam para "Não categorizado" e o orçamento dela é excluído."""
    categoria = _obter_personalizada(db, usuario, id_categoria)
    fallback = db.scalar(
        select(Categoria).where(Categoria.id_usuario.is_(None), Categoria.nome == CATEGORIA_FALLBACK)
    )
    if fallback is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f'Categoria "{CATEGORIA_FALLBACK}" ausente')
    db.execute(
        update(Despesa).where(Despesa.id_categoria == categoria.id_categoria).values(id_categoria=fallback.id_categoria)
    )
    db.execute(
        update(DespesaRecorrente)
        .where(DespesaRecorrente.id_categoria == categoria.id_categoria)
        .values(id_categoria=fallback.id_categoria)
    )
    db.delete(categoria)
    db.commit()
