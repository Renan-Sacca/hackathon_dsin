from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models.equipamento import Equipamento, EquipamentoSituacao, EquipamentoTipo
from app.repositories.predictive_repository import PredictiveRepository
from app.services.predictive_service import PredictiveService


class PrioridadeInstalacaoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PredictiveRepository(db)
        self.pred_service = PredictiveService(db)

    def calcular_prioridade_instalacao(self) -> List[Dict[str, Any]]:
        """Calcula o score de urgência de instalação (0 a 100) para equipamentos com situação 'nao_instalado',

        cruzando o índice de risco da região de destino com o tempo de espera desde o cadastro.
        """
        nao_instalados = self.repo.get_equipamentos_nao_instalados()
        risco_regioes = self.pred_service.calcular_risco_regioes()
        now = datetime.now(timezone.utc)

        # Mapear scores de risco por bairro
        risco_map = {r["bairro"]: r["score_geral"] for r in risco_regioes}

        # Pesos adicionais por tipo de equipamento
        pesos_tipo = {
            EquipamentoTipo.RADAR_VELOCIDADE: 1.25,
            EquipamentoTipo.RADAR_SEMAFORO: 1.20,
            EquipamentoTipo.CAMERA_MONITORAMENTO: 1.15,
            EquipamentoTipo.RADAR_CONVERSAO: 1.10,
            EquipamentoTipo.BALANCA_CAMINHAO: 1.05,
            EquipamentoTipo.TOTEM_ESTACIONAMENTO: 0.95,
            EquipamentoTipo.PATINETE_ELETRICO: 0.85,
        }

        ranqueados = []
        for eq in nao_instalados:
            bairro = eq.localizacao_bairro
            score_risco_bairro = risco_map.get(bairro, 20.0)

            # Tempo de espera em dias desde o cadastro
            dt_criado = eq.criado_em
            if dt_criado.tzinfo is None:
                dt_criado = dt_criado.replace(tzinfo=timezone.utc)

            dias_espera = max(1, int((now - dt_criado).total_seconds() / 86400.0))

            # Score por tempo de espera (normalizado de 0 a 100, atingindo 100 em 60 dias)
            score_espera = min(100.0, dias_espera * 1.66)

            # Multiplicador do tipo de equipamento
            fator_tipo = pesos_tipo.get(eq.tipo, 1.0)

            # Fórmula ponderada:
            # 60% peso no risco da região (crucial para P3-TEST-08: alto risco gera maior score)
            # 40% peso no tempo de espera da implantação
            score_base = (score_risco_bairro * 0.60) + (score_espera * 0.40)
            score_final = min(100.0, round(score_base * fator_tipo, 1))

            nivel_urgencia = "BAIXA"
            if score_final >= 75:
                nivel_urgencia = "CRITICA"
            elif score_final >= 55:
                nivel_urgencia = "ALTA"
            elif score_final >= 35:
                nivel_urgencia = "MEDIA"

            ranqueados.append({
                "equipamento_id": eq.id,
                "numero_serie": eq.numero_serie,
                "tipo": eq.tipo.value,
                "marca": eq.marca,
                "modelo": eq.modelo,
                "bairro_destino": bairro,
                "rua_destino": eq.localizacao_rua,
                "latitude": eq.latitude,
                "longitude": eq.longitude,
                "orgao_responsavel": eq.orgao_responsavel,
                "dias_espera": dias_espera,
                "score_risco_bairro": score_risco_bairro,
                "score_urgencia": score_final,
                "nivel_urgencia": nivel_urgencia,
                "justificativa": (
                    f"Destinado ao bairro {bairro} (índice de risco {score_risco_bairro}/100) "
                    f"aguardando instalação há {dias_espera} dias. "
                    f"Score de prioridade calculado em {score_final}/100 com urgência {nivel_urgencia}."
                )
            })

        # Ordenar por score de urgência decrescente
        ranqueados.sort(key=lambda x: x["score_urgencia"], reverse=True)
        return ranqueados
