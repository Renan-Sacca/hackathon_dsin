from datetime import datetime, timedelta, timezone, date
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session
from app.models.agente import Agente, AgenteSituacao
from app.models.equipamento import (
    Equipamento,
    EquipamentoSituacao,
    EquipamentoTipo,
    ManutencaoTipo,
)
from app.models.historico_equipamento import HistoricoEquipamento
from app.models.ocorrencia import Ocorrencia, OcorrenciaSeveridade


class PredictiveRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_equipamentos(self) -> List[Equipamento]:
        """Recupera todos os equipamentos ativos."""
        return self.db.execute(
            select(Equipamento).where(Equipamento.ativo.is_(True))
        ).scalars().all()

    def get_equipamento_by_id(self, equipamento_id: int) -> Optional[Equipamento]:
        """Recupera um equipamento específico por ID."""
        return self.db.execute(
            select(Equipamento).where(Equipamento.id == equipamento_id)
        ).scalar_one_or_none()

    def get_historico_equipamento(self, equipamento_id: int) -> List[HistoricoEquipamento]:
        """Recupera histórico cronológico de transições de um equipamento."""
        return self.db.execute(
            select(HistoricoEquipamento)
            .where(HistoricoEquipamento.equipamento_id == equipamento_id)
            .order_by(HistoricoEquipamento.data_mudanca.asc())
        ).scalars().all()

    def get_falhas_historicas(self, dias: int = 180) -> List[HistoricoEquipamento]:
        """Recupera todos os registros de entrada em falha no período especificado."""
        data_limite = datetime.now(timezone.utc) - timedelta(days=dias)
        return self.db.execute(
            select(HistoricoEquipamento)
            .where(
                HistoricoEquipamento.situacao_nova.in_([
                    EquipamentoSituacao.MAU_FUNCIONAMENTO,
                    EquipamentoSituacao.FURTADO
                ]),
                HistoricoEquipamento.data_mudanca >= data_limite
            )
            .order_by(HistoricoEquipamento.data_mudanca.asc())
        ).scalars().all()

    def get_ocorrencias_agrupadas(self, dias: int = 180) -> List[Dict[str, Any]]:
        """Recupera ocorrências agrupadas por bairro e período do dia com contagem ponderada por severidade."""
        data_limite = datetime.now(timezone.utc) - timedelta(days=dias)
        ocorrencias = self.db.execute(
            select(Ocorrencia).where(Ocorrencia.data_hora >= data_limite)
        ).scalars().all()

        return [
            {
                "id": o.id,
                "tipo": o.tipo.value,
                "severidade": o.severidade.value,
                "bairro": o.localizacao_bairro,
                "rua": o.localizacao_rua,
                "latitude": o.latitude,
                "longitude": o.longitude,
                "data_hora": o.data_hora,
                "periodo_dia": o.periodo_dia,
                "equipamento_id": o.equipamento_id,
            }
            for o in ocorrencias
        ]

    def get_agentes_ativos(self) -> List[Agente]:
        """Recupera agentes ativos cadastrados com coordenadas."""
        return self.db.execute(
            select(Agente).where(
                Agente.ativo.is_(True),
                Agente.situacao == AgenteSituacao.EM_ATIVIDADE
            )
        ).scalars().all()

    def get_manutencoes_com_custo(self, dias: int = 180) -> List[HistoricoEquipamento]:
        """Recupera manutenções com custo financeiro registrado."""
        data_limite = datetime.now(timezone.utc) - timedelta(days=dias)
        return self.db.execute(
            select(HistoricoEquipamento)
            .where(
                HistoricoEquipamento.custo_manutencao > 0,
                HistoricoEquipamento.data_mudanca >= data_limite
            )
            .order_by(HistoricoEquipamento.data_mudanca.asc())
        ).scalars().all()

    def get_equipamentos_nao_instalados(self) -> List[Equipamento]:
        """Recupera equipamentos com situação 'nao_instalado'."""
        return self.db.execute(
            select(Equipamento).where(
                Equipamento.ativo.is_(True),
                Equipamento.situacao == EquipamentoSituacao.NAO_INSTALADO
            )
        ).scalars().all()
