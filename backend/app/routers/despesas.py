from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import get_db
from app.models import Comprovante, Despesa, ExtracaoOCR, StatusDespesa, StatusOCR, Usuario
from app.routers.categorias import categorias_visiveis, obter_categoria_visivel
from app.schemas import (
    DadosExtraidos,
    DespesaAtualizar,
    DespesaCriar,
    DespesaDeComprovante,
    DespesaOut,
    ResultadoExtracao,
)
from app.security import get_usuario_atual
from app.services import armazenamento, extracao
from app.services.recorrencia import lancar_pendentes

router = APIRouter(prefix="/despesas", tags=["Despesas"])


def _obter_despesa(db: Session, usuario: Usuario, id_despesa: int) -> Despesa:
    despesa = db.get(Despesa, id_despesa)
    if despesa is None or despesa.id_usuario != usuario.id_usuario:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Despesa não encontrada")
    return despesa


# ------------------------------------------------------------------ consulta
@router.get("", response_model=list[DespesaOut])
def listar(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    id_categoria: int | None = None,
    busca: str | None = Query(default=None, description="Trecho do estabelecimento ou da descrição"),
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    lancar_pendentes(db, usuario)
    consulta = (
        select(Despesa)
        .options(selectinload(Despesa.comprovante))
        .where(Despesa.id_usuario == usuario.id_usuario)
        .order_by(Despesa.data_despesa.desc(), Despesa.data_criacao.desc())
    )
    if data_inicio:
        consulta = consulta.where(Despesa.data_despesa >= data_inicio)
    if data_fim:
        consulta = consulta.where(Despesa.data_despesa <= data_fim)
    if id_categoria:
        consulta = consulta.where(Despesa.id_categoria == id_categoria)
    if busca:
        padrao = f"%{busca}%"
        consulta = consulta.where(Despesa.estabelecimento.ilike(padrao) | Despesa.descricao.ilike(padrao))
    return list(db.scalars(consulta).unique())


@router.get("/{id_despesa}", response_model=DespesaOut)
def detalhar(id_despesa: int, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    return _obter_despesa(db, usuario, id_despesa)


# ------------------------------------------------------- registro manual
@router.post("", response_model=DespesaOut, status_code=status.HTTP_201_CREATED)
def registrar_manual(dados: DespesaCriar, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    obter_categoria_visivel(db, usuario, dados.id_categoria)
    despesa = Despesa(id_usuario=usuario.id_usuario, status_extracao=StatusDespesa.manual, **dados.model_dump())
    db.add(despesa)
    db.commit()
    db.refresh(despesa)
    return despesa


# ------------------------------------------- registro por comprovante (2 etapas)
@router.post("/comprovante/extrair", response_model=ResultadoExtracao)
async def extrair_comprovante(
    arquivo: UploadFile = File(...),
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    """Etapa 1: recebe o comprovante, executa o NuExtract3 e devolve os dados para conferência."""
    extensao = armazenamento.extensao_de(arquivo.filename or "")
    if extensao not in armazenamento.EXTENSOES_PERMITIDAS:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Envie um arquivo JPG, PNG ou PDF")
    conteudo = await arquivo.read()
    limite = get_settings().tamanho_max_upload_mb * 1024 * 1024
    if not conteudo or len(conteudo) > limite:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"O arquivo deve ter até {get_settings().tamanho_max_upload_mb} MB",
        )

    id_upload, caminho = armazenamento.salvar_temporario(conteudo, extensao, usuario.id_usuario)
    categorias = categorias_visiveis(db, usuario)
    resultado = await run_in_threadpool(extracao.extrair, caminho, [c.nome for c in categorias])

    sugerida = next((c.id_categoria for c in categorias if c.nome == resultado.categoria), None)
    dados = DadosExtraidos(
        valor=resultado.valor,
        data_despesa=resultado.data_despesa,
        estabelecimento=resultado.estabelecimento,
        id_categoria_sugerida=sugerida,
    )
    armazenamento.salvar_resultado(
        id_upload,
        {
            "status": resultado.status.value,
            "confianca": str(resultado.confianca),
            "modelo": resultado.modelo,
            "json_bruto": resultado.json_bruto,
            "dados": dados.model_dump(mode="json"),
            "tamanho": len(conteudo),
        },
    )
    mensagem = None
    if resultado.status == StatusOCR.falha_total:
        mensagem = "Não foi possível ler o comprovante. Preencha os dados manualmente."
    elif resultado.status == StatusOCR.falha_parcial:
        mensagem = "Alguns dados não foram encontrados. Confira e complete antes de salvar."
    return ResultadoExtracao(
        id_upload=id_upload, status=resultado.status, confianca=resultado.confianca, dados=dados, mensagem=mensagem
    )


@router.post("/comprovante/confirmar", response_model=DespesaOut, status_code=status.HTTP_201_CREATED)
def confirmar_comprovante(
    dados: DespesaDeComprovante,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    """Etapa 2: grava a despesa com os dados conferidos/corrigidos pelo usuário."""
    temporario = armazenamento.carregar_temporario(dados.id_upload, usuario.id_usuario)
    if temporario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload não encontrado ou expirado; envie o comprovante novamente")
    caminho_tmp, meta = temporario
    obter_categoria_visivel(db, usuario, dados.id_categoria)

    extraidos = DadosExtraidos(**meta["dados"])
    status_ocr = StatusOCR(meta["status"])
    if status_ocr == StatusOCR.falha_total:
        status_despesa = StatusDespesa.falha
    elif (extraidos.valor, extraidos.data_despesa, extraidos.estabelecimento, extraidos.id_categoria_sugerida) == (
        dados.valor,
        dados.data_despesa,
        dados.estabelecimento,
        dados.id_categoria,
    ):
        status_despesa = StatusDespesa.concluida
    else:
        status_despesa = StatusDespesa.corrigida_manualmente

    campos = dados.model_dump(exclude={"id_upload"})
    despesa = Despesa(id_usuario=usuario.id_usuario, status_extracao=status_despesa, **campos)
    db.add(despesa)
    db.flush()

    caminho_relativo = armazenamento.mover_definitivo(caminho_tmp, dados.id_upload, usuario.id_usuario)
    comprovante = Comprovante(
        id_despesa=despesa.id_despesa,
        caminho_arquivo=caminho_relativo,
        tipo_arquivo=caminho_tmp.suffix.lstrip(".").lower(),
        tamanho_arquivo=meta["tamanho"],
    )
    comprovante.extracoes.append(
        ExtracaoOCR(
            id_categoria_sugerida=extraidos.id_categoria_sugerida,
            json_bruto=meta["json_bruto"],
            modelo_utilizado=meta["modelo"],
            confianca=meta["confianca"],
            status=status_ocr,
        )
    )
    despesa.comprovante = comprovante
    try:
        db.commit()
    except Exception:
        db.rollback()
        armazenamento.remover(caminho_relativo)
        raise
    db.refresh(despesa)
    return despesa


@router.get("/{id_despesa}/comprovante", response_class=FileResponse)
def baixar_comprovante(
    id_despesa: int, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)
):
    despesa = _obter_despesa(db, usuario, id_despesa)
    if despesa.comprovante is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Despesa sem comprovante")
    return FileResponse(armazenamento.caminho_absoluto(despesa.comprovante.caminho_arquivo))


# ------------------------------------------------------ edição / exclusão
@router.put("/{id_despesa}", response_model=DespesaOut)
def editar(
    id_despesa: int,
    dados: DespesaAtualizar,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
):
    despesa = _obter_despesa(db, usuario, id_despesa)
    alteracoes = dados.model_dump(exclude_unset=True)
    for campo in ("valor", "data_despesa", "id_categoria"):
        if campo in alteracoes and alteracoes[campo] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"O campo {campo} não pode ser vazio")
    if "id_categoria" in alteracoes:
        obter_categoria_visivel(db, usuario, alteracoes["id_categoria"])
    for campo, valor in alteracoes.items():
        setattr(despesa, campo, valor)
    if alteracoes and despesa.status_extracao == StatusDespesa.concluida:
        despesa.status_extracao = StatusDespesa.corrigida_manualmente
    db.commit()
    db.refresh(despesa)
    return despesa


@router.delete("/{id_despesa}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(id_despesa: int, usuario: Usuario = Depends(get_usuario_atual), db: Session = Depends(get_db)):
    despesa = _obter_despesa(db, usuario, id_despesa)
    caminho = despesa.comprovante.caminho_arquivo if despesa.comprovante else None
    db.delete(despesa)
    db.commit()
    if caminho:
        armazenamento.remover(caminho)
