from datetime import datetime, timezone
import math
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models.agente import Agente, AgenteTipo
from app.repositories.predictive_repository import PredictiveRepository
from app.services.predictive_service import PredictiveService


class ReforcoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PredictiveRepository(db)
        self.pred_service = PredictiveService(db)

    def estimar_reforco_agentes(self) -> List[Dict[str, Any]]:
        """Cruza índice de risco de cada região por período do dia com a distribuição de agentes em campo

        para gerar recomendações preditivas de reforço operacional.
        """
        risco_regioes = self.pred_service.calcular_risco_regioes()
        agentes = self.repo.get_agentes_ativos()
        ocorrencias = self.repo.get_ocorrencias_agrupadas(dias=90)

        # Mapear quantidade de agentes por bairro
        # Calcula distância euclidiana simples entre coordenada do agente e coordenada do centro do bairro
        agentes_por_bairro: Dict[str, List[Agente]] = {r["bairro"]: [] for r in risco_regioes}

        for ag in agentes:
            if ag.latitude is None or ag.longitude is None:
                continue
            menor_dist = float("inf")
            bairro_mais_proximo = None
            for r in risco_regioes:
                d = math.hypot(ag.latitude - r["latitude"], ag.longitude - r["longitude"])
                if d < menor_dist:
                    menor_dist = d
                    bairro_mais_proximo = r["bairro"]

            if bairro_mais_proximo and menor_dist < 0.05:  # ~5km
                agentes_por_bairro[bairro_mais_proximo].append(ag)

        # Mapear tipos de ocorrência mais frequentes por bairro para direcionar tipo de agente
        tipos_por_bairro: Dict[str, Dict[str, int]] = {}
        for o in ocorrencias:
            b = o["bairro"]
            t = o["tipo"]
            if b not in tipos_por_bairro:
                tipos_por_bairro[b] = {}
            tipos_por_bairro[b][t] = tipos_por_bairro[b].get(t, 0) + 1

        recomendacoes = []

        horarios_periodo = {
            "manha": "07:00 às 11:30",
            "tarde": "12:00 às 17:30",
            "noite": "18:00 às 22:30",
            "madrugada": "23:00 às 05:00"
        }

        for regiao in risco_regioes:
            bairro = regiao["bairro"]
            agentes_locais = agentes_por_bairro.get(bairro, [])
            total_agentes_atuais = len(agentes_locais)

            # Analisar cada período
            for periodo, det in regiao["detalhes_periodos"].items():
                score = det["score_risco"]
                if score < 30.0:
                    continue

                # Fórmula de dimensionamento: ~1 agente para cada 25 pontos de risco
                agentes_necessarios = max(1, math.ceil(score / 25.0))
                deficit = max(0, agentes_necessarios - total_agentes_atuais)

                if deficit > 0 or score >= 60.0:
                    # Determinar tipo de reforço prioritário
                    contagens_tipo = tipos_por_bairro.get(bairro, {})
                    tipo_recomendado = "agente_transito"
                    nome_tipo = "Agente de Trânsito"

                    acidentes_e_transito = (
                        contagens_tipo.get("acidente_transito", 0) +
                        contagens_tipo.get("lentidao_congestionamento", 0) +
                        contagens_tipo.get("falha_semaforo", 0)
                    )
                    furtos_e_vandalismo = (
                        contagens_tipo.get("furto_roubo", 0) +
                        contagens_tipo.get("vandalismo", 0)
                    )

                    if furtos_e_vandalismo > acidentes_e_transito:
                        tipo_recomendado = "guarda_municipal"
                        nome_tipo = "Guarda Municipal / Patrulha Ostensiva"

                    prioridade = "ALTA"
                    if score >= 70 or deficit >= 3:
                        prioridade = "CRITICA"
                    elif score < 45:
                        prioridade = "MODERADA"

                    recomendacoes.append({
                        "bairro": bairro,
                        "latitude": regiao["latitude"],
                        "longitude": regiao["longitude"],
                        "periodo": periodo,
                        "horario_sugerido": horarios_periodo.get(periodo, periodo),
                        "score_risco": score,
                        "agentes_em_campo": total_agentes_atuais,
                        "agentes_ideais": agentes_necessarios,
                        "deficit_agentes": deficit,
                        "tipo_agente_sugerido": tipo_recomendado,
                        "nome_tipo_sugerido": nome_tipo,
                        "prioridade": prioridade,
                        "justificativa": (
                            f"Região {bairro} no período da {periodo} ({horarios_periodo.get(periodo)}) "
                            f"possui score de risco {score}/100 com {total_agentes_atuais} agente(s) alocado(s). "
                            f"Recomenda-se reforço de +{deficit} equipe(s) de {nome_tipo} para contenção preventiva."
                        )
                    })

        # Ordenar por prioridade e déficit decrescente
        peso_prio = {"CRITICA": 3, "ALTA": 2, "MODERADA": 1}
        recomendacoes.sort(
            key=lambda x: (peso_prio.get(x["prioridade"], 0), x["deficit_agentes"], x["score_risco"]),
            reverse=True
        )

        return recomendacoes
