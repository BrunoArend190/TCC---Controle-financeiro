"""Teste de ponta a ponta da API (com o servidor rodando em localhost:8000).

Uso: python scripts/teste_api.py caminho/do/comprovante.png
Cria um usuário descartável, exercita todas as rotas e remove o usuário ao final.
"""
import secrets
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402

API = "http://localhost:8000"
falhas = 0


def checar(descricao: str, condicao: bool, detalhe=""):
    global falhas
    print(f"[{'OK ' if condicao else 'ERRO'}] {descricao}" + (f"  -> {detalhe}" if not condicao else ""))
    falhas += not condicao


def main(comprovante: Path) -> None:
    c = httpx.Client(base_url=API, timeout=300)
    email = f"teste_{secrets.token_hex(4)}@exemplo.com"
    senha = secrets.token_urlsafe(12)

    r = c.get("/health")
    checar("health: banco e ollama", r.json().get("banco") and r.json().get("ollama"), r.text)

    # ---- cadastro / login
    r = c.post("/auth/cadastro", json={"nome": "Usuário Teste", "email": email, "senha": senha})
    checar("cadastro 201", r.status_code == 201, r.text)
    r = c.post("/auth/cadastro", json={"nome": "Outro", "email": email.upper(), "senha": senha})
    checar("e-mail duplicado 409", r.status_code == 409, r.text)
    r = c.post("/auth/login", data={"username": email, "password": "senha-errada"})
    checar("senha errada 401", r.status_code == 401, r.text)
    r = c.post("/auth/login", data={"username": email, "password": senha})
    checar("login 200", r.status_code == 200, r.text)
    c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    checar("sem token 401", httpx.get(f"{API}/despesas").status_code == 401)
    r = c.get("/auth/me")
    checar("/auth/me", r.status_code == 200 and r.json()["email"] == email, r.text)

    # ---- categorias
    cats = c.get("/categorias").json()
    checar("6 categorias padrão", sum(x["tipo"] == "padrao" for x in cats) == 6, cats)
    por_nome = {x["nome"]: x["id_categoria"] for x in cats}
    r = c.post("/categorias", json={"nome": "Academia"})
    checar("criar categoria personalizada", r.status_code == 201, r.text)
    id_academia = r.json()["id_categoria"]
    checar("nome duplicado 409", c.post("/categorias", json={"nome": "academia"}).status_code == 409)
    checar("nome igual a padrão 409", c.post("/categorias", json={"nome": "Lazer"}).status_code == 409)
    checar("editar padrão 403", c.put(f"/categorias/{por_nome['Lazer']}", json={"nome": "X"}).status_code == 403)
    r = c.put(f"/categorias/{id_academia}", json={"nome": "Academia e Esportes"})
    checar("renomear personalizada", r.status_code == 200 and r.json()["nome"] == "Academia e Esportes", r.text)

    # ---- despesa manual + regras
    hoje = date.today()
    base = {"valor": "59.90", "data_despesa": str(hoje), "id_categoria": id_academia, "estabelecimento": "Smart Fit"}
    r = c.post("/despesas", json=base)
    checar("despesa manual 201 / status manual", r.status_code == 201 and r.json()["status_extracao"] == "manual", r.text)
    id_manual = r.json()["id_despesa"]
    checar("RN03 valor zero 422", c.post("/despesas", json={**base, "valor": "0"}).status_code == 422)
    futura = str(hoje + timedelta(days=1))
    checar("RN04 data futura 422", c.post("/despesas", json={**base, "data_despesa": futura}).status_code == 422)
    r = c.post("/despesas", json={**base, "id_categoria": 999999})
    checar("categoria inexistente 404", r.status_code == 404, r.text)
    r = c.put(f"/despesas/{id_manual}", json={"valor": "64.90", "descricao": "Mensalidade"})
    checar("editar despesa", r.status_code == 200 and r.json()["valor"] == "64.90", r.text)
    r = c.post("/despesas", json={**base, "valor": "12.00", "id_categoria": por_nome["Transporte"],
                                  "estabelecimento": "Uber", "data_despesa": str(hoje - timedelta(days=40))})
    checar("segunda despesa manual", r.status_code == 201, r.text)

    # ---- comprovante (NuExtract3)
    r = c.post("/despesas/comprovante/extrair", files={"arquivo": ("teste.txt", b"abc", "text/plain")})
    checar("extensão inválida 415", r.status_code == 415, r.text)
    with comprovante.open("rb") as f:
        r = c.post("/despesas/comprovante/extrair", files={"arquivo": (comprovante.name, f, "image/png")})
    checar("extrair 200", r.status_code == 200, r.text)
    ext = r.json()
    print("      extraído:", ext["status"], ext["confianca"], ext["dados"])
    checar("extração com sucesso", ext["status"] == "sucesso", ext)
    # se a leitura falhar, o fluxo continua com dados digitados (como faria o usuário)
    dados = {k: v or d for (k, v), d in zip(ext["dados"].items(), ["84.02", str(hoje), "Mercado", None])}
    confirmar = {
        "id_upload": ext["id_upload"], "valor": dados["valor"], "data_despesa": dados["data_despesa"],
        "estabelecimento": dados["estabelecimento"], "id_categoria": dados["id_categoria_sugerida"] or por_nome["Não categorizado"],
    }
    r = c.post("/despesas/comprovante/confirmar", json={**confirmar, "id_upload": "outro_usuario_x"})
    checar("upload de outro usuário 404", r.status_code == 404, r.text)
    r = c.post("/despesas/comprovante/confirmar", json=confirmar)
    checar("confirmar sem alteração -> concluida",
           r.status_code == 201 and r.json()["status_extracao"] == "concluida" and r.json()["possui_comprovante"], r.text)
    id_comp = r.json()["id_despesa"]
    r = c.get(f"/despesas/{id_comp}/comprovante")
    checar("baixar comprovante", r.status_code == 200 and r.content[:4] == b"\x89PNG", r.status_code)
    r = c.put(f"/despesas/{id_comp}", json={"estabelecimento": "Supermercado Bom Preço"})
    checar("editar extraída -> corrigida_manualmente", r.json().get("status_extracao") == "corrigida_manualmente", r.text)

    with comprovante.open("rb") as f:
        ext2 = c.post("/despesas/comprovante/extrair", files={"arquivo": (comprovante.name, f, "image/png")}).json()
    r = c.post("/despesas/comprovante/confirmar", json={**confirmar, "id_upload": ext2["id_upload"], "valor": "80.00"})
    checar("confirmar com correção -> corrigida_manualmente", r.json().get("status_extracao") == "corrigida_manualmente", r.text)
    r = c.post("/despesas/comprovante/confirmar", json={**confirmar, "id_upload": ext2["id_upload"]})
    checar("reusar upload já confirmado 404", r.status_code == 404, r.text)

    # ---- consultas e relatório
    checar("listar 4 despesas", len(c.get("/despesas").json()) == 4)
    checar("filtro categoria", len(c.get("/despesas", params={"id_categoria": por_nome["Transporte"]}).json()) == 1)
    checar("filtro busca", len(c.get("/despesas", params={"busca": "smart"}).json()) == 1)
    corte = str(hoje - timedelta(days=30))  # a data do cupom de teste é fixa, então o esperado é calculado
    esperadas = sum(d["data_despesa"] >= corte for d in c.get("/despesas").json())
    checar("filtro período", len(c.get("/despesas", params={"data_inicio": corte}).json()) == esperadas)
    res = c.get("/relatorios/resumo").json()
    esperado = 64.90 + 12.00 + float(dados["valor"]) + 80.00
    checar("resumo total", abs(float(res["total"]) - esperado) < 0.01, res)
    print("      resumo:", res)

    # ---- remoção de categoria move despesas para "Não categorizado"
    checar("remover categoria 204", c.delete(f"/categorias/{id_academia}").status_code == 204)
    r = c.get(f"/despesas/{id_manual}")
    checar("despesa movida p/ Não categorizado", r.json()["categoria"]["nome"] == "Não categorizado", r.text)

    # ---- exclusão
    checar("excluir despesa 204", c.delete(f"/despesas/{id_comp}").status_code == 204)
    checar("excluída some 404", c.get(f"/despesas/{id_comp}").status_code == 404)

    # ---- integridade no banco (trigger: categoria de outro usuário)
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as con:
        n = con.execute("SELECT count(*) FROM extracao_ocr e JOIN comprovante c USING (id_comprovante) "
                        "JOIN despesa d USING (id_despesa) JOIN usuario u USING (id_usuario) WHERE u.email=%s",
                        (email,)).fetchone()[0]
        checar("extracao_ocr gravada (1 restante)", n == 1, n)
        try:
            con.execute("INSERT INTO usuario (nome,email,senha_hash) VALUES ('B', %s, 'x')", (f"b_{email}",))
            con.execute("INSERT INTO categoria (id_usuario,nome,tipo) SELECT id_usuario,'Priv','personalizada' "
                        "FROM usuario WHERE email=%s", (f"b_{email}",))
            con.execute("INSERT INTO despesa (id_usuario,id_categoria,valor,data_despesa) SELECT u.id_usuario, "
                        "c.id_categoria, 1, CURRENT_DATE FROM usuario u, categoria c WHERE u.email=%s AND c.nome='Priv'",
                        (email,))
            checar("trigger bloqueia categoria alheia", False, "INSERT aceito")
        except psycopg.errors.RaiseException:
            checar("trigger bloqueia categoria alheia", True)
        con.rollback()
        # limpeza: remove o usuário de teste (cascade em categorias, despesas, comprovantes e extrações)
        arquivos = [r[0] for r in con.execute(
            "SELECT c.caminho_arquivo FROM comprovante c JOIN despesa d USING (id_despesa) "
            "JOIN usuario u USING (id_usuario) WHERE u.email=%s", (email,))]
        con.execute("DELETE FROM usuario WHERE email=%s", (email,))
        con.commit()
    for a in arquivos:
        caminho = get_settings().uploads_path / a
        caminho.unlink(missing_ok=True)
        if not any(caminho.parent.iterdir()):
            caminho.parent.rmdir()

    print(f"\n{'TODOS OS TESTES PASSARAM' if falhas == 0 else f'{falhas} FALHA(S)'}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
