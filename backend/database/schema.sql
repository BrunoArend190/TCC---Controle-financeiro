-- =====================================================================
-- Script de criação do banco de dados
-- Sistema de Gestão Financeira Pessoal com OCR (NuExtract-3)
-- PostgreSQL 14+
-- =====================================================================

-- ---------------------------------------------------------------------
-- Tipos enumerados
-- ---------------------------------------------------------------------
CREATE TYPE tipo_categoria AS ENUM ('padrao', 'personalizada');

-- 'manual' = despesa registrada sem comprovante (não passa pela extração)
-- 'recorrente' = lançada automaticamente a partir de uma despesa recorrente
CREATE TYPE status_despesa AS ENUM ('manual', 'pendente', 'concluida', 'falha', 'corrigida_manualmente', 'recorrente');

CREATE TYPE status_ocr AS ENUM ('sucesso', 'falha_parcial', 'falha_total');

-- ---------------------------------------------------------------------
-- Tabela: usuario
-- ---------------------------------------------------------------------
CREATE TABLE usuario (
    id_usuario      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome            VARCHAR(120) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    senha_hash      VARCHAR(255) NOT NULL,
    data_cadastro   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- Tabela: categoria
-- id_usuario NULL = categoria padrão do sistema (compartilhada)
-- id_usuario preenchido = categoria personalizada (RN07)
-- ---------------------------------------------------------------------
CREATE TABLE categoria (
    id_categoria    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario      INTEGER NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    nome            VARCHAR(60) NOT NULL,
    tipo            tipo_categoria NOT NULL DEFAULT 'personalizada',
    CONSTRAINT chk_categoria_padrao_sem_usuario
        CHECK ( (tipo = 'padrao' AND id_usuario IS NULL)
             OR (tipo = 'personalizada' AND id_usuario IS NOT NULL) )
);

-- Nome de categoria único por usuário (e entre as categorias padrão),
-- sem diferenciar maiúsculas/minúsculas
CREATE UNIQUE INDEX uq_categoria_usuario_nome
    ON categoria (COALESCE(id_usuario, 0), LOWER(nome));

-- Garante o uso apenas de categoria padrão ou categoria do próprio usuário (RN09)
CREATE FUNCTION fn_valida_categoria_usuario() RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM categoria c
         WHERE c.id_categoria = NEW.id_categoria
           AND (c.id_usuario IS NULL OR c.id_usuario = NEW.id_usuario)
    ) THEN
        RAISE EXCEPTION 'Categoria % não pertence ao usuário %', NEW.id_categoria, NEW.id_usuario;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------
-- Tabela: despesa_recorrente (modelo lançado automaticamente todo mês)
-- ---------------------------------------------------------------------
CREATE TABLE despesa_recorrente (
    id_recorrente       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario          INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_categoria        INTEGER NOT NULL REFERENCES categoria(id_categoria) ON DELETE NO ACTION,
    valor               DECIMAL(10,2) NOT NULL,
    estabelecimento     VARCHAR(150),
    descricao           VARCHAR(255),
    dia_lancamento      SMALLINT NOT NULL,
    proximo_lancamento  DATE NOT NULL,
    ativa               BOOLEAN NOT NULL DEFAULT TRUE,
    data_criacao        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_recorrente_valor CHECK (valor > 0),
    CONSTRAINT chk_recorrente_dia CHECK (dia_lancamento BETWEEN 1 AND 31)
);

CREATE TRIGGER trg_valida_categoria_recorrente
    BEFORE INSERT OR UPDATE OF id_categoria, id_usuario ON despesa_recorrente
    FOR EACH ROW EXECUTE FUNCTION fn_valida_categoria_usuario();

-- ---------------------------------------------------------------------
-- Tabela: orcamento (limite mensal por categoria)
-- ---------------------------------------------------------------------
CREATE TABLE orcamento (
    id_orcamento   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario     INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_categoria   INTEGER NOT NULL REFERENCES categoria(id_categoria) ON DELETE CASCADE,
    valor_limite   DECIMAL(10,2) NOT NULL,
    CONSTRAINT uq_orcamento_usuario_categoria UNIQUE (id_usuario, id_categoria),
    CONSTRAINT chk_orcamento_limite CHECK (valor_limite > 0)
);

CREATE TRIGGER trg_valida_categoria_orcamento
    BEFORE INSERT OR UPDATE OF id_categoria, id_usuario ON orcamento
    FOR EACH ROW EXECUTE FUNCTION fn_valida_categoria_usuario();

-- ---------------------------------------------------------------------
-- Tabela: despesa
-- ---------------------------------------------------------------------
CREATE TABLE despesa (
    id_despesa        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario        INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    -- NO ACTION (padrão) em vez de RESTRICT: permite que a exclusão em cascata
    -- de um usuário remova suas despesas e categorias no mesmo comando
    id_categoria      INTEGER NOT NULL REFERENCES categoria(id_categoria) ON DELETE NO ACTION,
    valor             DECIMAL(10,2) NOT NULL,
    data_despesa      DATE NOT NULL,
    estabelecimento   VARCHAR(150),
    descricao         VARCHAR(255),
    status_extracao   status_despesa NOT NULL DEFAULT 'manual',
    id_recorrente     INTEGER NULL REFERENCES despesa_recorrente(id_recorrente) ON DELETE SET NULL,
    data_criacao      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_despesa_recorrente_data UNIQUE (id_recorrente, data_despesa), -- evita lançamento duplicado
    CONSTRAINT chk_valor_positivo CHECK (valor > 0),                    -- RN03
    CONSTRAINT chk_data_nao_futura CHECK (data_despesa <= CURRENT_DATE) -- RN04
);

CREATE TRIGGER trg_valida_categoria_despesa
    BEFORE INSERT OR UPDATE OF id_categoria, id_usuario ON despesa
    FOR EACH ROW EXECUTE FUNCTION fn_valida_categoria_usuario();

-- ---------------------------------------------------------------------
-- Tabela: comprovante (0..1 por despesa - despesas manuais não possuem)
-- ---------------------------------------------------------------------
CREATE TABLE comprovante (
    id_comprovante    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_despesa        INTEGER NOT NULL UNIQUE REFERENCES despesa(id_despesa) ON DELETE CASCADE,
    caminho_arquivo   VARCHAR(255) NOT NULL,
    tipo_arquivo      VARCHAR(10) NOT NULL,
    tamanho_arquivo   INTEGER NOT NULL,
    data_upload       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_tipo_arquivo CHECK (tipo_arquivo IN ('jpg','jpeg','png','pdf')),
    CONSTRAINT chk_tamanho_arquivo CHECK (tamanho_arquivo > 0)
);

-- ---------------------------------------------------------------------
-- Tabela: extracao_ocr (histórico de tentativas de extração via NuExtract-3)
-- ---------------------------------------------------------------------
CREATE TABLE extracao_ocr (
    id_extracao            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_comprovante         INTEGER NOT NULL REFERENCES comprovante(id_comprovante) ON DELETE CASCADE,
    id_categoria_sugerida  INTEGER NULL REFERENCES categoria(id_categoria) ON DELETE SET NULL,
    json_bruto             JSONB,
    modelo_utilizado       VARCHAR(60) NOT NULL DEFAULT 'NuExtract-3',
    confianca              DECIMAL(3,2),
    status                 status_ocr NOT NULL,
    data_processamento     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_confianca CHECK (confianca BETWEEN 0 AND 1)
);

-- ---------------------------------------------------------------------
-- Índices de apoio às consultas mais frequentes (RF10 - filtros)
-- ---------------------------------------------------------------------
CREATE INDEX idx_despesa_usuario_data   ON despesa (id_usuario, data_despesa);
CREATE INDEX idx_despesa_categoria      ON despesa (id_categoria);
CREATE INDEX idx_categoria_usuario      ON categoria (id_usuario);
CREATE INDEX idx_extracao_comprovante   ON extracao_ocr (id_comprovante);

-- ---------------------------------------------------------------------
-- Categorias padrão iniciais (seed)
-- ---------------------------------------------------------------------
INSERT INTO categoria (id_usuario, nome, tipo) VALUES
    (NULL, 'Alimentação', 'padrao'),
    (NULL, 'Transporte', 'padrao'),
    (NULL, 'Saúde', 'padrao'),
    (NULL, 'Moradia', 'padrao'),
    (NULL, 'Lazer', 'padrao'),
    (NULL, 'Não categorizado', 'padrao');
