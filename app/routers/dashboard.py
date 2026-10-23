from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Central de Operações / Dashboard"])


@router.get("/metricas", summary="Obter KPIs e Indicadores Gerais")
def get_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retorna os indicadores operacionais da cidade (total, operacionais, indisponíveis, disponibilidade %, agentes)."""
    service = DashboardService(db)
    return service.get_metrics()


@router.get("/mapa", summary="Obter Dados Geográficos para o Mapa Interativo")
def get_map(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de equipamento"),
    situacao: Optional[str] = Query(None, description="Filtrar por situação operacional"),
    bairro: Optional[str] = Query(None, description="Filtrar por bairro"),
    orgao: Optional[str] = Query(None, description="Filtrar por órgão responsável"),
    busca: Optional[str] = Query(None, description="Busca textual em número de série, marca ou logradouro"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retorna equipamentos e agentes filtrados para renderização no mapa Leaflet."""
    service = DashboardService(db)
    return service.get_map_data(
        tipo=tipo,
        situacao=situacao,
        bairro=bairro,
        orgao=orgao,
        busca=busca
    )


@router.get("/alertas", summary="Obter Lista de Alertas Ativos e Priorizados")
def get_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Retorna lista de alertas classificados em CRÍTICO, URGENTE e ATENÇÃO."""
    service = DashboardService(db)
    return service.get_alerts()


@router.get("/regioes", summary="Obter Indicadores de Saúde por Região/Bairro")
def get_regions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Retorna o percentual de disponibilidade e problemas de cada bairro da cidade."""
    service = DashboardService(db)
    return service.get_regions_health()
