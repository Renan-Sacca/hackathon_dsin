"""SQLAlchemy ORM models package."""
from app.models.user import User, UserType
from app.models.equipamento import (
    Equipamento,
    EquipamentoTipo,
    EquipamentoSituacao,
    ManutencaoTipo,
)
from app.models.equipamento_propriedade import EquipamentoPropriedade
from app.models.agente import Agente, AgenteTipo, AgenteSituacao

from app.models.historico_equipamento import HistoricoEquipamento
from app.models.ocorrencia import Ocorrencia, OcorrenciaTipo, OcorrenciaSeveridade

__all__ = [
    "User",
    "UserType",
    "Equipamento",
    "EquipamentoTipo",
    "EquipamentoSituacao",
    "ManutencaoTipo",
    "EquipamentoPropriedade",
    "Agente",
    "AgenteTipo",
    "AgenteSituacao",
    "HistoricoEquipamento",
    "Ocorrencia",
    "OcorrenciaTipo",
    "OcorrenciaSeveridade",
]
