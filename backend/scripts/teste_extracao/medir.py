"""Mede acerto e tempo da extração do sistema (app.services.extracao) sobre os comprovantes fictícios.

Uso, na pasta backend, com o Ollama aberto:
    .venv/Scripts/python.exe scripts/teste_extracao/medir.py [pasta_dos_comprovantes]
Grava resultados/resultados.json; a saída do terminal pode ser guardada em resultados/saida.txt.
"""
import json
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import httpx

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1]))  # pasta backend
from app.config import get_settings  # noqa: E402
from app.services.extracao import extrair  # noqa: E402

PASTA = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "comprovantes"
CATEGORIAS = ["Alimentação", "Transporte", "Saúde", "Moradia", "Lazer", "Não categorizado"]
s = get_settings()


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().upper()
    return "".join(c for c in t if c.isalnum())


def vram():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True).stdout
        return int(out.split()[0])
    except Exception:
        return None


gabarito = json.loads((PASTA / "gabarito.json").read_text(encoding="utf-8"))

# descarrega o modelo para medir a primeira leitura (carregamento a frio)
httpx.post(f"{s.ollama_url}/api/generate", json={"model": s.nuextract_modelo, "keep_alive": 0}, timeout=60)
time.sleep(3)
print("VRAM antes:", vram(), "MiB")

resultados = []
for n, g in enumerate(gabarito):
    t0 = time.perf_counter()
    e = extrair(PASTA / g["arquivo"], CATEGORIAS)
    dt = time.perf_counter() - t0
    r = {
        **g,
        "tempo": round(dt, 2),
        "frio": n == 0,
        "status": e.status.value,
        "ok_valor": e.valor is not None and f"{e.valor:.2f}" == g["valor"],
        "ok_data": e.data_despesa is not None and e.data_despesa.isoformat() == g["data"],
        "ok_estab": bool(e.estabelecimento) and (norm(g["estabelecimento"])[:12] in norm(e.estabelecimento)
                                                or norm(e.estabelecimento) in norm(g["estabelecimento"])),
        "ok_cat": e.categoria == g["categoria"],
        "lido": {"valor": str(e.valor), "data": str(e.data_despesa), "estab": e.estabelecimento, "cat": e.categoria},
    }
    resultados.append(r)
    print(json.dumps(r, ensure_ascii=False), flush=True)

print("VRAM com modelo:", vram(), "MiB")
(AQUI / "resultados").mkdir(exist_ok=True)
(AQUI / "resultados" / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")
