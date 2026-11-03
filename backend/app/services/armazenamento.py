"""Armazenamento dos comprovantes em disco.

Fluxo em duas etapas:
1. o arquivo enviado fica em uploads/tmp/<id_upload>.<ext> junto com o resultado
   da extração (<id_upload>.json) até o usuário confirmar os dados;
2. na confirmação ele é movido para uploads/<id_usuario>/<id_upload>.<ext>.
"""
import json
import secrets
import shutil
import time
from pathlib import Path

from app.config import get_settings

EXTENSOES_PERMITIDAS = {"jpg", "jpeg", "png", "pdf"}


def _pasta_tmp() -> Path:
    pasta = get_settings().uploads_path / "tmp"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def extensao_de(nome_arquivo: str) -> str:
    return Path(nome_arquivo).suffix.lower().lstrip(".")


def limpar_temporarios_antigos(horas: int = 24) -> None:
    """Remove uploads que nunca foram confirmados pelo usuário."""
    limite = time.time() - horas * 3600
    for arquivo in _pasta_tmp().iterdir():
        if arquivo.stat().st_mtime < limite:
            arquivo.unlink(missing_ok=True)


def salvar_temporario(conteudo: bytes, extensao: str, id_usuario: int) -> tuple[str, Path]:
    limpar_temporarios_antigos()
    # o id do usuário faz parte do identificador para que um usuário não confirme o upload de outro
    id_upload = f"{id_usuario}_{secrets.token_hex(8)}"
    caminho = _pasta_tmp() / f"{id_upload}.{extensao}"
    caminho.write_bytes(conteudo)
    return id_upload, caminho


def salvar_resultado(id_upload: str, resultado: dict) -> None:
    (_pasta_tmp() / f"{id_upload}.json").write_text(json.dumps(resultado, default=str), encoding="utf-8")


def carregar_temporario(id_upload: str, id_usuario: int) -> tuple[Path, dict] | None:
    if not id_upload.startswith(f"{id_usuario}_") or not id_upload.replace("_", "").isalnum():
        return None
    pasta = _pasta_tmp()
    arquivos = [p for p in pasta.glob(f"{id_upload}.*") if p.suffix != ".json"]
    meta = pasta / f"{id_upload}.json"
    if not arquivos or not meta.exists():
        return None
    return arquivos[0], json.loads(meta.read_text(encoding="utf-8"))


def mover_definitivo(caminho_tmp: Path, id_upload: str, id_usuario: int) -> str:
    """Move o arquivo para a pasta do usuário e devolve o caminho relativo gravado no banco."""
    base = get_settings().uploads_path
    destino_dir = base / str(id_usuario)
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / caminho_tmp.name
    shutil.move(caminho_tmp, destino)
    (_pasta_tmp() / f"{id_upload}.json").unlink(missing_ok=True)
    return destino.relative_to(base).as_posix()


def caminho_absoluto(caminho_relativo: str) -> Path:
    return get_settings().uploads_path / caminho_relativo


def remover(caminho_relativo: str) -> None:
    caminho_absoluto(caminho_relativo).unlink(missing_ok=True)


def remover_arquivos_do_usuario(id_usuario: int) -> None:
    """Apaga os comprovantes do usuário, inclusive os enviados e não confirmados."""
    shutil.rmtree(get_settings().uploads_path / str(id_usuario), ignore_errors=True)
    for arquivo in _pasta_tmp().glob(f"{id_usuario}_*"):
        arquivo.unlink(missing_ok=True)
