import html
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.equipamento import EquipamentoSituacao, EquipamentoTipo, ManutencaoTipo


def sanitize_string(val: Optional[str]) -> Optional[str]:
    """Sanitize input string against XSS by escaping HTML entities and trimming."""
    if val is None:
        return None
    return html.escape(val.strip())


class PropriedadeItem(BaseModel):
    chave: str = Field(..., min_length=1, max_length=100, description="Nome da propriedade")
    valor: str = Field(..., max_length=255, description="Valor da propriedade")

    @field_validator("chave", "valor", mode="before")
    @classmethod
    def sanitize(cls, v: str) -> str:
        return sanitize_string(v) or ""

    model_config = ConfigDict(from_attributes=True)


class PropriedadeResponse(PropriedadeItem):
    id: int
    equipamento_id: int

    model_config = ConfigDict(from_attributes=True)


class EquipamentoBase(BaseModel):
    numero_serie: str = Field(..., min_length=2, max_length=100, description="Número de série único")
    marca: str = Field(..., min_length=1, max_length=100, description="Fabricante")
    modelo: str = Field(..., min_length=1, max_length=100, description="Modelo")
    tipo: EquipamentoTipo = Field(..., description="Tipo do equipamento")
    situacao: EquipamentoSituacao = Field(
        default=EquipamentoSituacao.NAO_INSTALADO,
        description="Situação operacional"
    )
    manutencao_tipo: ManutencaoTipo = Field(
        default=ManutencaoTipo.NENHUMA,
        description="Necessidade de manutenção"
    )
    proxima_manutencao: Optional[date] = Field(None, description="Data agendada da próxima manutenção")

    # Localização
    localizacao_cep: Optional[str] = Field(None, max_length=20, description="CEP")
    localizacao_bairro: str = Field(..., min_length=1, max_length=100, description="Bairro")
    localizacao_cidade: str = Field(default="Marília", max_length=100, description="Cidade")
    localizacao_uf: str = Field(default="SP", min_length=2, max_length=2, description="UF")
    localizacao_rua: str = Field(..., min_length=1, max_length=255, description="Rua / Avenida")
    localizacao_referencia: Optional[str] = Field(None, max_length=255, description="Ponto de referência")
    latitude: float = Field(..., description="Latitude GPS")
    longitude: float = Field(..., description="Longitude GPS")

    orgao_responsavel: str = Field(..., min_length=1, max_length=100, description="Órgão responsável")

    @field_validator(
        "numero_serie",
        "marca",
        "modelo",
        "localizacao_cep",
        "localizacao_bairro",
        "localizacao_cidade",
        "localizacao_uf",
        "localizacao_rua",
        "localizacao_referencia",
        "orgao_responsavel",
        mode="before"
    )
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_string(v)


class EquipamentoCreate(EquipamentoBase):
    propriedades: Optional[List[PropriedadeItem]] = Field(
        default_factory=list,
        description="Propriedades dinâmicas por tipo (chave-valor)"
    )


class EquipamentoUpdate(BaseModel):
    numero_serie: Optional[str] = Field(None, min_length=2, max_length=100)
    marca: Optional[str] = Field(None, min_length=1, max_length=100)
    modelo: Optional[str] = Field(None, min_length=1, max_length=100)
    tipo: Optional[EquipamentoTipo] = None
    situacao: Optional[EquipamentoSituacao] = None
    manutencao_tipo: Optional[ManutencaoTipo] = None
    proxima_manutencao: Optional[date] = None

    localizacao_cep: Optional[str] = Field(None, max_length=20)
    localizacao_bairro: Optional[str] = Field(None, min_length=1, max_length=100)
    localizacao_cidade: Optional[str] = Field(None, max_length=100)
    localizacao_uf: Optional[str] = Field(None, min_length=2, max_length=2)
    localizacao_rua: Optional[str] = Field(None, min_length=1, max_length=255)
    localizacao_referencia: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    orgao_responsavel: Optional[str] = Field(None, min_length=1, max_length=100)
    ativo: Optional[bool] = None
    propriedades: Optional[List[PropriedadeItem]] = None

    @field_validator(
        "numero_serie",
        "marca",
        "modelo",
        "localizacao_cep",
        "localizacao_bairro",
        "localizacao_cidade",
        "localizacao_uf",
        "localizacao_rua",
        "localizacao_referencia",
        "orgao_responsavel",
        mode="before"
    )
    @classmethod
    def sanitize_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_string(v)


class EquipamentoResponse(EquipamentoBase):
    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime
    propriedades: List[PropriedadeResponse] = []

    model_config = ConfigDict(from_attributes=True)
