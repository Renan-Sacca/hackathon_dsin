from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.equipamento import EquipamentoSituacao, EquipamentoTipo, ManutencaoTipo
from app.models.user import User
from app.schemas.equipamento import (
    EquipamentoCreate,
    EquipamentoResponse,
    EquipamentoUpdate,
    HistoricoManutencaoCreate,
    HistoricoManutencaoResponse,
)
from app.services.equipamento_service import EquipamentoService

router = APIRouter(prefix="/api/equipamentos", tags=["Equipamentos"])


class EquipamentoListResponse(BaseModel):
    total: int
    items: List[EquipamentoResponse]


@router.get("", response_model=EquipamentoListResponse, summary="Listar Equipamentos com Filtros")
def list_equipamentos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    tipo: Optional[EquipamentoTipo] = None,
    situacao: Optional[EquipamentoSituacao] = None,
    bairro: Optional[str] = None,
    orgao: Optional[str] = None,
    manutencao_tipo: Optional[ManutencaoTipo] = None,
    busca: Optional[str] = None,
    apenas_ativos: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista equipamentos cadastrados com suporte a busca textual e filtros combinados."""
    service = EquipamentoService(db)
    items, total = service.list_equipamentos(
        skip=skip,
        limit=limit,
        tipo=tipo,
        situacao=situacao,
        bairro=bairro,
        orgao=orgao,
        manutencao_tipo=manutencao_tipo,
        busca=busca,
        apenas_ativos=apenas_ativos
    )
    return EquipamentoListResponse(
        total=total,
        items=[EquipamentoResponse.model_validate(e) for e in items]
    )


@router.get("/filtros", summary="Opções Dinâmicas para Filtros")
def get_filters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna listas distintas de bairros, órgãos e enums para popular filtros."""
    service = EquipamentoService(db)
    return service.get_filter_options()


@router.post(
    "",
    response_model=EquipamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Equipamento"
)
def create_equipamento(
    data: EquipamentoCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Cadastra um novo equipamento com propriedades dinâmicas e validação de regras de negócio."""
    service = EquipamentoService(db)
    new_eq = service.create_equipamento(data)
    return EquipamentoResponse.model_validate(new_eq)


@router.get("/{equipamento_id}", response_model=EquipamentoResponse, summary="Detalhes do Equipamento")
def get_equipamento(
    equipamento_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna os dados completos do equipamento pelo ID."""
    service = EquipamentoService(db)
    eq = service.get_equipamento(equipamento_id)
    return EquipamentoResponse.model_validate(eq)


@router.put("/{equipamento_id}", response_model=EquipamentoResponse, summary="Atualizar Equipamento")
def update_equipamento(
    equipamento_id: int,
    data: EquipamentoUpdate,
    force_reactivation: bool = Query(False, description="Forçar retorno de furtado/desativado para operacional"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Atualiza dados do equipamento com validação de transições de situação."""
    service = EquipamentoService(db)
    updated = service.update_equipamento(equipamento_id, data, force_reactivation)
    return EquipamentoResponse.model_validate(updated)


@router.delete("/{equipamento_id}", response_model=EquipamentoResponse, summary="Desativar Equipamento (Soft Delete)")
def delete_equipamento(
    equipamento_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Desativa um equipamento mantendo integridade e histórico."""
    service = EquipamentoService(db)
    deleted = service.delete_equipamento(equipamento_id)
    return EquipamentoResponse.model_validate(deleted)


@router.get(
    "/{equipamento_id}/historico",
    response_model=List[HistoricoManutencaoResponse],
    summary="Histórico de Manutenções do Equipamento"
)
def get_historico_equipamento(
    equipamento_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna o histórico completo de manutenções, mudanças de situação, custos e tempo de inatividade."""
    service = EquipamentoService(db)
    historico = service.get_historico(equipamento_id)
    return [HistoricoManutencaoResponse.model_validate(h) for h in historico]


@router.post(
    "/{equipamento_id}/historico",
    response_model=HistoricoManutencaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar Nova Intervenção / Manutenção"
)
def create_historico_manutencao(
    equipamento_id: int,
    data: HistoricoManutencaoCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Registra uma intervenção técnica de manutenção no equipamento, atualizando a situação operacional."""
    service = EquipamentoService(db)
    novo_historico = service.add_historico(equipamento_id, data)
    return HistoricoManutencaoResponse.model_validate(novo_historico)

