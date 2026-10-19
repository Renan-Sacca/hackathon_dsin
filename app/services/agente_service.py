from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.agente import Agente, AgenteSituacao, AgenteTipo
from app.repositories.agente_repository import AgenteRepository
from app.schemas.agente import AgenteCreate, AgenteUpdate


class AgenteService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AgenteRepository(db)

    def validate_coordinates(self, lat: Optional[float], lon: Optional[float]) -> None:
        if lat is not None and not (-90.0 <= lat <= 90.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Latitude inválida: {lat}. Deve estar entre -90 e 90."
            )
        if lon is not None and not (-180.0 <= lon <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Longitude inválida: {lon}. Deve estar entre -180 e 180."
            )

    def create_agente(self, data: AgenteCreate) -> Agente:
        existing = self.repo.get_by_matricula(data.matricula)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agente com matrícula '{data.matricula}' já cadastrado."
            )

        self.validate_coordinates(data.latitude, data.longitude)
        return self.repo.create(data)

    def update_agente(self, agente_id: int, data: AgenteUpdate) -> Agente:
        agente = self.repo.get_by_id(agente_id)
        if not agente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agente ID {agente_id} não encontrado."
            )

        if data.matricula and data.matricula != agente.matricula:
            existing = self.repo.get_by_matricula(data.matricula)
            if existing and existing.id != agente_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Matrícula '{data.matricula}' já pertence a outro agente."
                )

        lat = data.latitude if data.latitude is not None else agente.latitude
        lon = data.longitude if data.longitude is not None else agente.longitude
        self.validate_coordinates(lat, lon)

        return self.repo.update(agente, data)

    def get_agente(self, agente_id: int) -> Agente:
        agente = self.repo.get_by_id(agente_id)
        if not agente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agente ID {agente_id} não encontrado."
            )
        return agente

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
        return self.repo.list_agentes(
            skip=skip,
            limit=limit,
            tipo=tipo,
            situacao=situacao,
            orgao=orgao,
            busca=busca,
            apenas_ativos=apenas_ativos
        )

    def delete_agente(self, agente_id: int) -> Agente:
        agente = self.get_agente(agente_id)
        return self.repo.soft_delete(agente)

    def get_filter_options(self) -> dict:
        return {
            "orgaos": self.repo.get_orgaos(),
            "tipos": [t.value for t in AgenteTipo],
            "situacoes": [s.value for s in AgenteSituacao],
        }
