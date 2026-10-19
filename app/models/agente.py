from datetime import datetime, timezone
import enum
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    String,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class AgenteTipo(str, enum.Enum):
    AGENTE_TRANSITO = "agente_transito"
    GUARDA_MUNICIPAL = "guarda_municipal"
    POLICIAL_MILITAR = "policial_militar"


class AgenteSituacao(str, enum.Enum):
    EM_ATIVIDADE = "em_atividade"
    FORA_DE_SERVICO = "fora_de_servico"
    FERIAS = "ferias"
    AFASTADO = "afastado"


class Agente(Base):
    __tablename__ = "agentes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    matricula: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    tipo: Mapped[AgenteTipo] = mapped_column(
        SQLEnum(AgenteTipo, native_enum=False),
        nullable=False,
        index=True
    )
    orgao: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    situacao: Mapped[AgenteSituacao] = mapped_column(
        SQLEnum(AgenteSituacao, native_enum=False),
        default=AgenteSituacao.EM_ATIVIDADE,
        nullable=False,
        index=True
    )

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Agente id={self.id} matricula='{self.matricula}' tipo='{self.tipo.value}' situacao='{self.situacao.value}'>"
