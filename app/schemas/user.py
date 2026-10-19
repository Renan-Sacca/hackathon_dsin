import html
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.user import UserType


def sanitize_string(val: Optional[str]) -> Optional[str]:
    """Sanitize input string against XSS by escaping HTML entities and trimming."""
    if val is None:
        return None
    return html.escape(val.strip())


class UserBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="E-mail de acesso corporativo")
    tipo: UserType = Field(default=UserType.OPERADOR, description="Nível de acesso no sistema")

    @field_validator("nome", mode="before")
    @classmethod
    def sanitize_nome(cls, v: str) -> str:
        return sanitize_string(v) or ""


class UserCreate(UserBase):
    senha: str = Field(..., min_length=6, max_length=128, description="Senha de acesso")


class UserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    tipo: Optional[UserType] = None
    senha: Optional[str] = Field(None, min_length=6, max_length=128)
    ativo: Optional[bool] = None

    @field_validator("nome", mode="before")
    @classmethod
    def sanitize_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_string(v)


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="E-mail cadastrado")
    senha: str = Field(..., description="Senha cadastrada")


class UserResponse(UserBase):
    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
