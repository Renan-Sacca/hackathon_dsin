from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.agente import AgenteSituacao, AgenteTipo
from app.models.user import User
from app.schemas.agente import AgenteCreate, AgenteResponse, AgenteUpdate
from app.services.agente_service import AgenteService

router = APIRouter(prefix="/api/agentes", tags=["Agentes"])


class AgenteListResponse(BaseModel):
    total: int
    items: List[AgenteResponse]


@router.get("", response_model=AgenteListResponse, summary="Listar Agentes com Filtros")
def list_agentes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    tipo: Optional[AgenteTipo] = None,
    situacao: Optional[AgenteSituacao] = None,
    orgao: Optional[str] = None,
    busca: Optional[str] = None,
    apenas_ativos: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista agentes cadastrados com busca por matrícula, nome ou órgão."""
    service = AgenteService(db)
    items, total = service.list_agentes(
        skip=skip,
        limit=limit,
        tipo=tipo,
        situacao=situacao,
        orgao=orgao,
        busca=busca,
        apenas_ativos=apenas_ativos
    )
    return AgenteListResponse(
        total=total,
        items=[AgenteResponse.model_validate(a) for e, a in enumerate(items)]
    )


@router.get("/filtros", summary="Opções Dinâmicas para Filtros de Agentes")
def get_filters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna listas distintas de órgãos e situações para popular filtros."""
    service = AgenteService(db)
    return service.get_filter_options()


@router.post(
    "",
    response_model=AgenteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Agente"
)
def create_agente(
    data: AgenteCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Cadastra um novo agente no sistema."""
    service = AgenteService(db)
    new_ag = service.create_agente(data)
    return AgenteResponse.model_validate(new_ag)


@router.get("/{agente_id}", response_model=AgenteResponse, summary="Detalhes do Agente")
def get_agente(
    agente_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna os dados completos do agente pelo ID."""
    service = AgenteService(db)
    ag = service.get_agente(agente_id)
    return AgenteResponse.model_validate(ag)


@router.put("/{agente_id}", response_model=AgenteResponse, summary="Atualizar Agente")
def update_agente(
    agente_id: int,
    data: AgenteUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Atualiza dados do agente."""
    service = AgenteService(db)
    updated = service.update_agente(agente_id, data)
    return AgenteResponse.model_validate(updated)


@router.delete("/{agente_id}", response_model=AgenteResponse, summary="Desativar Agente (Soft Delete)")
def delete_agente(
    agente_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Desativa um agente no sistema."""
    service = AgenteService(db)
    deleted = service.delete_agente(agente_id)
    return AgenteResponse.model_validate(deleted)
