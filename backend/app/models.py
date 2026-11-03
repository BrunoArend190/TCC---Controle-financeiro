"""Mapeamento ORM das tabelas definidas em database/schema.sql.

O esquema é criado pelo script SQL (fonte de verdade do MER do TCC);
estes modelos apenas o refletem, por isso os ENUMs usam create_type=False.
"""
import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoCategoria(str, enum.Enum):
    padrao = "padrao"
    personalizada = "personalizada"


class StatusDespesa(str, enum.Enum):
    manual = "manual"
    pendente = "pendente"
    concluida = "concluida"
    falha = "falha"
    corrigida_manualmente = "corrigida_manualmente"
    recorrente = "recorrente"


class StatusOCR(str, enum.Enum):
    sucesso = "sucesso"
    falha_parcial = "falha_parcial"
    falha_total = "falha_total"


def _pg_enum(enum_cls: type[enum.Enum], nome: str) -> Enum:
    return Enum(enum_cls, name=nome, create_type=False, values_callable=lambda e: [m.value for m in e])


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    data_cadastro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Categoria(Base):
    __tablename__ = "categoria"

    id_categoria: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey("usuario.id_usuario", ondelete="CASCADE"))
    nome: Mapped[str] = mapped_column(String(60))
    tipo: Mapped[TipoCategoria] = mapped_column(
        _pg_enum(TipoCategoria, "tipo_categoria"), default=TipoCategoria.personalizada
    )


class DespesaRecorrente(Base):
    """Modelo de despesa lançado automaticamente todo mês (ex.: aluguel, assinaturas)."""

    __tablename__ = "despesa_recorrente"

    id_recorrente: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario", ondelete="CASCADE"))
    id_categoria: Mapped[int] = mapped_column(ForeignKey("categoria.id_categoria"))
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estabelecimento: Mapped[str | None] = mapped_column(String(150))
    descricao: Mapped[str | None] = mapped_column(String(255))
    dia_lancamento: Mapped[int] = mapped_column(SmallInteger)
    proximo_lancamento: Mapped[date] = mapped_column(Date)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    categoria: Mapped[Categoria] = relationship(lazy="joined")


class Orcamento(Base):
    """Limite de gastos mensal de um usuário em uma categoria."""

    __tablename__ = "orcamento"

    id_orcamento: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario", ondelete="CASCADE"))
    id_categoria: Mapped[int] = mapped_column(ForeignKey("categoria.id_categoria", ondelete="CASCADE"))
    valor_limite: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    categoria: Mapped[Categoria] = relationship(lazy="joined")


class Despesa(Base):
    __tablename__ = "despesa"

    id_despesa: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario", ondelete="CASCADE"))
    id_categoria: Mapped[int] = mapped_column(ForeignKey("categoria.id_categoria"))
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    data_despesa: Mapped[date] = mapped_column(Date)
    estabelecimento: Mapped[str | None] = mapped_column(String(150))
    descricao: Mapped[str | None] = mapped_column(String(255))
    status_extracao: Mapped[StatusDespesa] = mapped_column(
        _pg_enum(StatusDespesa, "status_despesa"), default=StatusDespesa.manual
    )
    id_recorrente: Mapped[int | None] = mapped_column(
        ForeignKey("despesa_recorrente.id_recorrente", ondelete="SET NULL")
    )
    data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    categoria: Mapped[Categoria] = relationship(lazy="joined")
    comprovante: Mapped["Comprovante | None"] = relationship(
        back_populates="despesa", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def possui_comprovante(self) -> bool:
        return self.comprovante is not None


class Comprovante(Base):
    __tablename__ = "comprovante"

    id_comprovante: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    id_despesa: Mapped[int] = mapped_column(
        ForeignKey("despesa.id_despesa", ondelete="CASCADE"), unique=True
    )
    caminho_arquivo: Mapped[str] = mapped_column(String(255))
    tipo_arquivo: Mapped[str] = mapped_column(String(10))
    tamanho_arquivo: Mapped[int] = mapped_column(Integer)
    data_upload: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    despesa: Mapped[Despesa] = relationship(back_populates="comprovante")
    extracoes: Mapped[list["ExtracaoOCR"]] = relationship(
        back_populates="comprovante", cascade="all, delete-orphan", passive_deletes=True
    )


class ExtracaoOCR(Base):
    __tablename__ = "extracao_ocr"

    id_extracao: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    id_comprovante: Mapped[int] = mapped_column(
        ForeignKey("comprovante.id_comprovante", ondelete="CASCADE")
    )
    id_categoria_sugerida: Mapped[int | None] = mapped_column(
        ForeignKey("categoria.id_categoria", ondelete="SET NULL")
    )
    json_bruto: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    modelo_utilizado: Mapped[str] = mapped_column(String(60), default="NuExtract-3")
    confianca: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    status: Mapped[StatusOCR] = mapped_column(_pg_enum(StatusOCR, "status_ocr"))
    data_processamento: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    comprovante: Mapped[Comprovante] = relationship(back_populates="extracoes")
