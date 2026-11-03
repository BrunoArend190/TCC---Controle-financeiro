from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.schemas import ContaExcluir, SenhaAlterar, Token, UsuarioAtualizar, UsuarioCriar, UsuarioOut
from app.security import criar_token, gerar_hash_senha, get_usuario_atual, verificar_senha
from app.services import armazenamento

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/cadastro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: UsuarioCriar, db: Session = Depends(get_db)):
    email = dados.email.lower()
    if db.scalar(select(Usuario).where(func.lower(Usuario.email) == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    usuario = Usuario(nome=dados.nome.strip(), email=email, senha_hash=gerar_hash_senha(dados.senha))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Autentica com e-mail (campo `username`) e senha; devolve um token JWT."""
    usuario = db.scalar(select(Usuario).where(func.lower(Usuario.email) == form.username.lower()))
    if usuario is None or not verificar_senha(form.password, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha incorretos")
    return Token(access_token=criar_token(usuario.id_usuario))


@router.get("/me", response_model=UsuarioOut)
def usuario_logado(usuario: Usuario = Depends(get_usuario_atual)):
    return usuario


def _conferir_senha(senha: str, usuario: Usuario, mensagem: str) -> None:
    # 400 e não 401: a sessão continua válida, só a senha digitada está errada
    if not verificar_senha(senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, mensagem)


@router.put("/me", response_model=UsuarioOut)
def atualizar_perfil(
    dados: UsuarioAtualizar, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)
):
    email = dados.email.lower()
    outro = db.scalar(select(Usuario).where(func.lower(Usuario.email) == email, Usuario.id_usuario != usuario.id_usuario))
    if outro:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    usuario.nome = dados.nome.strip()
    usuario.email = email
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    return usuario


@router.put("/me/senha", status_code=status.HTTP_204_NO_CONTENT)
def alterar_senha(dados: SenhaAlterar, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    _conferir_senha(dados.senha_atual, usuario, "Senha atual incorreta")
    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    db.commit()


@router.post("/me/excluir", status_code=status.HTTP_204_NO_CONTENT)
def excluir_conta(dados: ContaExcluir, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    """Exclui a conta, todos os dados do usuário (ON DELETE CASCADE) e seus comprovantes (RN15)."""
    _conferir_senha(dados.senha, usuario, "Senha incorreta")
    id_usuario = usuario.id_usuario
    db.delete(usuario)
    db.commit()
    armazenamento.remover_arquivos_do_usuario(id_usuario)
