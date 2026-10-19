from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.equipamento import (
    Equipamento,
    EquipamentoSituacao,
    EquipamentoTipo,
    ManutencaoTipo,
)
from app.models.equipamento_propriedade import EquipamentoPropriedade
from app.schemas.equipamento import EquipamentoCreate, EquipamentoUpdate


class EquipamentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, equipamento_id: int) -> Optional[Equipamento]:
        stmt = select(Equipamento).where(Equipamento.id == equipamento_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_numero_serie(self, numero_serie: str) -> Optional[Equipamento]:
        stmt = select(Equipamento).where(Equipamento.numero_serie == numero_serie)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_equipamentos(
        self,
        skip: int = 0,
        limit: int = 100,
        tipo: Optional[EquipamentoTipo] = None,
        situacao: Optional[EquipamentoSituacao] = None,
        bairro: Optional[str] = None,
        orgao: Optional[str] = None,
        manutencao_tipo: Optional[ManutencaoTipo] = None,
        busca: Optional[str] = None,
        apenas_ativos: bool = True
    ) -> Tuple[List[Equipamento], int]:
        stmt = select(Equipamento)

        if apenas_ativos:
            stmt = stmt.where(Equipamento.ativo.is_(True))

        if tipo:
            stmt = stmt.where(Equipamento.tipo == tipo)

        if situacao:
            stmt = stmt.where(Equipamento.situacao == situacao)

        if bairro:
            stmt = stmt.where(Equipamento.localizacao_bairro == bairro)

        if orgao:
            stmt = stmt.where(Equipamento.orgao_responsavel == orgao)

        if manutencao_tipo:
            stmt = stmt.where(Equipamento.manutencao_tipo == manutencao_tipo)

        if busca:
            termo = f"%{busca.strip()}%"
            stmt = stmt.where(
                or_(
                    Equipamento.numero_serie.ilike(termo),
                    Equipamento.marca.ilike(termo),
                    Equipamento.modelo.ilike(termo),
                    Equipamento.localizacao_rua.ilike(termo),
                    Equipamento.localizacao_bairro.ilike(termo),
                    Equipamento.localizacao_referencia.ilike(termo),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0

        # Query items
        stmt = stmt.offset(skip).limit(limit).order_by(Equipamento.id.desc())
        items = list(self.db.execute(stmt).scalars().all())

        return items, total

    def create(self, equipamento_in: EquipamentoCreate) -> Equipamento:
        data = equipamento_in.model_dump(exclude={"propriedades"})
        propriedades_data = equipamento_in.propriedades or []

        equipamento = Equipamento(**data, ativo=True)

        for prop in propriedades_data:
            equipamento.propriedades.append(
                EquipamentoPropriedade(chave=prop.chave, valor=prop.valor)
            )

        self.db.add(equipamento)
        self.db.commit()
        self.db.refresh(equipamento)
        return equipamento

    def update(self, equipamento: Equipamento, equipamento_in: EquipamentoUpdate) -> Equipamento:
        update_data = equipamento_in.model_dump(exclude_unset=True, exclude={"propriedades"})

        for field, value in update_data.items():
            setattr(equipamento, field, value)

        if equipamento_in.propriedades is not None:
            # Substitui propriedades
            equipamento.propriedades.clear()
            for prop in equipamento_in.propriedades:
                equipamento.propriedades.append(
                    EquipamentoPropriedade(chave=prop.chave, valor=prop.valor)
                )

        self.db.commit()
        self.db.refresh(equipamento)
        return equipamento

    def soft_delete(self, equipamento: Equipamento) -> Equipamento:
        equipamento.ativo = False
        self.db.commit()
        self.db.refresh(equipamento)
        return equipamento

    def get_bairros(self) -> List[str]:
        stmt = (
            select(Equipamento.localizacao_bairro)
            .where(Equipamento.ativo.is_(True))
            .distinct()
            .order_by(Equipamento.localizacao_bairro)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_orgaos(self) -> List[str]:
        stmt = (
            select(Equipamento.orgao_responsavel)
            .where(Equipamento.ativo.is_(True))
            .distinct()
            .order_by(Equipamento.orgao_responsavel)
        )
        return list(self.db.execute(stmt).scalars().all())
