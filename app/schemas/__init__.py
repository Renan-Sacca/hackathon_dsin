"""Pydantic schemas package for PROMETHEUS — F.O.G.O."""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.schemas.equipamento import (
    PropriedadeItem,
    PropriedadeResponse,
    EquipamentoBase,
    EquipamentoCreate,
    EquipamentoUpdate,
    EquipamentoResponse,
)
from app.schemas.agente import (
    AgenteBase,
    AgenteCreate,
    AgenteUpdate,
    AgenteResponse,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "PropriedadeItem",
    "PropriedadeResponse",
    "EquipamentoBase",
    "EquipamentoCreate",
    "EquipamentoUpdate",
    "EquipamentoResponse",
    "AgenteBase",
    "AgenteCreate",
    "AgenteUpdate",
    "AgenteResponse",
]
