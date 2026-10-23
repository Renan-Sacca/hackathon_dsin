from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DashboardRepository(db)

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna todos os KPIs agregados para o dashboard executivo."""
        return self.repo.get_kpis()

    def get_map_data(
        self,
        tipo: Optional[str] = None,
        situacao: Optional[str] = None,
        bairro: Optional[str] = None,
        orgao: Optional[str] = None,
        busca: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Retorna dados de equipamentos e agentes prontos para plotagem no mapa."""
        return self.repo.get_map_items(
            tipo=tipo,
            situacao=situacao,
            bairro=bairro,
            orgao=orgao,
            busca=busca
        )

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Retorna lista de alertas priorizada por criticidade."""
        return self.repo.get_active_alerts()

    def get_regions_health(self) -> List[Dict[str, Any]]:
        """Retorna lista de bairros classificados por integridade operacional."""
        return self.repo.get_regions_health()
