from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.agente import Agente, AgenteSituacao, AgenteTipo
from app.models.equipamento import (
    Equipamento,
    EquipamentoSituacao,
    EquipamentoTipo,
    ManutencaoTipo,
)


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_kpis(self) -> Dict[str, Any]:
        """Calcula os indicadores-chave de desempenho do inventário urbano."""
        total_equipamentos = self.db.scalar(
            select(func.count(Equipamento.id)).where(Equipamento.ativo.is_(True))
        ) or 0

        operacionais = self.db.scalar(
            select(func.count(Equipamento.id)).where(
                Equipamento.ativo.is_(True),
                Equipamento.situacao == EquipamentoSituacao.OPERACIONAL
            )
        ) or 0

        indisponiveis = self.db.scalar(
            select(func.count(Equipamento.id)).where(
                Equipamento.ativo.is_(True),
                Equipamento.situacao.in_([
                    EquipamentoSituacao.MAU_FUNCIONAMENTO,
                    EquipamentoSituacao.FURTADO,
                    EquipamentoSituacao.DESATIVADO
                ])
            )
        ) or 0

        manutencao_imediata = self.db.scalar(
            select(func.count(Equipamento.id)).where(
                Equipamento.ativo.is_(True),
                Equipamento.manutencao_tipo == ManutencaoTipo.IMEDIATA
            )
        ) or 0

        hoje = date.today()
        proximos_7_dias = hoje + timedelta(days=7)
        manutencao_agendada_7d = self.db.scalar(
            select(func.count(Equipamento.id)).where(
                Equipamento.ativo.is_(True),
                Equipamento.proxima_manutencao.is_not(None),
                Equipamento.proxima_manutencao >= hoje,
                Equipamento.proxima_manutencao <= proximos_7_dias
            )
        ) or 0

        agentes_em_atividade = self.db.scalar(
            select(func.count(Agente.id)).where(
                Agente.ativo.is_(True),
                Agente.situacao == AgenteSituacao.EM_ATIVIDADE
            )
        ) or 0

        total_agentes = self.db.scalar(
            select(func.count(Agente.id)).where(Agente.ativo.is_(True))
        ) or 0

        percentual_disponibilidade = (
            round((operacionais / total_equipamentos) * 100, 1)
            if total_equipamentos > 0
            else 0.0
        )

        # Contagem por tipo
        tipo_counts_rows = self.db.execute(
            select(Equipamento.tipo, func.count(Equipamento.id))
            .where(Equipamento.ativo.is_(True))
            .group_by(Equipamento.tipo)
        ).all()
        por_tipo = {r[0].value if hasattr(r[0], 'value') else str(r[0]): r[1] for r in tipo_counts_rows}

        # Contagem por situacao
        situacao_counts_rows = self.db.execute(
            select(Equipamento.situacao, func.count(Equipamento.id))
            .where(Equipamento.ativo.is_(True))
            .group_by(Equipamento.situacao)
        ).all()
        por_situacao = {r[0].value if hasattr(r[0], 'value') else str(r[0]): r[1] for r in situacao_counts_rows}

        return {
            "total_equipamentos": total_equipamentos,
            "operacionais": operacionais,
            "indisponiveis": indisponiveis,
            "percentual_disponibilidade": percentual_disponibilidade,
            "manutencao_imediata": manutencao_imediata,
            "manutencao_agendada_7d": manutencao_agendada_7d,
            "agentes_em_atividade": agentes_em_atividade,
            "total_agentes": total_agentes,
            "por_tipo": por_tipo,
            "por_situacao": por_situacao,
        }

    def get_map_items(
        self,
        tipo: Optional[str] = None,
        situacao: Optional[str] = None,
        bairro: Optional[str] = None,
        orgao: Optional[str] = None,
        busca: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Recupera equipamentos e agentes formatados para renderização no Leaflet."""
        # Query Equipamentos
        eq_stmt = select(Equipamento).where(Equipamento.ativo.is_(True))
        if tipo:
            eq_stmt = eq_stmt.where(Equipamento.tipo == tipo)
        if situacao:
            eq_stmt = eq_stmt.where(Equipamento.situacao == situacao)
        if bairro:
            eq_stmt = eq_stmt.where(Equipamento.localizacao_bairro == bairro)
        if orgao:
            eq_stmt = eq_stmt.where(Equipamento.orgao_responsavel == orgao)
        if busca:
            t = f"%{busca.strip()}%"
            eq_stmt = eq_stmt.where(
                or_(
                    Equipamento.numero_serie.ilike(t),
                    Equipamento.marca.ilike(t),
                    Equipamento.modelo.ilike(t),
                    Equipamento.localizacao_rua.ilike(t),
                    Equipamento.localizacao_bairro.ilike(t),
                )
            )

        equipamentos = self.db.execute(eq_stmt).scalars().all()

        eq_list = []
        for e in equipamentos:
            # Identifica criticidade do equipamento
            criticidade = "normal"
            if e.situacao in (EquipamentoSituacao.MAU_FUNCIONAMENTO, EquipamentoSituacao.FURTADO):
                criticidade = "critico"
            elif e.manutencao_tipo == ManutencaoTipo.IMEDIATA:
                criticidade = "urgente"
            elif e.proxima_manutencao and (e.proxima_manutencao - date.today()).days <= 3:
                criticidade = "atencao"

            eq_list.append({
                "id": e.id,
                "numero_serie": e.numero_serie,
                "marca": e.marca,
                "modelo": e.modelo,
                "tipo": e.tipo.value,
                "situacao": e.situacao.value,
                "criticidade": criticidade,
                "manutencao_tipo": e.manutencao_tipo.value,
                "proxima_manutencao": str(e.proxima_manutencao) if e.proxima_manutencao else None,
                "localizacao_rua": e.localizacao_rua,
                "localizacao_bairro": e.localizacao_bairro,
                "localizacao_referencia": e.localizacao_referencia,
                "latitude": e.latitude,
                "longitude": e.longitude,
                "orgao_responsavel": e.orgao_responsavel,
                "propriedades": [
                    {"chave": p.chave, "valor": p.valor} for p in (e.propriedades or [])
                ],
            })

        # Query Agentes
        ag_stmt = select(Agente).where(
            Agente.ativo.is_(True),
            Agente.latitude.is_not(None),
            Agente.longitude.is_not(None)
        )
        if orgao:
            ag_stmt = ag_stmt.where(Agente.orgao == orgao)
        if busca:
            t = f"%{busca.strip()}%"
            ag_stmt = ag_stmt.where(
                or_(
                    Agente.nome.ilike(t),
                    Agente.matricula.ilike(t),
                    Agente.orgao.ilike(t),
                )
            )

        agentes = self.db.execute(ag_stmt).scalars().all()
        ag_list = []
        for a in agentes:
            ag_list.append({
                "id": a.id,
                "nome": a.nome,
                "matricula": a.matricula,
                "tipo": a.tipo.value,
                "orgao": a.orgao,
                "telefone": a.telefone,
                "situacao": a.situacao.value,
                "latitude": a.latitude,
                "longitude": a.longitude,
            })

        return {
            "equipamentos": eq_list,
            "agentes": ag_list
        }

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Gera lista priorizada de alertas em tempo real classificados por criticidade."""
        hoje = date.today()
        limite_atencao = hoje + timedelta(days=3)

        equipamentos = self.db.execute(
            select(Equipamento).where(Equipamento.ativo.is_(True))
        ).scalars().all()

        alertas = []
        for e in equipamentos:
            if e.situacao == EquipamentoSituacao.MAU_FUNCIONAMENTO:
                alertas.append({
                    "equipamento_id": e.id,
                    "numero_serie": e.numero_serie,
                    "tipo": e.tipo.value,
                    "bairro": e.localizacao_bairro,
                    "rua": e.localizacao_rua,
                    "latitude": e.latitude,
                    "longitude": e.longitude,
                    "severidade": "CRITICO",
                    "mensagem": f"Equipamento {e.numero_serie} em MAU FUNCIONAMENTO.",
                    "prioridade": 1
                })
            elif e.situacao == EquipamentoSituacao.FURTADO:
                alertas.append({
                    "equipamento_id": e.id,
                    "numero_serie": e.numero_serie,
                    "tipo": e.tipo.value,
                    "bairro": e.localizacao_bairro,
                    "rua": e.localizacao_rua,
                    "latitude": e.latitude,
                    "longitude": e.longitude,
                    "severidade": "CRITICO",
                    "mensagem": f"ALERTA POLICIAL: Equipamento {e.numero_serie} marcado como FURTADO.",
                    "prioridade": 1
                })
            elif e.manutencao_tipo == ManutencaoTipo.IMEDIATA:
                alertas.append({
                    "equipamento_id": e.id,
                    "numero_serie": e.numero_serie,
                    "tipo": e.tipo.value,
                    "bairro": e.localizacao_bairro,
                    "rua": e.localizacao_rua,
                    "latitude": e.latitude,
                    "longitude": e.longitude,
                    "severidade": "URGENTE",
                    "mensagem": f"Manutenção imediata pendente no dispositivo {e.numero_serie}.",
                    "prioridade": 2
                })
            elif e.proxima_manutencao and hoje <= e.proxima_manutencao <= limite_atencao:
                dias = (e.proxima_manutencao - hoje).days
                alertas.append({
                    "equipamento_id": e.id,
                    "numero_serie": e.numero_serie,
                    "tipo": e.tipo.value,
                    "bairro": e.localizacao_bairro,
                    "rua": e.localizacao_rua,
                    "latitude": e.latitude,
                    "longitude": e.longitude,
                    "severidade": "ATENCAO",
                    "mensagem": f"Manutenção agendada para daqui a {dias} dia(s) ({e.proxima_manutencao}).",
                    "prioridade": 3
                })

        # Ordena por prioridade (1=CRITICO, 2=URGENTE, 3=ATENCAO)
        alertas.sort(key=lambda x: x["prioridade"])
        return alertas

    def get_regions_health(self) -> List[Dict[str, Any]]:
        """Agrupa equipamentos por bairro e calcula o índice de saúde (% operacional)."""
        bairros = self.db.execute(
            select(Equipamento.localizacao_bairro)
            .where(Equipamento.ativo.is_(True))
            .distinct()
        ).scalars().all()

        regioes = []
        for b in bairros:
            total = self.db.scalar(
                select(func.count(Equipamento.id)).where(
                    Equipamento.ativo.is_(True),
                    Equipamento.localizacao_bairro == b
                )
            ) or 0

            operacionais = self.db.scalar(
                select(func.count(Equipamento.id)).where(
                    Equipamento.ativo.is_(True),
                    Equipamento.localizacao_bairro == b,
                    Equipamento.situacao == EquipamentoSituacao.OPERACIONAL
                )
            ) or 0

            problemas = self.db.scalar(
                select(func.count(Equipamento.id)).where(
                    Equipamento.ativo.is_(True),
                    Equipamento.localizacao_bairro == b,
                    Equipamento.situacao.in_([
                        EquipamentoSituacao.MAU_FUNCIONAMENTO,
                        EquipamentoSituacao.FURTADO
                    ])
                )
            ) or 0

            # Latitude e longitude médias do bairro para facilitar pan no mapa
            coords = self.db.execute(
                select(
                    func.avg(Equipamento.latitude),
                    func.avg(Equipamento.longitude)
                ).where(
                    Equipamento.ativo.is_(True),
                    Equipamento.localizacao_bairro == b
                )
            ).first()

            pct = round((operacionais / total) * 100, 1) if total > 0 else 0.0

            regioes.append({
                "bairro": b,
                "total": total,
                "operacionais": operacionais,
                "problemas": problemas,
                "percentual_saude": pct,
                "lat": float(coords[0]) if coords and coords[0] else None,
                "lon": float(coords[1]) if coords and coords[1] else None,
            })

        # Ordena por criticidade (menor percentual de saúde e maior número de problemas no topo)
        regioes.sort(key=lambda r: (r["percentual_saude"], -r["problemas"]))
        return regioes
