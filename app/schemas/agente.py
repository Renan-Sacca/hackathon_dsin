import html
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.agente import AgenteSituacao, AgenteTipo


def sanitize_string(val: Optional[str]) -> Optional[str]:
    """Sanitize input string against XSS by escaping HTML entities and trimming."""
    if val is None:
        return None
    return html.escape(val.strip())


class AgenteBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255, description="Nome completo do agente")
    matricula: str = Field(..., min_length=2, max_length=50, description="Matrícula funcional única")
    tipo: AgenteTipo = Field(..., description="Tipo de corporação / agente")
    orgao: str = Field(..., min_length=2, max_length=100, description="Órgão de vínculo")
    telefone: Optional[str] = Field(None, max_length=50, description="Telefone de contato funcional")
    situacao: AgenteSituacao = Field(
        default=AgenteSituacao.EM_ATIVIDADE,
        description="Situação do agente no turno"
    )
    latitude: Optional[float] = Field(None, description="Latitude GPS da última posição")
    longitude: Optional[float] = Field(None, description="Longitude GPS da última posição")

    @field_validator("nome", "matricula", "orgao", "telefone", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_string(v)


class AgenteCreate(AgenteBase):
    pass


class AgenteUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=255)
    matricula: Optional[str] = Field(None, min_length=2, max_length=50)
    tipo: Optional[AgenteTipo] = None
    orgao: Optional[str] = Field(None, min_length=2, max_length=100)
    telefone: Optional[str] = Field(None, max_length=50)
    situacao: Optional[AgenteSituacao] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ativo: Optional[bool] = None

    @field_validator("nome", "matricula", "orgao", "telefone", mode="before")
    @classmethod
    def sanitize_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_string(v)


class AgenteResponse(AgenteBase):
    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)
