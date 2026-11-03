"""Testa orçamentos, comparativos, despesas recorrentes, perfil e exclusão de conta.

Uso (com a API rodando em localhost:8000, na pasta backend):
    .venv/Scripts/python.exe scripts/teste_novidades.py
Cria um usuário descartável e o exclui ao final pela própria API.
"""
import secrets
import sys
from calendar import monthrange
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402
from app.services.recorrencia import mes_seguinte, proxima_ocorrencia  # noqa: E402

API = "http://localhost:8000"
falhas = 0


def checar(descricao, condicao, detalhe=""):
    global falhas
    print(f"[{'OK ' if condicao else 'ERRO'}] {descricao}" + (f"  -> {detalhe}" if not condicao else ""))
    falhas += not condicao


def mes_anterior(d: date) -> date:
    ano, mes = (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)
    return date(ano, mes, min(d.day, monthrange(ano, mes)[1]))


def testar_datas():
    checar("dia 31 em fevereiro vira o último dia", proxima_ocorrencia(31, date(2027, 2, 10)) == date(2027, 2, 28))
    checar("ano bissexto", proxima_ocorrencia(31, date(2028, 2, 1)) == date(2028, 2, 29))
    checar("dia já passado vai para o mês seguinte", proxima_ocorrencia(5, date(2026, 11, 20)) == date(2026, 12, 5))
    checar("dia de hoje conta como próxima ocorrência", proxima_ocorrencia(20, date(2026, 11, 20)) == date(2026, 11, 20))
    checar("depois de fevereiro volta ao dia 31", mes_seguinte(date(2027, 2, 28), 31) == date(2027, 3, 31))
    checar("virada de ano", mes_seguinte(date(2026, 12, 15), 15) == date(2027, 1, 15))


def main():
    testar_datas()
    c = httpx.Client(base_url=API, timeout=60)
    email = f"teste_{secrets.token_hex(4)}@exemplo.com"
    senha = secrets.token_urlsafe(12)
    assert c.post("/auth/cadastro", json={"nome": "Teste Novidades", "email": email, "senha": senha}).status_code == 201
    c.headers["Authorization"] = "Bearer " + c.post("/auth/login", data={"username": email, "password": senha}).json()["access_token"]
    id_usuario = c.get("/auth/me").json()["id_usuario"]
    cats = {x["nome"]: x["id_categoria"] for x in c.get("/categorias").json()}
    hoje = date.today()

    # ---------------------------------------------------------- despesas recorrentes
    base = {"valor": "100.00", "id_categoria": cats["Moradia"], "estabelecimento": "Aluguel", "dia_lancamento": hoje.day}
    r = c.post("/recorrentes", json=base)
    checar("criar recorrente com dia de hoje", r.status_code == 201, r.text)
    rec = r.json()
    checar("próximo lançamento vai para o mês seguinte", rec["proximo_lancamento"] == str(mes_seguinte(hoje, hoje.day)), rec)
    despesas = c.get("/despesas").json()
    checar("lançou a despesa de hoje com origem recorrente",
           len(despesas) == 1 and despesas[0]["status_extracao"] == "recorrente" and despesas[0]["data_despesa"] == str(hoje), despesas)
    checar("consultar de novo não duplica", len(c.get("/despesas").json()) == 1)
    with ThreadPoolExecutor(6) as ex:
        codigos = list(ex.map(lambda _: c.get("/relatorios/resumo").status_code, range(6)))
    checar("chamadas simultâneas não falham", all(x == 200 for x in codigos), codigos)
    checar("chamadas simultâneas não duplicam", len(c.get("/despesas").json()) == 1)

    id_lancada = despesas[0]["id_despesa"]
    checar("excluir a despesa lançada", c.delete(f"/despesas/{id_lancada}").status_code == 204)
    checar("despesa excluída não é recriada", len(c.get("/despesas").json()) == 0)

    amanha = hoje + timedelta(days=1)
    dia_futuro = amanha.day if amanha.month == hoje.month else 1
    r = c.post("/recorrentes", json={**base, "dia_lancamento": dia_futuro, "estabelecimento": "Internet", "valor": "99.90"})
    checar("dia futuro não lança agora", r.status_code == 201 and len(c.get("/despesas").json()) == 0, r.text)
    id_internet = r.json()["id_recorrente"]
    checar("dia inválido 422", c.post("/recorrentes", json={**base, "dia_lancamento": 32}).status_code == 422)
    checar("valor inválido 422", c.post("/recorrentes", json={**base, "valor": "0"}).status_code == 422)
    checar("categoria inexistente 404", c.post("/recorrentes", json={**base, "id_categoria": 999999}).status_code == 404)

    # pausar e reativar: meses parados não são lançados retroativamente
    pausa = {**base, "dia_lancamento": dia_futuro, "estabelecimento": "Internet", "valor": "120.00", "ativa": False}
    r = c.put(f"/recorrentes/{id_internet}", json=pausa)
    checar("pausar e alterar valor", r.status_code == 200 and r.json()["ativa"] is False and r.json()["valor"] == "120.00", r.text)
    r = c.put(f"/recorrentes/{id_internet}", json={**pausa, "ativa": True})
    checar("reativar calcula a próxima data a partir de hoje", r.json()["proximo_lancamento"] == str(proxima_ocorrencia(dia_futuro, hoje)), r.text)
    checar("excluir recorrente", c.delete(f"/recorrentes/{id_internet}").status_code == 204)
    checar("recorrente excluída some da lista", id_internet not in [x["id_recorrente"] for x in c.get("/recorrentes").json()])

    # histórico e isolamento entre usuários
    c2 = httpx.Client(base_url=API, timeout=60)
    email2 = f"teste_{secrets.token_hex(4)}@exemplo.com"
    c2.post("/auth/cadastro", json={"nome": "Outro", "email": email2, "senha": senha})
    c2.headers["Authorization"] = "Bearer " + c2.post("/auth/login", data={"username": email2, "password": senha}).json()["access_token"]
    checar("outro usuário não edita a recorrente", c2.put(f"/recorrentes/{rec['id_recorrente']}", json=base).status_code == 404)
    checar("outro usuário não exclui a recorrente", c2.delete(f"/recorrentes/{rec['id_recorrente']}").status_code == 404)

    # ---------------------------------------------------------- orçamentos
    alim = cats["Alimentação"]
    despesa = {"data_despesa": str(hoje), "estabelecimento": "Mercado"}
    checar("definir orçamento", c.put(f"/orcamentos/{alim}", json={"valor_limite": "100.00"}).status_code == 204)
    checar("limite zero 422", c.put(f"/orcamentos/{alim}", json={"valor_limite": "0"}).status_code == 422)
    checar("categoria inexistente 404", c.put("/orcamentos/999999", json={"valor_limite": "10"}).status_code == 404)
    o = c.get("/orcamentos").json()
    checar("sem gastos: situação ok", o[0]["situacao"] == "ok" and o[0]["gasto"] == "0" or float(o[0]["gasto"]) == 0, o)
    c.post("/despesas", json={**despesa, "valor": "79.00", "id_categoria": alim})
    checar("79%: ainda ok", c.get("/orcamentos").json()[0]["situacao"] == "ok")
    c.post("/despesas", json={**despesa, "valor": "1.00", "id_categoria": alim})
    o = c.get("/orcamentos").json()[0]
    checar("80%: alerta", o["situacao"] == "alerta" and o["percentual"] == 80.0, o)
    c.post("/despesas", json={**despesa, "valor": "20.00", "id_categoria": alim})
    o = c.get("/orcamentos").json()[0]
    checar("100%: alerta, não excedido", o["situacao"] == "alerta" and float(o["restante"]) == 0, o)
    c.post("/despesas", json={**despesa, "valor": "50.00", "id_categoria": alim})
    o = c.get("/orcamentos").json()[0]
    checar("150%: excedido e restante negativo", o["situacao"] == "excedido" and float(o["restante"]) == -50, o)
    mes_passado = mes_anterior(hoje).strftime("%Y-%m")
    o = c.get("/orcamentos", params={"mes": mes_passado}).json()[0]
    checar("consulta de outro mês não soma este mês", float(o["gasto"]) == 0, o)
    checar("mês inválido 422", c.get("/orcamentos", params={"mes": "2026-13"}).status_code == 422)
    checar("atualizar limite não duplica",
           c.put(f"/orcamentos/{alim}", json={"valor_limite": "500.00"}).status_code == 204 and len(c.get("/orcamentos").json()) == 1)
    checar("orçamentos são isolados por usuário", c2.get("/orcamentos").json() == [])

    # remover categoria personalizada: despesas/recorrentes vão para "Não categorizado" e o orçamento some
    id_acad = c.post("/categorias", json={"nome": "Academia"}).json()["id_categoria"]
    c.put(f"/orcamentos/{id_acad}", json={"valor_limite": "90"})
    id_rec_acad = c.post("/recorrentes", json={**base, "id_categoria": id_acad, "dia_lancamento": dia_futuro}).json()["id_recorrente"]
    checar("remover categoria com orçamento e recorrente", c.delete(f"/categorias/{id_acad}").status_code == 204)
    checar("orçamento da categoria removida some", id_acad not in [x["categoria"]["id_categoria"] for x in c.get("/orcamentos").json()])
    rec_acad = next(x for x in c.get("/recorrentes").json() if x["id_recorrente"] == id_rec_acad)
    checar("recorrente vai para Não categorizado", rec_acad["categoria"]["nome"] == "Não categorizado", rec_acad)
    id_alheia = c2.post("/categorias", json={"nome": "Privada"}).json()["id_categoria"]
    checar("orçamento em categoria de outro usuário 404", c.put(f"/orcamentos/{id_alheia}", json={"valor_limite": "9"}).status_code == 404)

    # ---------------------------------------------------------- comparativos (no usuário 2, sem outros dados)
    checar("sem dados: nenhuma frase", c2.get("/relatorios/comparativo").json()["frases"] == [])
    anterior = str(mes_anterior(hoje))
    novo = {"data_despesa": str(hoje)}
    velho = {"data_despesa": anterior}
    c2.post("/despesas", json={**velho, "valor": "100.00", "id_categoria": cats["Alimentação"]})
    c2.post("/despesas", json={**novo, "valor": "120.00", "id_categoria": cats["Alimentação"]})
    c2.post("/despesas", json={**velho, "valor": "50.00", "id_categoria": cats["Transporte"]})
    c2.post("/despesas", json={**novo, "valor": "25.00", "id_categoria": cats["Transporte"]})
    c2.post("/despesas", json={**velho, "valor": "10.00", "id_categoria": cats["Lazer"]})
    c2.post("/despesas", json={**novo, "valor": "30.00", "id_categoria": cats["Saúde"]})
    c2.post("/despesas", json={**velho, "valor": "200.00", "id_categoria": cats["Moradia"]})
    c2.post("/despesas", json={**novo, "valor": "202.00", "id_categoria": cats["Moradia"]})
    r = c2.get("/relatorios/comparativo").json()
    textos = " | ".join(f["texto"] for f in r["frases"])
    print("      frases:", textos)
    checar("totais do período", float(r["total_atual"]) == 377 and float(r["total_anterior"]) == 360, r)
    checar("aumento em %", any("20% a mais em Alimentação" in f["texto"] and f["tipo"] == "aumento" for f in r["frases"]), textos)
    checar("queda em %", any("50% a menos em Transporte" in f["texto"] and f["tipo"] == "queda" for f in r["frases"]), textos)
    checar("categoria nova", any("R$ 30,00 em Saúde" in f["texto"] for f in r["frases"]), textos)
    checar("categoria sem gastos este mês", any("R$ 10,00" in f["texto"] and "Lazer" in f["texto"] for f in r["frases"]), textos)
    checar("variação pequena não gera frase", "Moradia" not in textos, textos)

    # ---------------------------------------------------------- perfil
    r = c.put("/auth/me", json={"nome": "  Nome Novo ", "email": email.upper()})
    checar("atualizar perfil", r.status_code == 200 and r.json()["nome"] == "Nome Novo" and r.json()["email"] == email, r.text)
    checar("e-mail de outro usuário 409", c.put("/auth/me", json={"nome": "X Y", "email": email2}).status_code == 409)
    checar("e-mail inválido 422", c.put("/auth/me", json={"nome": "X Y", "email": "nao-e-email"}).status_code == 422)
    nova = secrets.token_urlsafe(12)
    r = c.put("/auth/me/senha", json={"senha_atual": "errada-errada", "nova_senha": nova})
    checar("senha atual errada 400 (mantém a sessão)", r.status_code == 400, r.text)
    checar("nova senha curta 422", c.put("/auth/me/senha", json={"senha_atual": senha, "nova_senha": "curta"}).status_code == 422)
    checar("alterar senha", c.put("/auth/me/senha", json={"senha_atual": senha, "nova_senha": nova}).status_code == 204)
    checar("senha antiga não entra mais", httpx.post(f"{API}/auth/login", data={"username": email, "password": senha}).status_code == 401)
    checar("senha nova entra", httpx.post(f"{API}/auth/login", data={"username": email, "password": nova}).status_code == 200)

    # ---------------------------------------------------------- exclusão de conta
    uploads = get_settings().uploads_path
    pasta = uploads / str(id_usuario)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "comprovante.jpg").write_bytes(b"x")
    temporario = uploads / "tmp" / f"{id_usuario}_abc.jpg"
    temporario.parent.mkdir(parents=True, exist_ok=True)
    temporario.write_bytes(b"x")
    checar("senha errada não exclui (400)", c.post("/auth/me/excluir", json={"senha": "errada-errada"}).status_code == 400)
    checar("excluir conta", c.post("/auth/me/excluir", json={"senha": nova}).status_code == 204)
    checar("token não vale mais", c.get("/auth/me").status_code == 401)
    checar("login não funciona mais", httpx.post(f"{API}/auth/login", data={"username": email, "password": nova}).status_code == 401)
    checar("comprovantes apagados", not pasta.exists() and not temporario.exists())
    checar("excluir conta do usuário 2", c2.post("/auth/me/excluir", json={"senha": senha}).status_code == 204)

    print(f"\n{'TODOS OS TESTES PASSARAM' if falhas == 0 else f'{falhas} FALHA(S)'}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
