from datetime import datetime, timedelta, timezone, date
import math
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.equipamento import (
    Equipamento,
    EquipamentoSituacao,
    EquipamentoTipo,
    ManutencaoTipo,
)
from app.models.historico_equipamento import HistoricoEquipamento
from app.repositories.predictive_repository import PredictiveRepository


class PredictiveService:
    def __init__(self, db: Session):
        self.repo = PredictiveRepository(db)

    # -------------------------------------------------------------------------
    # 1. Risco por Região e Período do Dia (P3-PRED-01 / P3-TEST-01)
    # -------------------------------------------------------------------------
    def calcular_risco_regioes(self, dias: int = 180) -> List[Dict[str, Any]]:
        """Calcula o índice de risco (0 a 100) para cada bairro e período do dia."""
        ocorrencias = self.repo.get_ocorrencias_agrupadas(dias=dias)
        equipamentos = self.repo.get_all_equipamentos()
        falhas = self.repo.get_falhas_historicas(dias=dias)

        # Pesos de severidade para cálculo
        peso_severidade = {
            "baixa": 1.0,
            "media": 2.5,
            "alta": 5.0,
            "critica": 10.0
        }

        # Agrupar ocorrências por (bairro, periodo)
        dados_regioes: Dict[str, Dict[str, Any]] = {}

        # Mapear coordenadas médias de cada bairro
        coords_bairros: Dict[str, List[float]] = {}
        for eq in equipamentos:
            if eq.localizacao_bairro not in coords_bairros:
                coords_bairros[eq.localizacao_bairro] = [eq.latitude, eq.longitude]

        # Inicializar dados para bairros conhecidos
        bairros_conhecidos = list(set([e.localizacao_bairro for e in equipamentos] + [o["bairro"] for o in ocorrencias]))
        for b in bairros_conhecidos:
            coords = coords_bairros.get(b, [-22.2139, -49.9458])
            dados_regioes[b] = {
                "bairro": b,
                "latitude": coords[0],
                "longitude": coords[1],
                "periodos": {
                    "manha": {"pontuacao": 0.0, "total_ocorrencias": 0, "criticas": 0},
                    "tarde": {"pontuacao": 0.0, "total_ocorrencias": 0, "criticas": 0},
                    "noite": {"pontuacao": 0.0, "total_ocorrencias": 0, "criticas": 0},
                    "madrugada": {"pontuacao": 0.0, "total_ocorrencias": 0, "criticas": 0},
                },
                "total_falhas_equipamentos": 0,
            }

        # Somar ocorrências
        for o in ocorrencias:
            b = o["bairro"]
            p = o["periodo_dia"]
            if b in dados_regioes and p in dados_regioes[b]["periodos"]:
                pts = peso_severidade.get(o["severidade"], 1.0)
                dados_regioes[b]["periodos"][p]["pontuacao"] += pts
                dados_regioes[b]["periodos"][p]["total_ocorrencias"] += 1
                if o["severidade"] in ("alta", "critica"):
                    dados_regioes[b]["periodos"][p]["criticas"] += 1

        # Mapear falhas de equipamentos por bairro
        eq_map = {e.id: e.localizacao_bairro for e in equipamentos}
        for f in falhas:
            bairro_eq = eq_map.get(f.equipamento_id)
            if bairro_eq and bairro_eq in dados_regioes:
                dados_regioes[bairro_eq]["total_falhas_equipamentos"] += 1

        resultado = []
        for b, data in dados_regioes.items():
            # Achar período de maior risco
            max_pts = 0.0
            p_critico = "tarde"
            pontuacoes_normalizadas = {}

            # Fator de escala: normaliza pontuação de 0 a 100
            for p, p_data in data["periodos"].items():
                # Pontuação base de ocorrências + contribuição de falhas da região
                pts_total = p_data["pontuacao"] + (data["total_falhas_equipamentos"] * 1.5)
                # Escala logarítmica/ponderada para 0 - 100
                score = min(100.0, round(pts_total * 2.2, 1))
                pontuacoes_normalizadas[p] = {
                    "score_risco": score,
                    "total_ocorrencias": p_data["total_ocorrencias"],
                    "criticas": p_data["criticas"]
                }
                if score > max_pts:
                    max_pts = score
                    p_critico = p

            # Nível geral
            nivel = "BAIXO"
            if max_pts >= 70:
                nivel = "CRITICO"
            elif max_pts >= 45:
                nivel = "ALTO"
            elif max_pts >= 25:
                nivel = "MODERADO"

            resultado.append({
                "bairro": b,
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "score_geral": max_pts,
                "nivel_risco": nivel,
                "periodo_mais_critico": p_critico,
                "detalhes_periodos": pontuacoes_normalizadas,
                "total_falhas_equipamentos": data["total_falhas_equipamentos"],
                "explicacao": (
                    f"Índice baseado em {sum(p['total_ocorrencias'] for p in data['periodos'].values())} ocorrências "
                    f"e {data['total_falhas_equipamentos']} falhas registradas nos últimos {dias} dias. "
                    f"O período de maior risco é a {p_critico} com score {max_pts}/100."
                )
            })

        # Ordenar pelos bairros de maior risco no topo
        resultado.sort(key=lambda x: x["score_geral"], reverse=True)
        return resultado

    # -------------------------------------------------------------------------
    # 2. Previsão de Falhas de Equipamentos (P3-PRED-01 / P3-TEST-02)
    # -------------------------------------------------------------------------
    def prever_falhas_equipamentos(self) -> List[Dict[str, Any]]:
        """Identifica equipamentos com histórico de falhas recorrentes e calcula probabilidade e data prevista da próxima falha."""
        equipamentos = self.repo.get_all_equipamentos()
        now = datetime.now(timezone.utc)
        previsoes = []

        for eq in equipamentos:
            if eq.situacao == EquipamentoSituacao.NAO_INSTALADO:
                continue

            historico = self.repo.get_historico_equipamento(eq.id)
            # Filtrar eventos de falha (entrada em mau funcionamento ou furtado)
            eventos_falha = [
                h for h in historico
                if h.situacao_nova in (EquipamentoSituacao.MAU_FUNCIONAMENTO, EquipamentoSituacao.FURTADO)
            ]

            total_falhas = len(eventos_falha)
            if total_falhas < 2:
                # Se teve poucas falhas, calcula risco padrão por idade/tipo
                continue

            # Calcular MTBF (Mean Time Between Failures) em dias
            intervalos_dias = []
            for i in range(1, total_falhas):
                delta = eventos_falha[i].data_mudanca - eventos_falha[i - 1].data_mudanca
                intervalos_dias.append(max(1.0, delta.total_seconds() / 86400.0))

            mtbf_medio_dias = sum(intervalos_dias) / len(intervalos_dias)
            ultima_falha = eventos_falha[-1].data_mudanca
            if ultima_falha.tzinfo is None:
                ultima_falha = ultima_falha.replace(tzinfo=timezone.utc)

            dias_desde_ultima_falha = (now - ultima_falha).total_seconds() / 86400.0

            # Probabilidade baseada no ciclo MTBF (modelo de confiabilidade exponencial Weibull aproximado)
            razao_ciclo = dias_desde_ultima_falha / max(mtbf_medio_dias, 1.0)
            # Probabilidade aumenta conforme se aproxima ou passa do MTBF
            probabilidade_pct = min(98.5, round((1.0 - math.exp(-pow(razao_ciclo, 1.8))) * 100.0, 1))

            # Previsão da data da próxima falha
            dias_restantes_estimados = max(1, round(mtbf_medio_dias - dias_desde_ultima_falha))
            data_prevista_falha = (now + timedelta(days=dias_restantes_estimados)).date()

            # Severidade da previsão
            if probabilidade_pct >= 75:
                grau_urgencia = "CRITICA"
            elif probabilidade_pct >= 50:
                grau_urgencia = "ALTA"
            else:
                grau_urgencia = "MEDIA"

            previsoes.append({
                "equipamento_id": eq.id,
                "numero_serie": eq.numero_serie,
                "tipo": eq.tipo.value,
                "marca": eq.marca,
                "modelo": eq.modelo,
                "localizacao_bairro": eq.localizacao_bairro,
                "localizacao_rua": eq.localizacao_rua,
                "latitude": eq.latitude,
                "longitude": eq.longitude,
                "situacao_atual": eq.situacao.value,
                "total_falhas_registradas": total_falhas,
                "mtbf_dias": round(mtbf_medio_dias, 1),
                "dias_desde_ultima_falha": round(dias_desde_ultima_falha, 1),
                "probabilidade_falha_percentual": probabilidade_pct,
                "data_prevista_proxima_falha": str(data_prevista_falha),
                "dias_restantes": dias_restantes_estimados,
                "grau_urgencia": grau_urgencia,
                "explicacao": (
                    f"Apresentou {total_falhas} falhas no histórico com intervalo médio de {round(mtbf_medio_dias, 1)} dias (MTBF). "
                    f"A última falha ocorreu há {round(dias_desde_ultima_falha, 1)} dias. "
                    f"Probabilidade estimada de nova falha em até {dias_restantes_estimados} dias é de {probabilidade_pct}%."
                )
            })

        # Ordenar por probabilidade de falha decrescente
        previsoes.sort(key=lambda x: x["probabilidade_falha_percentual"], reverse=True)
        return previsoes

    # -------------------------------------------------------------------------
    # 3. Alertas Preventivos e Anomalias (P3-PRED-01 / P3-TEST-03)
    # -------------------------------------------------------------------------
    def gerar_alertas_preventivos(self) -> List[Dict[str, Any]]:
        """Gera alertas preventivos antecipando falhas, manutenções vencidas e anomalias operacionais."""
        alertas = []
        previsoes_falhas = self.prever_falhas_equipamentos()
        equipamentos = self.repo.get_all_equipamentos()
        hoje = date.today()

        # Alerta 1: Equipamentos com alta probabilidade iminente de falha
        for p in previsoes_falhas:
            if p["probabilidade_falha_percentual"] >= 65:
                alertas.append({
                    "tipo": "PREVISAO_FALHA_IMINENTE",
                    "severidade": "CRITICO" if p["probabilidade_falha_percentual"] >= 80 else "ALTO",
                    "equipamento_id": p["equipamento_id"],
                    "numero_serie": p["numero_serie"],
                    "bairro": p["localizacao_bairro"],
                    "latitude": p["latitude"],
                    "longitude": p["longitude"],
                    "titulo": f"Previsão de Falha Iminente: {p['numero_serie']}",
                    "mensagem": (
                        f"Risco de falha de {p['probabilidade_falha_percentual']}% estimado para os próximos "
                        f"{p['dias_restantes']} dias em {p['localizacao_bairro']}."
                    ),
                    "acao_recomendada": "Despachar equipe técnica para manutenção preventiva antes da parada operacional.",
                    "data_previsao": p["data_prevista_proxima_falha"]
                })

        # Alerta 2: Manutenções Agendadas Vencendo ou Atrasadas
        for eq in equipamentos:
            if eq.proxima_manutencao:
                dias_ate_manut = (eq.proxima_manutencao - hoje).days
                if dias_ate_manut < 0:
                    alertas.append({
                        "tipo": "MANUTENCAO_VENCIDA",
                        "severidade": "CRITICO",
                        "equipamento_id": eq.id,
                        "numero_serie": eq.numero_serie,
                        "bairro": eq.localizacao_bairro,
                        "latitude": eq.latitude,
                        "longitude": eq.longitude,
                        "titulo": f"Manutenção Vencida: {eq.numero_serie}",
                        "mensagem": f"Equipamento deveria ter passado por manutenção há {abs(dias_ate_manut)} dia(s) atrás.",
                        "acao_recomendada": "Executar vistoria técnica imediata para evitar degradação de telemetria.",
                        "data_previsao": str(eq.proxima_manutencao)
                    })
                elif dias_ate_manut <= 5:
                    alertas.append({
                        "tipo": "MANUTENCAO_PROXIMA",
                        "severidade": "MODERADO",
                        "equipamento_id": eq.id,
                        "numero_serie": eq.numero_serie,
                        "bairro": eq.localizacao_bairro,
                        "latitude": eq.latitude,
                        "longitude": eq.longitude,
                        "titulo": f"Manutenção Preventiva Agendada: {eq.numero_serie}",
                        "mensagem": f"Revisão técnica preventiva programada para daqui a {dias_ate_manut} dia(s).",
                        "acao_recomendada": "Separar peças de reposição e agendar rota da equipe de campo.",
                        "data_previsao": str(eq.proxima_manutencao)
                    })

        # Alerta 3: Detecção de Anomalia de Concentração de Problemas
        risco_regioes = self.calcular_risco_regioes()
        for r in risco_regioes:
            if r["score_geral"] >= 75:
                alertas.append({
                    "tipo": "ANOMALIA_ZONA_RISCO",
                    "severidade": "ALTO",
                    "equipamento_id": None,
                    "numero_serie": "REGIAO",
                    "bairro": r["bairro"],
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "titulo": f"Anomalia de Risco Operacional: {r['bairro']}",
                    "mensagem": (
                        f"Bairro {r['bairro']} atingiu índice crítico de {r['score_geral']}/100 "
                        f"com pico no período da {r['periodo_mais_critico']}."
                    ),
                    "acao_recomendada": f"Reforçar patrulhamento e rondas ostensivas na região durante a {r['periodo_mais_critico']}.",
                    "data_previsao": str(hoje)
                })

        return alertas
