from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.agente import Agente, AgenteSituacao, AgenteTipo
from app.schemas.agente import AgenteCreate, AgenteUpdate


class AgenteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, agente_id: int) -> Optional[Agente]:
        stmt = select(Agente).where(Agente.id == agente_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_matricula(self, matricula: str) -> Optional[Agente]:
        stmt = select(Agente).where(Agente.matricula == matricula)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_agentes(
        self,
        skip: int = 0,
        limit: int = 100,
        tipo: Optional[AgenteTipo] = None,
        situacao: Optional[AgenteSituacao] = None,
        orgao: Optional[str] = None,
        busca: Optional[str] = None,
        apenas_ativos: bool = True
    ) -> Tuple[List[Agente], int]:
        stmt = select(Agente)

        if apenas_ativos:
            stmt = stmt.where(Agente.ativo.is_(True))

        if tipo:
            stmt = stmt.where(Agente.tipo == tipo)

        if situacao:
            stmt = stmt.where(Agente.situacao == situacao)

        if orgao:
            stmt = stmt.where(Agente.orgao == orgao)

        if busca:
            termo = f"%{busca.strip()}%"
            stmt = stmt.where(
                or_(
                    Agente.nome.ilike(termo),
                    Agente.matricula.ilike(termo),
                    Agente.orgao.ilike(termo),
                    Agente.telefone.ilike(termo),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0

        # Query items
        stmt = stmt.offset(skip).limit(limit).order_by(Agente.id.desc())
        items = list(self.db.execute(stmt).scalars().all())

        return items, total

    def create(self, agente_in: AgenteCreate) -> Agente:
        agente = Agente(**agente_in.model_dump(), ativo=True)
        self.db.add(agente)
        self.db.commit()
        self.db.refresh(agente)
        return agente

    def update(self, agente: Agente, agente_in: AgenteUpdate) -> Agente:
        update_data = agente_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agente, field, value)

        self.db.commit()
        self.db.refresh(agente)
        return agente

    def soft_delete(self, agente: Agente) -> Agente:
        agente.ativo = False
        self.db.commit()
        self.db.refresh(agente)
        return agente

    def get_orgaos(self) -> List[str]:
        stmt = (
            select(Agente.orgao)
            .where(Agente.ativo.is_(True))
            .distinct()
            .order_by(Agente.orgao)
        )
        return list(self.db.execute(stmt).scalars().all())
