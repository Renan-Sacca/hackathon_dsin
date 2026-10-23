from datetime import datetime, timedelta, timezone
import math
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models.equipamento import Equipamento, EquipamentoSituacao
from app.repositories.predictive_repository import PredictiveRepository


class CorrelacaoService:
    def __init__(self, db: Session):
        self.repo = PredictiveRepository(db)

    def detectar_zonas_correlacao(self, dias: int = 180, janela_horas: float = 2.0) -> List[Dict[str, Any]]:
        """Identifica zonas de equipamentos que apresentam falhas simultâneas/correlacionadas no tempo e espaço,

        sinalizando problemas de infraestrutura compartilhada (rede elétrica, fibra óptica, vandalismo concentrado).
        """
        falhas = self.repo.get_falhas_historicas(dias=dias)
        equipamentos = {e.id: e for e in self.repo.get_all_equipamentos()}

        if not falhas:
            return []

        # Agrupar falhas ocorridas na mesma janela temporal (<= 2 horas)
        janelas_temporais: List[List[Any]] = []
        falhas_ordenadas = sorted(falhas, key=lambda f: f.data_mudanca)

        janela_atual = [falhas_ordenadas[0]]
        for f in falhas_ordenadas[1:]:
            diff = (f.data_mudanca - janela_atual[-1].data_mudanca).total_seconds() / 3600.0
            if diff <= janela_horas:
                janela_atual.append(f)
            else:
                if len(janela_atual) >= 2:
                    janelas_temporais.append(janela_atual)
                janela_atual = [f]

        if len(janela_atual) >= 2:
            janelas_temporais.append(janela_atual)

        # Analisar agrupamentos espaciais por bairro/rua nas janelas temporais
        zonas_detectadas: Dict[str, Dict[str, Any]] = {}

        for janela in janelas_temporais:
            # Agrupar falhas da janela por proximidade geográfica (mesmo bairro ou raio < 1km)
            grupos_locais: Dict[str, List[Any]] = {}
            for f in janela:
                eq = equipamentos.get(f.equipamento_id)
                if not eq:
                    continue
                chave_loc = eq.localizacao_bairro
                if chave_loc not in grupos_locais:
                    grupos_locais[chave_loc] = []
                # Evita duplicata do mesmo equipamento na mesma janela
                if not any(item.equipamento_id == eq.id for item in grupos_locais[chave_loc]):
                    grupos_locais[chave_loc].append(f)

            # Para cada local onde 2 ou mais equipamentos distintos falharam juntos
            for bairro, falhas_grupo in grupos_locais.items():
                if len(falhas_grupo) >= 2:
                    eq_ids = sorted(list(set([fg.equipamento_id for fg in falhas_grupo])))
                    chave_zona = f"{bairro}:{'-'.join(str(i) for i in eq_ids)}"

                    if chave_zona not in zonas_detectadas:
                        # Extrair dados espaciais
                        eqs_da_zona = [equipamentos[eid] for eid in eq_ids]
                        lat_media = sum(e.latitude for e in eqs_da_zona) / len(eqs_da_zona)
                        lon_media = sum(e.longitude for e in eqs_da_zona) / len(eqs_da_zona)

                        # Raio da zona em metros
                        max_dist_m = 100.0
                        for e in eqs_da_zona:
                            dist_m = math.hypot(e.latitude - lat_media, e.longitude - lon_media) * 111320.0
                            if dist_m > max_dist_m:
                                max_dist_m = dist_m

                        zonas_detectadas[chave_zona] = {
                            "bairro": bairro,
                            "ruas": list(set([e.localizacao_rua for e in eqs_da_zona])),
                            "latitude": round(lat_media, 6),
                            "longitude": round(lon_media, 6),
                            "raio_metros": round(max_dist_m + 80.0),  # margem de abrangência
                            "equipamentos": [
                                {
                                    "id": e.id,
                                    "numero_serie": e.numero_serie,
                                    "tipo": e.tipo.value,
                                    "rua": e.localizacao_rua,
                                    "latitude": e.latitude,
                                    "longitude": e.longitude
                                }
                                for e in eqs_da_zona
                            ],
                            "episodios_simultaneos": 0,
                            "datas_episodios": [],
                            "motivos_relatados": []
                        }

                    zonas_detectadas[chave_zona]["episodios_simultaneos"] += 1
                    zonas_detectadas[chave_zona]["datas_episodios"].append(
                        falhas_grupo[0].data_mudanca.strftime("%d/%m/%Y %H:%M")
                    )
                    for fg in falhas_grupo:
                        if fg.motivo and fg.motivo not in zonas_detectadas[chave_zona]["motivos_relatados"]:
                            zonas_detectadas[chave_zona]["motivos_relatados"].append(fg.motivo)

        resultado = []
        for chave, z in zonas_detectadas.items():
            qtd_equipamentos = len(z["equipamentos"])
            qtd_episodios = z["episodios_simultaneos"]

            # Cálculo de score de correlação (0 a 100%)
            score_correlacao = min(99.0, round((qtd_episodios * 25.0) + (qtd_equipamentos * 12.0), 1))

            nivel_suspeita = "MODERADA"
            if score_correlacao >= 70 or qtd_episodios >= 3:
                nivel_suspeita = "CRITICA"
            elif score_correlacao >= 45:
                nivel_suspeita = "ALTA"

            # Causa provável identificada
            causa_provavel = "Instabilidade na rede elétrica compartilhada (queda de fase/surto)"
            motivos_str = " ".join(z["motivos_relatados"]).lower()
            if "fibra" in motivos_str or "modem" in motivos_str or "rede" in motivos_str:
                causa_provavel = "Falha no link de comunicação / rompimento de fibra óptica na via"
            elif "vandalismo" in motivos_str or "furto" in motivos_str:
                causa_provavel = "Ação coordenada de vandalismo / furto na localidade"

            resultado.append({
                "zona_id": chave,
                "bairro": z["bairro"],
                "ruas_principais": z["ruas"],
                "latitude": z["latitude"],
                "longitude": z["longitude"],
                "raio_metros": z["raio_metros"],
                "total_equipamentos_afetados": qtd_equipamentos,
                "total_episodios_simultaneos": qtd_episodios,
                "score_correlacao": score_correlacao,
                "nivel_suspeita": nivel_suspeita,
                "causa_provavel": causa_provavel,
                "equipamentos": z["equipamentos"],
                "datas_episodios": z["datas_episodios"],
                "explicacao": (
                    f"Detectados {qtd_episodios} episódios em que {qtd_equipamentos} equipamentos distintos "
                    f"nesta zona entraram em falha na mesma janela horária. Nível de correlação de {score_correlacao}%, "
                    f"indicando forte suspeita de: {causa_provavel}."
                )
            })

        resultado.sort(key=lambda x: x["score_correlacao"], reverse=True)
        return resultado
