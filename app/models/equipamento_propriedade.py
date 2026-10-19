from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.equipamento import Equipamento


class EquipamentoPropriedade(Base):
    __tablename__ = "equipamento_propriedades"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    equipamento_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("equipamentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chave: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    valor: Mapped[str] = mapped_column(String(255), nullable=False)

    equipamento: Mapped["Equipamento"] = relationship(
        "Equipamento",
        back_populates="propriedades"
    )

    def __repr__(self) -> str:
        return f"<EquipamentoPropriedade id={self.id} equipamento_id={self.equipamento_id} chave='{self.chave}' valor='{self.valor}'>"
