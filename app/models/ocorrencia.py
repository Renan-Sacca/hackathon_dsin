from datetime import datetime, timezone
import enum
from typing import Optional
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class OcorrenciaTipo(str, enum.Enum):
    ACIDENTE_TRANSITO = "acidente_transito"
    LENTIDAO_CONGESTIONAMENTO = "lentidao_congestionamento"
    FURTO_ROUBO = "furto_roubo"
    VANDALISMO = "vandalismo"
    ALAGAMENTO = "alagamento"
    FALHA_SEMAFORO = "falha_semaforo"
    FISCALIZACAO = "fiscalizacao"
    OUTRO = "outro"


class OcorrenciaSeveridade(str, enum.Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class Ocorrencia(Base):
    __tablename__ = "ocorrencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)

    tipo: Mapped[OcorrenciaTipo] = mapped_column(
        SQLEnum(OcorrenciaTipo, native_enum=False),
        nullable=False,
        index=True
    )
    severidade: Mapped[OcorrenciaSeveridade] = mapped_column(
        SQLEnum(OcorrenciaSeveridade, native_enum=False),
        default=OcorrenciaSeveridade.MEDIA,
        nullable=False,
        index=True
    )

    descricao: Mapped[str] = mapped_column(String(255), nullable=False)

    localizacao_bairro: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    localizacao_rua: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    data_hora: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )

    # Período do dia para correlação preditiva temporal: 'manha', 'tarde', 'noite', 'madrugada'
    periodo_dia: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Equipamento opcionalmente correlacionado
    equipamento_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("equipamentos.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relacionamento ORM
    equipamento = relationship("Equipamento", backref="ocorrencias_relacionadas")
