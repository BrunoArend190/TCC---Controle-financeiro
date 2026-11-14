"""Gera comprovantes fictícios (imagem limpa, foto simulada e baixa resolução) e o gabarito.

Uso: python gerar_comprovantes.py [pasta]   (padrão: comprovantes/, ao lado deste arquivo)
Usa fontes do Windows; a semente fixa faz as imagens saírem sempre iguais.
"""
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SAIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "comprovantes"
SAIDA.mkdir(parents=True, exist_ok=True)
random.seed(42)

FONTES = ["C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/lucon.ttf"]

# (estabelecimento, cnpj, cidade, itens, data impressa, data ISO, categoria esperada)
COMPROVANTES = [
    ("SUPERMERCADO BOM PRECO LTDA", "12.345.678/0001-90", "Santa Catarina - SC",
     [("ARROZ TIPO 1 5KG", 27.90), ("FEIJAO PRETO 1KG", 8.49), ("LEITE INTEGRAL 1L x6", 35.94), ("CAFE 500G", 19.90)],
     "03/11/2026 18:42:10", "2026-11-03", "Alimentação"),
    ("FARMACIA SAUDE TOTAL", "23.456.789/0001-01", "Pinhalzinho - SC",
     [("DIPIRONA 500MG 10CP", 6.99), ("PROTETOR SOLAR FPS50", 54.90), ("VITAMINA C 1G", 21.50)],
     "28/10/2026 10:15", "2026-10-28", "Saúde"),
    ("AUTO POSTO RODOVIA BR-282", "34.567.890/0001-12", "Maravilha - SC",
     [("GASOLINA COMUM 32,150 L x 6,29", 202.22)],
     "05/11/26 07:58", "2026-11-05", "Transporte"),
    ("RESTAURANTE SABOR CASEIRO ME", "45.678.901/0001-23", "Chapeco - SC",
     [("BUFFET KG 0,612 x 69,90", 42.78), ("REFRIGERANTE LATA", 6.50), ("SOBREMESA", 9.00)],
     "10/11/2026 12:31:44", "2026-11-10", "Alimentação"),
    ("PADARIA PAO DOURADO", "56.789.012/0001-34", "Pinhalzinho - SC",
     [("PAO FRANCES KG 0,450", 7.65), ("CUCA DE BANANA", 18.00), ("QUEIJO COLONIAL 0,320", 19.17)],
     "08/11/2026 08:05", "2026-11-08", "Alimentação"),
    ("CINE ARTE SHOPPING", "67.890.123/0001-45", "Chapeco - SC",
     [("INGRESSO INTEIRA 2D", 32.00), ("INGRESSO MEIA 2D", 16.00), ("COMBO PIPOCA M", 38.90)],
     "01/11/2026 19:40", "2026-11-01", "Lazer"),
    ("CELESC DISTRIBUICAO S.A.", "08.336.783/0001-90", "Florianopolis - SC",
     [("CONSUMO ENERGIA 212 KWH", 168.43), ("CONTRIB. ILUM. PUBLICA", 14.20)],
     "20/10/2026", "2026-10-20", "Moradia"),
    ("CLINICA ODONTO SORRISO", "78.901.234/0001-56", "Pinhalzinho - SC",
     [("CONSULTA DE AVALIACAO", 150.00), ("LIMPEZA E PROFILAXIA", 180.00)],
     "12/11/2026 14:20", "2026-11-12", "Saúde"),
]


def desenhar(i, estab, cnpj, cidade, itens, data_txt):
    fonte_nome = FONTES[i % len(FONTES)]
    f = ImageFont.truetype(fonte_nome, 26)
    fb = ImageFont.truetype(fonte_nome, 30)
    largura, linhas = 720, []
    linhas += [(estab, fb), (f"CNPJ: {cnpj}", f), (cidade, f), ("-" * 44, f),
               ("CUPOM FISCAL ELETRONICO - SAT" if i % 2 == 0 else "DOCUMENTO AUXILIAR DA NFC-e", f), ("-" * 44, f)]
    total = 0.0
    for nome, valor in itens:
        total += valor
        linhas.append((nome, f))
        linhas.append((f"{'':<28}R$ {valor:>8.2f}".replace(".", ","), f))
    linhas += [("-" * 44, f), (f"TOTAL R$ {total:>.2f}".replace(".", ","), fb),
               (f"FORMA PAGTO: {'CARTAO DEBITO' if i % 3 else 'PIX'}", f), ("-" * 44, f),
               (f"Emissao: {data_txt}", f), ("Consumidor nao identificado", f), ("Obrigado pela preferencia!", f)]
    altura = 60 + 40 * len(linhas)
    img = Image.new("RGB", (largura, altura), "white")
    d = ImageDraw.Draw(img)
    y = 30
    for texto, fonte in linhas:
        d.text((30, y), texto, fill="black", font=fonte)
        y += 40
    return img, round(total, 2)


def foto(img):
    """Simula uma foto de celular: fundo, rotação, desfoque, sombra e ruído."""
    fundo = Image.new("RGB", (img.width + 260, img.height + 260), (120, 105, 90))
    fundo.paste(img, (130, 130))
    fundo = fundo.rotate(random.uniform(-6, 6), resample=Image.BICUBIC, expand=True, fillcolor=(120, 105, 90))
    sombra = Image.linear_gradient("L").resize(fundo.size).point(lambda v: 255 - v // 3)
    fundo = Image.composite(fundo, Image.new("RGB", fundo.size, (40, 40, 40)), sombra)
    fundo = fundo.filter(ImageFilter.GaussianBlur(1.4))
    ruido = Image.effect_noise(fundo.size, 18).convert("RGB")
    return Image.blend(fundo, ruido, 0.12)


def baixa(img):
    return img.resize((int(img.width * 0.35), int(img.height * 0.35)), Image.BILINEAR)


gabarito = []
for i, (estab, cnpj, cidade, itens, data_txt, data_iso, cat) in enumerate(COMPROVANTES, 1):
    img, total = desenhar(i, estab, cnpj, cidade, itens, data_txt)
    for cond, fn in (("limpo", lambda x: x), ("foto", foto), ("baixa_resolucao", baixa)):
        nome = f"c{i:02d}_{cond}.png"
        fn(img).save(SAIDA / nome)
        gabarito.append({"arquivo": nome, "condicao": cond, "valor": f"{total:.2f}", "data": data_iso,
                         "estabelecimento": estab, "categoria": cat})
(SAIDA / "gabarito.json").write_text(json.dumps(gabarito, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(gabarito), "imagens geradas")
