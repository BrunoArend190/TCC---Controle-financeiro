from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import StatusDespesa, StatusOCR, TipoCategoria


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------- usuário
class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)  # bcrypt usa no máximo 72 bytes


class UsuarioOut(_Orm):
    id_usuario: int
    nome: str
    email: EmailStr
    data_cadastro: datetime


class UsuarioAtualizar(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr


class SenhaAlterar(BaseModel):
    senha_atual: str
    nova_senha: str = Field(min_length=8, max_length=72)


class ContaExcluir(BaseModel):
    senha: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -------------------------------------------------------------- categoria
class CategoriaCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=60)


class CategoriaOut(_Orm):
    id_categoria: int
    nome: str
    tipo: TipoCategoria


# ---------------------------------------------------------------- despesa
def _validar_data(valor: date | None) -> date | None:
    if valor is not None and valor > date.today():
        raise ValueError("A data da despesa não pode ser futura")  # RN04
    return valor


class DespesaBase(BaseModel):
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)  # RN03
    data_despesa: date
    id_categoria: int
    estabelecimento: str | None = Field(default=None, max_length=150)
    descricao: str | None = Field(default=None, max_length=255)

    _data = field_validator("data_despesa")(_validar_data)


class DespesaCriar(DespesaBase):
    pass


class DespesaDeComprovante(DespesaBase):
    """Confirmação de uma despesa cujos dados vieram (e talvez foram corrigidos) da extração."""

    id_upload: str


class DespesaAtualizar(BaseModel):
    valor: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    data_despesa: date | None = None
    id_categoria: int | None = None
    estabelecimento: str | None = Field(default=None, max_length=150)
    descricao: str | None = Field(default=None, max_length=255)

    _data = field_validator("data_despesa")(_validar_data)


class DespesaOut(_Orm):
    id_despesa: int
    valor: Decimal
    data_despesa: date
    estabelecimento: str | None
    descricao: str | None
    status_extracao: StatusDespesa
    data_criacao: datetime
    categoria: CategoriaOut
    possui_comprovante: bool


# ------------------------------------------------------ despesa recorrente
class RecorrenteSalvar(BaseModel):
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    id_categoria: int
    estabelecimento: str | None = Field(default=None, max_length=150)
    descricao: str | None = Field(default=None, max_length=255)
    dia_lancamento: int = Field(ge=1, le=31)
    ativa: bool = True


class RecorrenteOut(_Orm):
    id_recorrente: int
    valor: Decimal
    estabelecimento: str | None
    descricao: str | None
    dia_lancamento: int
    proximo_lancamento: date
    ativa: bool
    categoria: CategoriaOut


# --------------------------------------------------------------- orçamento
class OrcamentoSalvar(BaseModel):
    valor_limite: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class OrcamentoOut(BaseModel):
    id_orcamento: int
    categoria: CategoriaOut
    valor_limite: Decimal
    gasto: Decimal
    restante: Decimal
    percentual: float
    situacao: str  # ok | alerta | excedido


# --------------------------------------------------------------- extração
class DadosExtraidos(BaseModel):
    valor: Decimal | None = None
    data_despesa: date | None = None
    estabelecimento: str | None = None
    id_categoria_sugerida: int | None = None


class ResultadoExtracao(BaseModel):
    id_upload: str
    status: StatusOCR
    confianca: Decimal
    dados: DadosExtraidos
    mensagem: str | None = None


# ------------------------------------------------------------- relatórios
class TotalPorCategoria(BaseModel):
    categoria: str
    total: Decimal


class TotalPorMes(BaseModel):
    mes: str  # AAAA-MM
    total: Decimal


class Resumo(BaseModel):
    total: Decimal
    quantidade: int
    por_categoria: list[TotalPorCategoria]
    por_mes: list[TotalPorMes]


class FraseComparativo(BaseModel):
    tipo: str  # aumento | queda
    texto: str


class Comparativo(BaseModel):
    total_atual: Decimal
    total_anterior: Decimal
    frases: list[FraseComparativo]
