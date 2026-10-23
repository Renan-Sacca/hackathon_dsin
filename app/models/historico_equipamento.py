from datetime import datetime, timezone
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
from app.models.equipamento import EquipamentoSituacao


class HistoricoEquipamento(Base):
    __tablename__ = "historico_equipamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    equipamento_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("equipamentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    situacao_anterior: Mapped[Optional[EquipamentoSituacao]] = mapped_column(
        SQLEnum(EquipamentoSituacao, native_enum=False),
        nullable=True
    )
    situacao_nova: Mapped[EquipamentoSituacao] = mapped_column(
        SQLEnum(EquipamentoSituacao, native_enum=False),
        nullable=False,
        index=True
    )

    data_mudanca: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )

    motivo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    custo_manutencao: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tempo_inatividade_horas: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relacionamento ORM
    equipamento = relationship("Equipamento", backref="historico_situacoes")
