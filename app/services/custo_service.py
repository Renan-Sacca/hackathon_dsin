from datetime import datetime, timedelta, timezone, date
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models.equipamento import Equipamento, EquipamentoSituacao, EquipamentoTipo
from app.repositories.predictive_repository import PredictiveRepository
from app.services.predictive_service import PredictiveService


class CustoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PredictiveRepository(db)
        self.pred_service = PredictiveService(db)

    def projetar_custos_manutencao(self, dias_historico: int = 180) -> Dict[str, Any]:
        """Projeta o custo esperado de manutenção para os próximos 30, 60 e 90 dias,

        cruzando frequência histórica, custos reais acumulados e probabilidade de novas falhas.
        """
        manutencoes = self.repo.get_manutencoes_com_custo(dias=dias_historico)
        equipamentos = self.repo.get_all_equipamentos()
        previsoes_falhas = self.pred_service.prever_falhas_equipamentos()
        now = datetime.now(timezone.utc)
        hoje = date.today()

        # 1. Total real gasto no período histórico
        custo_real_total = sum(m.custo_manutencao for m in manutencoes)

        # 2. Histórico mensal real (últimos 6 meses)
        meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        gastos_por_mes: Dict[str, float] = {}

        for m in manutencoes:
            dt = m.data_mudanca
            chave_mes = f"{meses_nomes[dt.month - 1]}/{str(dt.year)[2:]}"
            gastos_por_mes[chave_mes] = gastos_por_mes.get(chave_mes, 0.0) + m.custo_manutencao

        # Custos médios por tipo de equipamento
        custos_por_tipo: Dict[str, List[float]] = {}
        eq_map = {e.id: e for e in equipamentos}

        for m in manutencoes:
            eq = eq_map.get(m.equipamento_id)
            if eq:
                t = eq.tipo.value
                if t not in custos_por_tipo:
                    custos_por_tipo[t] = []
                custos_por_tipo[t].append(m.custo_manutencao)

        custo_medio_por_tipo: Dict[str, float] = {
            t: (sum(valores) / len(valores)) if valores else 800.0
            for t, valores in custos_por_tipo.items()
        }

        # Custo médio diário histórico
        dias_validos = max(30, dias_historico)
        custo_diario_historico = custo_real_total / dias_validos

        # 3. Projeção Baseada em Falhas Previstas (Preditivo Estocástico)
        custo_falhas_30d = 0.0
        custo_falhas_60d = 0.0
        custo_falhas_90d = 0.0

        for p in previsoes_falhas:
            tipo_eq = p["tipo"]
            custo_reparo = custo_medio_por_tipo.get(tipo_eq, 950.0)
            prob = p["probabilidade_falha_percentual"] / 100.0
            valor_esperado = custo_reparo * prob

            dias_prev = p["dias_restantes"]
            if dias_prev <= 30:
                custo_falhas_30d += valor_esperado
                custo_falhas_60d += valor_esperado
                custo_falhas_90d += valor_esperado
            elif dias_prev <= 60:
                custo_falhas_60d += valor_esperado
                custo_falhas_90d += valor_esperado
            elif dias_prev <= 90:
                custo_falhas_90d += valor_esperado

        # 4. Projeção Baseada em Manutenções Preventivas Agendadas
        custo_preventivo_30d = 0.0
        custo_preventivo_60d = 0.0
        custo_preventivo_90d = 0.0

        for eq in equipamentos:
            if eq.proxima_manutencao:
                dias_ate = (eq.proxima_manutencao - hoje).days
                custo_prev_estimado = custo_medio_por_tipo.get(eq.tipo.value, 600.0) * 0.6  # preventiva é mais barata que corretiva

                if 0 <= dias_ate <= 30:
                    custo_preventivo_30d += custo_prev_estimado
                    custo_preventivo_60d += custo_prev_estimado
                    custo_preventivo_90d += custo_prev_estimado
                elif 30 < dias_ate <= 60:
                    custo_preventivo_60d += custo_prev_estimado
                    custo_preventivo_90d += custo_prev_estimado
                elif 60 < dias_ate <= 90:
                    custo_preventivo_90d += custo_prev_estimado

        # Adicionar margem de desgaste natural residual
        projecao_30d = round(custo_falhas_30d + custo_preventivo_30d + (custo_diario_historico * 10), 2)
        projecao_60d = round(custo_falhas_60d + custo_preventivo_60d + (custo_diario_historico * 22), 2)
        projecao_90d = round(custo_falhas_90d + custo_preventivo_90d + (custo_diario_historico * 35), 2)

        # Montar timeline histórica + projetada para gráfico
        mes_atual = now.month
        ano_atual = now.year

        labels_proj = []
        for i in range(1, 4):
            m_futuro = (mes_atual + i - 1) % 12 + 1
            a_futuro = ano_atual if (mes_atual + i <= 12) else ano_atual + 1
            labels_proj.append(f"{meses_nomes[m_futuro - 1]}/{str(a_futuro)[2:]} (Proj)")

        projecao_mensal_futura = [
            round(projecao_30d, 2),
            round(max(0.0, projecao_60d - projecao_30d), 2),
            round(max(0.0, projecao_90d - projecao_60d), 2)
        ]

        return {
            "periodo_historico_dias": dias_historico,
            "custo_real_acumulado": round(custo_real_total, 2),
            "media_mensal_real": round(custo_real_total / (dias_validos / 30.0), 2),
            "projecao_30_dias": projecao_30d,
            "projecao_60_dias": projecao_60d,
            "projecao_90_dias": projecao_90d,
            "detalhamento_30d": {
                "corretivo_falhas_esperadas": round(custo_falhas_30d, 2),
                "preventivo_agendado": round(custo_preventivo_30d, 2),
                "manutencoes_rotina": round(projecao_30d - custo_falhas_30d - custo_preventivo_30d, 2)
            },
            "grafico_comparativo": {
                "meses_reais": list(gastos_por_mes.keys()),
                "valores_reais": [round(v, 2) for v in gastos_por_mes.values()],
                "meses_projetados": labels_proj,
                "valores_projetados": projecao_mensal_futura
            },
            "explicacao": (
                f"Projeção calculada com base em R$ {custo_real_total:,.2f} investidos nos últimos {dias_historico} dias. "
                f"Para os próximos 30 dias, estima-se R$ {projecao_30d:,.2f} considerando as falhas preditas por MTBF "
                f"e manutenções preventivas programadas."
            )
        }
