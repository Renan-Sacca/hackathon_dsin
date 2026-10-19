from datetime import date, datetime, timezone
import enum
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    String,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class EquipamentoTipo(str, enum.Enum):
    RADAR_VELOCIDADE = "radar_velocidade"
    RADAR_SEMAFORO = "radar_semaforo"
    RADAR_CONVERSAO = "radar_conversao"
    CAMERA_MONITORAMENTO = "camera_monitoramento"
    BALANCA_CAMINHAO = "balanca_caminhao"
    VEICULO_FISCALIZACAO_ESTACIONAMENTO = "veiculo_fiscalizacao_estacionamento"
    CANCELA_AUTOMATIZADA = "cancela_automatizada"
    VEICULO_TRANSPORTE = "veiculo_transporte"
    TOTEM_ESTACIONAMENTO = "totem_estacionamento"
    PATINETE_ELETRICO = "patinete_eletrico"
    MOTO_AGENTE = "moto_agente"
    VIATURA_GUARDA = "viatura_guarda"
    VIATURA_POLICIA = "viatura_policia"
    OUTRO = "outro"


class EquipamentoSituacao(str, enum.Enum):
    NAO_INSTALADO = "nao_instalado"
    OPERACIONAL = "operacional"
    MAU_FUNCIONAMENTO = "mau_funcionamento"
    MANUTENCAO = "manutencao"
    DESATIVADO = "desativado"
    FURTADO = "furtado"


class ManutencaoTipo(str, enum.Enum):
    NENHUMA = "nenhuma"
    IMEDIATA = "imediata"
    AGENDADA = "agendada"


class Equipamento(Base):
    __tablename__ = "equipamentos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    numero_serie: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    marca: Mapped[str] = mapped_column(String(100), nullable=False)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)

    tipo: Mapped[EquipamentoTipo] = mapped_column(
        SQLEnum(EquipamentoTipo, native_enum=False),
        nullable=False,
        index=True
    )
    situacao: Mapped[EquipamentoSituacao] = mapped_column(
        SQLEnum(EquipamentoSituacao, native_enum=False),
        default=EquipamentoSituacao.NAO_INSTALADO,
        nullable=False,
        index=True
    )
    manutencao_tipo: Mapped[ManutencaoTipo] = mapped_column(
        SQLEnum(ManutencaoTipo, native_enum=False),
        default=ManutencaoTipo.NENHUMA,
        nullable=False,
        index=True
    )
    proxima_manutencao: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Localização
    localizacao_cep: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    localizacao_bairro: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    localizacao_cidade: Mapped[str] = mapped_column(String(100), nullable=False, default="Marília")
    localizacao_uf: Mapped[str] = mapped_column(String(2), nullable=False, default="SP")
    localizacao_rua: Mapped[str] = mapped_column(String(255), nullable=False)
    localizacao_referencia: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    orgao_responsavel: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
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

    # Relationships
    propriedades: Mapped[List["EquipamentoPropriedade"]] = relationship(
        "EquipamentoPropriedade",
        back_populates="equipamento",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Equipamento id={self.id} serie='{self.numero_serie}' tipo='{self.tipo.value}' situacao='{self.situacao.value}'>"
