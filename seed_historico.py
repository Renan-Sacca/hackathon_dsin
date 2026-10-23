"""Script de Geração de Dados Históricos Sintéticos — PROMETHEUS F.O.G.O. (Parte 3)

Gera 6+ meses (180+ dias) de:
1. Histórico de transições de situação dos equipamentos (falhas, manutenções, custos e downtimes)
2. Padrões de falha recorrentes em equipamentos específicos (para MTBF e previsão de próxima falha)
3. Zonas de correlação de falhas simultâneas (ex: falhas de energia em grupo na Av. Sampaio Vidal)
4. Mais de 250 ocorrências urbanas distribuídas por bairro, período do dia e severidade
5. Equipamentos não instalados aguardando implantação com tempos de espera distintos
"""

from datetime import datetime, timedelta, timezone, date
import logging
import random
from sqlalchemy import select
from app.database.connection import SessionLocal
from app.database.seed import init_db
from app.models.equipamento import (
    Equipamento,
    EquipamentoSituacao,
    EquipamentoTipo,
    ManutencaoTipo,
)
from app.models.historico_equipamento import HistoricoEquipamento
from app.models.ocorrencia import Ocorrencia, OcorrenciaTipo, OcorrenciaSeveridade

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_historico")

BAIRROS_MARILIA = [
    {"bairro": "Centro", "lat": -22.2139, "lon": -49.9458, "peso_risco": 1.8},
    {"bairro": "Fragata", "lat": -22.2215, "lon": -49.9482, "peso_risco": 1.4},
    {"bairro": "Cascata", "lat": -22.2305, "lon": -49.9460, "peso_risco": 0.9},
    {"bairro": "Campus Universitário", "lat": -22.2380, "lon": -49.9650, "peso_risco": 0.6},
    {"bairro": "Nova Marília", "lat": -22.2450, "lon": -49.9550, "peso_risco": 1.6},
    {"bairro": "Palmital", "lat": -22.2020, "lon": -49.9380, "peso_risco": 1.2},
    {"bairro": "Alto Cafezal", "lat": -22.2180, "lon": -49.9530, "peso_risco": 0.8},
    {"bairro": "Distrito Industrial", "lat": -22.1920, "lon": -49.9550, "peso_risco": 1.1},
]

MOTIVOS_FALHA = [
    "Falha no sensor indutivo de pista",
    "Superaquecimento da unidade de processamento",
    "Curto-circuito na alimentação elétrica",
    "Lente obstruída por pichação / vandalismo",
    "Falha no modem 4G de transmissão",
    "Oscilação brusca de tensão na rede da concessionária",
    "Desalinhamento óptico após temporal com ventos fortes",
    "Rompimento de fibra óptica por caminhão",
    "Bateria do nobreak esgotada",
    "Travamento do firmware após queda de energia",
]

MOTIVOS_MANUTENCAO = [
    "Manutenção preventiva periódica trimestral",
    "Calibração anual metrológica pelo IPEM/INMETRO",
    "Limpeza das lentes e dissipadores de calor",
    "Substituição de conectores oxidados",
    "Atualização de firmware de segurança",
    "Reaperto de suportes e hastes metálicas",
]

CUSTOS_BASE_TIPO = {
    EquipamentoTipo.RADAR_VELOCIDADE: (1200.0, 3200.0),
    EquipamentoTipo.RADAR_SEMAFORO: (900.0, 2400.0),
    EquipamentoTipo.RADAR_CONVERSAO: (850.0, 2100.0),
    EquipamentoTipo.CAMERA_MONITORAMENTO: (450.0, 1600.0),
    EquipamentoTipo.BALANCA_CAMINHAO: (1800.0, 4500.0),
    EquipamentoTipo.VEICULO_FISCALIZACAO_ESTACIONAMENTO: (600.0, 1900.0),
    EquipamentoTipo.CANCELA_AUTOMATIZADA: (350.0, 1100.0),
    EquipamentoTipo.VEICULO_TRANSPORTE: (800.0, 2800.0),
    EquipamentoTipo.TOTEM_ESTACIONAMENTO: (300.0, 950.0),
    EquipamentoTipo.PATINETE_ELETRICO: (120.0, 380.0),
    EquipamentoTipo.MOTO_AGENTE: (250.0, 850.0),
    EquipamentoTipo.VIATURA_GUARDA: (700.0, 2200.0),
    EquipamentoTipo.VIATURA_POLICIA: (750.0, 2400.0),
    EquipamentoTipo.OUTRO: (300.0, 1000.0),
}


def periodo_para_hora(periodo: str) -> int:
    if periodo == "madrugada":
        return random.randint(0, 5)
    elif periodo == "manha":
        return random.randint(6, 11)
    elif periodo == "tarde":
        return random.randint(12, 17)
    else:  # noite
        return random.randint(18, 23)


def seed_historical_data():
    init_db()
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        equipamentos = db.execute(select(Equipamento)).scalars().all()
        if not equipamentos:
            logger.error("Nenhum equipamento cadastrado. Execute seed_demo.py primeiro!")
            return

        # Limpar dados históricos e ocorrências prévios se existirem
        logger.info("Limpando histórico e ocorrências prévias...")
        db.query(HistoricoEquipamento).delete()
        db.query(Ocorrencia).delete()
        db.commit()

        # -------------------------------------------------------------------------
        # 1. Garantir Equipamentos Não Instalados para Prioridade de Instalação (P3-PRED-06)
        # -------------------------------------------------------------------------
        logger.info("Verificando equipamentos com situação 'nao_instalado'...")
        nao_instalados = [e for e in equipamentos if e.situacao == EquipamentoSituacao.NAO_INSTALADO]
        if len(nao_instalados) < 4:
            # Seleciona alguns equipamentos e ajusta para nao_instalado com datas passadas de cadastro
            candidatos = [e for e in equipamentos if e.id not in (1, 2, 4, 26)][:4]
            dias_espera = [65, 45, 20, 8]
            bairros_alocacao = ["Centro", "Nova Marília", "Cascata", "Campus Universitário"]
            for idx, c in enumerate(candidatos):
                c.situacao = EquipamentoSituacao.NAO_INSTALADO
                c.criado_em = now - timedelta(days=dias_espera[idx])
                c.localizacao_bairro = bairros_alocacao[idx]
            db.commit()
            logger.info(f"{len(candidatos)} equipamentos configurados como 'nao_instalado' para teste de priorização.")

        # -------------------------------------------------------------------------
        # 2. Gerar Histórico de Situações (180 dias / 6 meses)
        # -------------------------------------------------------------------------
        logger.info("Gerando histórico temporal de falhas e manutenções (180 dias)...")
        registros_historico = []

        # Identificar equipamentos com falhas frequentes intencionais (Padrão de Falha Recorrente - P3-PRED-01 / P3-TEST-02)
        # O equipamento id 1 e id 2 terão falhas frequentes a cada ~25-35 dias
        eq_recorrente_1 = equipamentos[0]  # ID 1 (ex: RAD-VEL-0101)
        eq_recorrente_2 = equipamentos[1]  # ID 2 (ex: CAM-MON-0205)

        for eq in [eq_recorrente_1, eq_recorrente_2]:
            faixa_custo = CUSTOS_BASE_TIPO.get(eq.tipo, (500.0, 1500.0))
            # 5 ciclos de falha e reparo nos últimos 160 dias
            for ciclo in range(5):
                dias_atras = 160 - (ciclo * 32) + random.randint(-3, 3)
                data_falha = now - timedelta(days=dias_atras, hours=random.randint(1, 10))
                data_reparo = data_falha + timedelta(hours=random.randint(12, 48))

                # Evento 1: Entrou em mau funcionamento
                registros_historico.append(HistoricoEquipamento(
                    equipamento_id=eq.id,
                    situacao_anterior=EquipamentoSituacao.OPERACIONAL,
                    situacao_nova=EquipamentoSituacao.MAU_FUNCIONAMENTO,
                    data_mudanca=data_falha,
                    motivo=random.choice(MOTIVOS_FALHA),
                    custo_manutencao=0.0,
                    tempo_inatividade_horas=0.0
                ))

                # Evento 2: Entrou em manutenção e foi reparado
                custo = round(random.uniform(faixa_custo[0], faixa_custo[1]), 2)
                horas_parado = (data_reparo - data_falha).total_seconds() / 3600.0
                registros_historico.append(HistoricoEquipamento(
                    equipamento_id=eq.id,
                    situacao_anterior=EquipamentoSituacao.MAU_FUNCIONAMENTO,
                    situacao_nova=EquipamentoSituacao.OPERACIONAL,
                    data_mudanca=data_reparo,
                    motivo="Substituição preventiva de componentes e calibração",
                    custo_manutencao=custo,
                    tempo_inatividade_horas=round(horas_parado, 1)
                ))

        # -------------------------------------------------------------------------
        # 3. Zonas de Correlação de Falhas Simultâneas (P3-PRED-04 / P3-TEST-06)
        # -------------------------------------------------------------------------
        # Criar 3 episódios em que 4+ equipamentos da mesma região (Centro / Sampaio Vidal)
        # falharam simultaneamente na mesma data/hora (ex: surto elétrico ou rompimento de rede)
        logger.info("Inserindo episódios de correlação de falha simultânea na mesma zona (Centro)...")
        equipamentos_centro = [e for e in equipamentos if e.localizacao_bairro == "Centro" and e.situacao != EquipamentoSituacao.NAO_INSTALADO][:5]
        datas_correlacao = [
            now - timedelta(days=120, hours=14),
            now - timedelta(days=70, hours=9),
            now - timedelta(days=25, hours=21),
        ]

        for dt_evento in datas_correlacao:
            for eq_c in equipamentos_centro:
                faixa_custo = CUSTOS_BASE_TIPO.get(eq_c.tipo, (400.0, 1200.0))
                dt_falha = dt_evento + timedelta(minutes=random.randint(0, 15))
                dt_resolucao = dt_falha + timedelta(hours=random.randint(4, 18))

                registros_historico.append(HistoricoEquipamento(
                    equipamento_id=eq_c.id,
                    situacao_anterior=EquipamentoSituacao.OPERACIONAL,
                    situacao_nova=EquipamentoSituacao.MAU_FUNCIONAMENTO,
                    data_mudanca=dt_falha,
                    motivo="Queda de fase na rede elétrica da concessionária local (Surto coletivo)",
                    custo_manutencao=0.0,
                    tempo_inatividade_horas=0.0
                ))
                registros_historico.append(HistoricoEquipamento(
                    equipamento_id=eq_c.id,
                    situacao_anterior=EquipamentoSituacao.MAU_FUNCIONAMENTO,
                    situacao_nova=EquipamentoSituacao.OPERACIONAL,
                    data_mudanca=dt_resolucao,
                    motivo="Restauração de energia e rearme de disjuntores da zona",
                    custo_manutencao=round(random.uniform(faixa_custo[0] * 0.5, faixa_custo[1] * 0.7), 2),
                    tempo_inatividade_horas=round((dt_resolucao - dt_falha).total_seconds() / 3600.0, 1)
                ))

        # -------------------------------------------------------------------------
        # 4. Histórico Aleatório para os Demais Equipamentos (Custos e Manutenções)
        # -------------------------------------------------------------------------
        logger.info("Gerando manutenções e histórico geral para todos os equipamentos...")
        for eq in equipamentos:
            if eq.situacao == EquipamentoSituacao.NAO_INSTALADO:
                continue

            faixa_custo = CUSTOS_BASE_TIPO.get(eq.tipo, (350.0, 1200.0))
            # 1 a 3 manutenções/falhas normais nos últimos 180 dias
            qtd_eventos = random.randint(1, 3)
            for _ in range(qtd_eventos):
                dias_atras = random.randint(10, 175)
                dt_inicio = now - timedelta(days=dias_atras, hours=random.randint(0, 23))
                dt_fim = dt_inicio + timedelta(hours=random.randint(2, 36))
                custo = round(random.uniform(faixa_custo[0], faixa_custo[1]), 2)
                motivo = random.choice(MOTIVOS_MANUTENCAO)

                registros_historico.append(HistoricoEquipamento(
                    equipamento_id=eq.id,
                    situacao_anterior=EquipamentoSituacao.OPERACIONAL,
                    situacao_nova=EquipamentoSituacao.MANUTENCAO,
                    data_mudanca=dt_inicio,
                    motivo=motivo,
                    custo_manutencao=0.0,
                    tempo_inatividade_horas=0.0
                ))
                registros_historico.append(HistoricoEquipamento(
                    equipamento_id=eq.id,
                    situacao_anterior=EquipamentoSituacao.MANUTENCAO,
                    situacao_nova=EquipamentoSituacao.OPERACIONAL,
                    data_mudanca=dt_fim,
                    motivo=f"Conclusão: {motivo}",
                    custo_manutencao=custo,
                    tempo_inatividade_horas=round((dt_fim - dt_inicio).total_seconds() / 3600.0, 1)
                ))

        db.add_all(registros_historico)
        db.commit()
        logger.info(f"Total de {len(registros_historico)} registros de histórico inseridos com sucesso.")

        # -------------------------------------------------------------------------
        # 5. Gerar Ocorrências Urbanas (250+ nos últimos 180 dias)
        # -------------------------------------------------------------------------
        logger.info("Gerando ocorrências urbanas sintéticas (acidentes, lentidão, furtos, etc.)...")
        ocorrencias = []
        tipos_ocorrencia = list(OcorrenciaTipo)
        severidades = [
            (OcorrenciaSeveridade.BAIXA, 0.40),
            (OcorrenciaSeveridade.MEDIA, 0.35),
            (OcorrenciaSeveridade.ALTA, 0.18),
            (OcorrenciaSeveridade.CRITICA, 0.07),
        ]

        descricoes_por_tipo = {
            OcorrenciaTipo.ACIDENTE_TRANSITO: [
                "Colisão transversal com danos materiais",
                "Queda de motociclista com lentidão no fluxo",
                "Abalroamento longitudinal entre veículo leve e ônibus",
                "Colisão frontal com necessidade de socorro móvel SAMU",
                "Engavetamento leve entre três veículos na faixa rápida",
            ],
            OcorrenciaTipo.LENTIDAO_CONGESTIONAMENTO: [
                "Congestionamento no horário de pico escolar",
                "Tráfego travado devido a veículo de carga avariado",
                "Lentidão extrema por obras de recapeamento asfáltico",
                "Retenção decorrente de semáforo intermitente",
            ],
            OcorrenciaTipo.FURTO_ROUBO: [
                "Furto de fiação de cobre de semáforo municipal",
                "Tentativa de arrombamento de totem de estacionamento",
                "Subtração de patinete elétrico compartilhado",
                "Furto de estepe e bateria de viatura estacionada",
            ],
            OcorrenciaTipo.VANDALISMO: [
                "Pintura com spray nas lentes de câmera de fiscalização",
                "Quebra deliberada da cancela automatizada",
                "Pichação em totem com dano ao leitor de cartão",
                "Vidro quebrado de veículo municipal estacionado",
            ],
            OcorrenciaTipo.ALAGAMENTO: [
                "Ponto de alagamento intransitável em via rebaixada",
                "Bueiro entupido com acúmulo de enxurrada na pista",
                "Transbordamento de córrego com desvio obrigatório",
            ],
            OcorrenciaTipo.FALHA_SEMAFORO: [
                "Semáforo piscando em amarelo intermitente",
                "Semáforo apagado com risco iminente de colisão",
                "Descompasso do sincronismo de onda verde",
            ],
            OcorrenciaTipo.FISCALIZACAO: [
                "Operação de fiscalização de excesso de peso em caminhões",
                "Blitz de trânsito conjunta com PM e Trânsito",
                "Fiscalização de vagas reservadas para idosos e PCDs",
            ],
            OcorrenciaTipo.OUTRO: [
                "Queda de galho de grande porte obstruindo faixa",
                "Vazamento de óleo na pista com necessidade de serragem",
                "Animal na pista causando frenagens bruscas",
            ],
        }

        # Períodos do dia e pesos por período
        periodos = [
            ("tarde", 0.40),     # Maior fluxo
            ("noite", 0.30),     # Picos e ocorrências noturnas
            ("manha", 0.22),     # Fluxo matinal
            ("madrugada", 0.08)  # Menor volume, mas severidades mais altas
        ]

        # Gerar 280 ocorrências
        for _ in range(280):
            # Escolher bairro ponderado pelo peso de risco
            bairro_info = random.choices(
                BAIRROS_MARILIA,
                weights=[b["peso_risco"] for b in BAIRROS_MARILIA],
                k=1
            )[0]

            # Escolher período
            periodo = random.choices(
                [p[0] for p in periodos],
                weights=[p[1] for p in periodos],
                k=1
            )[0]

            # Data aleatória nos últimos 180 dias
            dias_atras = random.randint(1, 180)
            hora = periodo_para_hora(periodo)
            minuto = random.randint(0, 59)
            data_ocorr = now - timedelta(days=dias_atras)
            data_ocorr = data_ocorr.replace(hour=hora, minute=minuto, second=0)

            tipo = random.choice(tipos_ocorrencia)
            severidade = random.choices(
                [s[0] for s in severidades],
                weights=[s[1] for s in severidades],
                k=1
            )[0]

            # Se for madrugada e acidente/furto, aumenta severidade
            if periodo == "madrugada" and tipo in (OcorrenciaTipo.ACIDENTE_TRANSITO, OcorrenciaTipo.FURTO_ROUBO):
                if random.random() < 0.6:
                    severidade = OcorrenciaSeveridade.ALTA

            # Descrição correspondente
            desc_opcoes = descricoes_por_tipo.get(tipo, ["Ocorrência operacional registrada na via."])
            descricao = random.choice(desc_opcoes)

            # Coordenadas próximas à base do bairro
            lat_ocorr = bairro_info["lat"] + random.uniform(-0.005, 0.005)
            lon_ocorr = bairro_info["lon"] + random.uniform(-0.005, 0.005)

            # Equipamento próximo correlacionado (opcional)
            eq_relacionado_id = None
            eqs_do_bairro = [e for e in equipamentos if e.localizacao_bairro == bairro_info["bairro"] and e.ativo]
            if eqs_do_bairro and random.random() < 0.5:
                eq_relacionado_id = random.choice(eqs_do_bairro).id

            ocorrencias.append(Ocorrencia(
                tipo=tipo,
                severidade=severidade,
                descricao=descricao,
                localizacao_bairro=bairro_info["bairro"],
                localizacao_rua=f"Via Principal - {bairro_info['bairro']}",
                latitude=lat_ocorr,
                longitude=lon_ocorr,
                data_hora=data_ocorr,
                periodo_dia=periodo,
                equipamento_id=eq_relacionado_id
            ))

        db.add_all(ocorrencias)
        db.commit()
        logger.info(f"Total de {len(ocorrencias)} ocorrências sintéticas inseridas com sucesso.")
        logger.info("Base de dados históricos da Parte 3 populada com sucesso!")


if __name__ == "__main__":
    seed_historical_data()
