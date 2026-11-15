"""Extração de dados de comprovantes com o NuExtract3 servido pelo Ollama.

O NuExtract recebe um *template* JSON (mesma estrutura da saída esperada) e a
imagem do comprovante, e devolve o JSON preenchido (campos não encontrados = null).
"""
import base64
import io
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import httpx
from PIL import Image

from app.config import get_settings
from app.models import StatusOCR

log = logging.getLogger(__name__)

LADO_MAX_PX = 1600  # imagens maiores são reduzidas para acelerar a inferência


@dataclass
class Extracao:
    status: StatusOCR
    confianca: Decimal
    valor: Decimal | None = None
    data_despesa: date | None = None
    estabelecimento: str | None = None
    categoria: str | None = None
    json_bruto: dict | None = None
    mensagem: str | None = None
    modelo: str = field(default_factory=lambda: get_settings().nuextract_modelo)


def montar_template(nomes_categorias: list[str]) -> dict:
    return {
        "valor_total": "number",
        "data": "date",
        "estabelecimento": "verbatim-string",
        # enum: o modelo escolhe uma das categorias existentes do usuário
        "categoria": nomes_categorias,
    }


def imagem_base64(caminho: Path) -> str:
    """Converte o comprovante (imagem ou 1ª página do PDF) em PNG base64."""
    if caminho.suffix.lower() == ".pdf":
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(caminho))
        try:
            imagem = pdf[0].render(scale=2).to_pil()
        finally:
            pdf.close()
    else:
        imagem = Image.open(caminho)
    imagem = imagem.convert("RGB")
    imagem.thumbnail((LADO_MAX_PX, LADO_MAX_PX))
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def _parse_json(texto: str) -> dict:
    texto = texto.strip()
    bloco = re.search(r"\{.*\}", texto, re.DOTALL)  # tolera ```json ... ``` ao redor
    return json.loads(bloco.group(0) if bloco else texto)


def _parse_valor(bruto) -> Decimal | None:
    if bruto is None:
        return None
    if isinstance(bruto, str):  # ex.: "1.234,56" ou "R$ 12,90"
        bruto = re.sub(r"[^\d,.-]", "", bruto)
        if "," in bruto:
            bruto = bruto.replace(".", "").replace(",", ".")
    try:
        valor = Decimal(str(bruto)).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None
    return valor if valor > 0 else None


def _parse_data(bruto) -> date | None:
    if not bruto:
        return None
    try:
        return date.fromisoformat(str(bruto)[:10])
    except ValueError:
        return None


def extrair(caminho: Path, nomes_categorias: list[str]) -> Extracao:
    settings = get_settings()
    template = montar_template(nomes_categorias)
    try:
        corpo = {
            "model": settings.nuextract_modelo,
            "messages": [
                {"role": "template", "content": json.dumps(template, ensure_ascii=False)},
                {"role": "user", "content": "", "images": [imagem_base64(caminho)]},
            ],
            "stream": False,
            "options": {"temperature": 0},
        }
        resposta = httpx.post(
            f"{settings.ollama_url}/api/chat", json=corpo, timeout=settings.nuextract_timeout_segundos
        )
        resposta.raise_for_status()
        bruto = _parse_json(resposta.json()["message"]["content"])
    except Exception as exc:  # modelo indisponível, timeout, JSON inválido...
        log.exception("Falha na extração do comprovante %s", caminho.name)
        return Extracao(status=StatusOCR.falha_total, confianca=Decimal("0"), mensagem=str(exc))

    categoria = bruto.get("categoria")
    extracao = Extracao(
        status=StatusOCR.sucesso,
        confianca=Decimal("0"),
        valor=_parse_valor(bruto.get("valor_total")),
        data_despesa=_parse_data(bruto.get("data")),
        estabelecimento=(bruto.get("estabelecimento") or None),
        categoria=categoria if categoria in nomes_categorias else None,
        json_bruto=bruto,
    )
    # "confiança" = proporção de campos do template preenchidos com valor válido
    preenchidos = [extracao.valor, extracao.data_despesa, extracao.estabelecimento, extracao.categoria]
    extracao.confianca = Decimal(sum(v is not None for v in preenchidos)) / len(preenchidos)
    # a categoria não conta: é uma sugestão, não um dado lido do documento
    if extracao.valor is None and extracao.data_despesa is None and extracao.estabelecimento is None:
        extracao.status = StatusOCR.falha_total
    elif None in (extracao.valor, extracao.data_despesa):
        extracao.status = StatusOCR.falha_parcial
    return extracao


def ollama_disponivel() -> bool:
    try:
        httpx.get(f"{get_settings().ollama_url}/api/tags", timeout=3).raise_for_status()
        return True
    except httpx.HTTPError:
        return False
