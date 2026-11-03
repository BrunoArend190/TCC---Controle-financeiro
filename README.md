# Gestão Financeira Pessoal com OCR (TCC)

Sistema web para registro de despesas com extração automática de dados de comprovantes
(valor, data, estabelecimento e categoria sugerida) usando o modelo **NuExtract3** rodando localmente no Ollama.

| Camada     | Tecnologia                               |
|------------|------------------------------------------|
| Backend    | Python 3.12 + FastAPI + SQLAlchemy       |
| Frontend   | Vue 3 + Quasar + Pinia + Axios + Chart.js |
| Banco      | PostgreSQL (script em `backend/database/schema.sql`) |
| Extração   | NuExtract3 (Q4_K_M) via Ollama           |

## Estrutura

```
sistema/
├── backend/
│   ├── app/
│   │   ├── main.py            # aplicação FastAPI
│   │   ├── config.py          # configurações (.env)
│   │   ├── models.py          # ORM (espelha o schema.sql)
│   │   ├── schemas.py         # validação de entrada/saída (RN03, RN04)
│   │   ├── security.py        # senha (bcrypt) e token JWT
│   │   ├── routers/           # auth, categorias, despesas, relatórios
│   │   └── services/          # extração (NuExtract3) e armazenamento de arquivos
│   ├── database/schema.sql    # cópia de "TCC II/Diagramas/SQL.sql"
│   └── scripts/criar_banco.py
└── frontend/src/              # projeto Quasar (Vue 3), no padrão da disciplina de Programação Visual
    ├── boot/axios.js          # instância do Axios (baseURL /api + token JWT)
    ├── services/              # um arquivo por recurso da API (auth, despesas, categorias, relatórios)
    ├── stores/                # stores Pinia (state, getters, actions)
    ├── router/                # routes.js (MainLayout + children) e guarda de login
    ├── layouts/MainLayout.vue # menu lateral
    ├── pages/                 # Login, Cadastro, Dashboard, Despesas, Comprovante, Categorias
    └── components/            # diálogos de formulário e campos reutilizáveis
```

## Preparação do ambiente (uma vez)

1. **PostgreSQL**: instale o PostgreSQL 16+ (https://www.postgresql.org/download/windows/) e anote a senha do usuário `postgres`.
2. **Ollama + modelo**: com o Ollama aberto, baixe o modelo:
   ```
   ollama pull numind/nuextract3:Q4_K_M
   ```
3. **Backend**:
   ```
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env      # depois edite a senha do banco e o JWT_SECRET
   python scripts/criar_banco.py
   ```
4. **Frontend**:
   ```
   cd frontend
   npm install
   ```

## Executando

Forma mais simples (de qualquer pasta, no terminal ou com duplo clique):

```
C:\Users\Bruno\Desktop\TCC\sistema\iniciar.bat
```

Abre o Ollama (se necessário), a API e o frontend em janelas próprias e carrega o navegador.

Alternativa no VS Code (com a pasta `sistema` aberta): **Terminal → Run Task → "Rodar sistema (backend + frontend)"**
(ou F5 com a configuração "Backend (FastAPI)" para depurar a API).

- Frontend: http://localhost:5173
- API + documentação Swagger: http://localhost:8000/docs
- Diagnóstico (banco e Ollama): http://localhost:8000/health

> O Ollama precisa estar aberto (ícone na bandeja) para a extração funcionar.
> Se não estiver, a tela de comprovante avisa e permite preencher os dados manualmente.

## Teste de ponta a ponta

Com a API rodando, execute na pasta `backend` (use qualquer imagem de cupom fiscal):

```
.venv\Scripts\python.exe scripts\teste_api.py caminho\do\cupom.png
```

O script cria um usuário descartável, exercita todas as rotas (cadastro, login, categorias, despesas,
RN03/RN04, extração, confirmação, relatórios, trigger de integridade) e remove tudo ao final.

## Funcionalidades de gestão

- **Orçamentos:** limite mensal por categoria, com barra de progresso e alerta no Dashboard a partir de 80%.
- **Comparativos:** frases automáticas comparando o mês atual com o mesmo período do mês anterior.
- **Despesas recorrentes:** lançadas automaticamente no dia escolhido. Não há processo agendado: os lançamentos
  vencidos são feitos quando o usuário consulta os dados, então nada se perde com o sistema desligado.
- **Meu perfil:** edição de nome, e-mail e senha, e exclusão da conta com todos os dados.

Um banco criado antes dessas funcionalidades é atualizado, sem perder dados, com:

```
.venv/Scripts/python.exe scripts/migrar_v2.py
```

## Fluxo de registro por comprovante

1. `POST /despesas/comprovante/extrair`: o arquivo é salvo temporariamente e enviado ao NuExtract3
   com um template JSON (`valor_total`, `data`, `estabelecimento`, `categoria` ∈ categorias do usuário).
2. O usuário confere/corrige os dados na tela.
3. `POST /despesas/comprovante/confirmar`: grava `despesa`, `comprovante` e `extracao_ocr`.
   O `status_extracao` fica `concluida` se nada foi alterado, `corrigida_manualmente` se houve correção
   e `falha` se o modelo não conseguiu ler o documento.

A "confiança" registrada em `extracao_ocr` é a proporção de campos do template que o modelo preencheu
com valor válido (o NuExtract não devolve uma probabilidade).
