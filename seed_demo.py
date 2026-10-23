"""Script de Dados de Demonstração — PROMETHEUS F.O.G.O.

Popula o banco de dados com:
- 50+ equipamentos realistas de segurança e trânsito com coordenadas de Marília/SP
- 20+ agentes de campo (Trânsito, Guarda Municipal e Polícia Militar)
- Equipamentos em diversas situações (operacional, mau funcionamento, manutenção, furtado, etc.)
- Propriedades técnicas dinâmicas detalhadas por tipo
"""

from datetime import date, datetime, timedelta, timezone
import logging
import random
from sqlalchemy import select
from app.database.connection import SessionLocal
from app.database.seed import init_db, seed_default_admin
from app.models.agente import Agente, AgenteSituacao, AgenteTipo
from app.models.equipamento import (
    Equipamento,
    EquipamentoSituacao,
    EquipamentoTipo,
    ManutencaoTipo,
)
from app.models.equipamento_propriedade import EquipamentoPropriedade

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_demo")

# Regiões e logradouros reais de Marília/SP
LOCAIS = [
    {"bairro": "Centro", "rua": "Av. Sampaio Vidal", "ref": "Próximo à Prefeitura", "lat": -22.2139, "lon": -49.9458},
    {"bairro": "Centro", "rua": "Rua 9 de Julho", "ref": "Cruzamento bancário", "lat": -22.2162, "lon": -49.9475},
    {"bairro": "Centro", "rua": "Av. Brasil", "ref": "Próximo à Estação Rodoviária Velha", "lat": -22.2115, "lon": -49.9440},
    {"bairro": "Centro", "rua": "Rua São Luiz", "ref": "Área comercial", "lat": -22.2150, "lon": -49.9465},
    {"bairro": "Fragata", "rua": "Av. Tiradentes", "ref": "Próximo à Santa Casa", "lat": -22.2215, "lon": -49.9482},
    {"bairro": "Fragata", "rua": "Rua Marília", "ref": "Entrada do bosque", "lat": -22.2248, "lon": -49.9510},
    {"bairro": "Fragata", "rua": "Av. das Esmeraldas", "ref": "Pista de Cooper km 1", "lat": -22.2285, "lon": -49.9420},
    {"bairro": "Fragata", "rua": "Av. das Esmeraldas", "ref": "Pista de Cooper km 3", "lat": -22.2350, "lon": -49.9380},
    {"bairro": "Cascata", "rua": "Av. Cascata", "ref": "Rotatória do Mirante", "lat": -22.2305, "lon": -49.9460},
    {"bairro": "Cascata", "rua": "Rua Anita Garibaldi", "ref": "Próximo à represa", "lat": -22.2335, "lon": -49.9490},
    {"bairro": "Campus Universitário", "rua": "Av. Hygino Muzzi Filho", "ref": "Em frente à UNESP", "lat": -22.2380, "lon": -49.9650},
    {"bairro": "Campus Universitário", "rua": "Av. Castro Alves", "ref": "Acesso Unimar", "lat": -22.2320, "lon": -49.9680},
    {"bairro": "Nova Marília", "rua": "Av. João Ramalho", "ref": "KM 202 - Sentido Bairro", "lat": -22.2450, "lon": -49.9550},
    {"bairro": "Nova Marília", "rua": "Av. Mem de Sá", "ref": "Em frente ao posto de saúde", "lat": -22.2490, "lon": -49.9580},
    {"bairro": "Nova Marília", "rua": "Rua Vicente Ferreira", "ref": "Cruzamento da feira", "lat": -22.2420, "lon": -49.9515},
    {"bairro": "Maracá", "rua": "Av. Nelson Spielmann", "ref": "Acesso Zona Norte", "lat": -22.1950, "lon": -49.9430},
    {"bairro": "Palmital", "rua": "Rua dos Bancários", "ref": "Próximo à creche municipal", "lat": -22.2020, "lon": -49.9380},
    {"bairro": "Palmital", "rua": "Av. Santo Antônio", "ref": "Posto Ipiranga", "lat": -22.2065, "lon": -49.9410},
    {"bairro": "Alto Cafezal", "rua": "Rua Bahia", "ref": "Oposto ao nº 450", "lat": -22.2180, "lon": -49.9530},
    {"bairro": "Jardim Acapulco", "rua": "Av. Brigadeiro Eduardo Gomes", "ref": "Acesso ao Aeroporto", "lat": -22.1980, "lon": -49.9270},
    {"bairro": "Jardim América", "rua": "Av. Rio Branco", "ref": "Viaduto de acesso", "lat": -22.2090, "lon": -49.9500},
    {"bairro": "Distrito Industrial", "rua": "Av. República", "ref": "KM 454 Rod. SP-294", "lat": -22.1920, "lon": -49.9550},
    {"bairro": "Distrito Industrial", "rua": "Rua Manoel Santos", "ref": "Portaria 3 da fábrica", "lat": -22.1890, "lon": -49.9580},
]

ORGAOS = ["EMDURB", "Guarda Municipal", "Polícia Militar", "Secretaria de Obras", "Secretaria de Trânsito"]


def seed_demo_data():
    init_db()
    with SessionLocal() as db:
        seed_default_admin(db)

        # Verifica se já há equipamentos
        existentes_eq = db.scalar(select(Equipamento).limit(1))
        if existentes_eq:
            logger.info("Equipamentos já encontrados no banco. Limpando dados de demonstração anteriores...")
            db.query(EquipamentoPropriedade).delete()
            db.query(Equipamento).delete()
            db.query(Agente).delete()
            db.commit()

        logger.info("Gerando 55+ equipamentos realistas...")

        equipamentos_gerados = []
        hoje = date.today()

        # Definição de equipamentos estratégicos com problemas intencionais (para alertas visuais ricos)
        equipamentos_config = [
            # CRÍTICOS (Mau Funcionamento e Furtados)
            {
                "serie": "RAD-VEL-0101", "tipo": EquipamentoTipo.RADAR_VELOCIDADE, "situacao": EquipamentoSituacao.MAU_FUNCIONAMENTO,
                "manutencao": ManutencaoTipo.IMEDIATA, "marca": "FiscalTech", "modelo": "SpeedMaster 400",
                "props": [("velocidade_maxima", "60"), ("qtd_faixas", "2"), ("sentido", "Centro-Bairro"), ("sensor_laco", "falha_indutiva")]
            },
            {
                "serie": "CAM-MON-0205", "tipo": EquipamentoTipo.CAMERA_MONITORAMENTO, "situacao": EquipamentoSituacao.MAU_FUNCIONAMENTO,
                "manutencao": ManutencaoTipo.IMEDIATA, "marca": "Hikvision", "modelo": "DarkFighter 4K",
                "props": [("resolucao", "4K UHD"), ("visao_noturna", "Sim"), ("ptz_360", "Sim"), ("status_video", "sem_sinal_optico")]
            },
            {
                "serie": "PAT-ELE-0033", "tipo": EquipamentoTipo.PATINETE_ELETRICO, "situacao": EquipamentoSituacao.FURTADO,
                "manutencao": ManutencaoTipo.NENHUMA, "marca": "Ninebot", "modelo": "Segway Max Pro",
                "props": [("rastreador_gps", "offline"), ("alerta_policial", "B.O. 4512/2026")]
            },
            {
                "serie": "TOT-EST-0012", "tipo": EquipamentoTipo.TOTEM_ESTACIONAMENTO, "situacao": EquipamentoSituacao.MAU_FUNCIONAMENTO,
                "manutencao": ManutencaoTipo.IMEDIATA, "marca": "DigiSat", "modelo": "SmartTotem v3",
                "props": [("leitor_cartao", "travado"), ("conexao", "4G")]
            },
            # URGENTES / MANUTENÇÃO IMEDIATA
            {
                "serie": "BAL-CAM-0004", "tipo": EquipamentoTipo.BALANCA_CAMINHAO, "situacao": EquipamentoSituacao.MANUTENCAO,
                "manutencao": ManutencaoTipo.IMEDIATA, "marca": "Toledo", "modelo": "RoadScale 80T",
                "props": [("capacidade_maxima_ton", "80"), ("calibracao", "vencida_inmetro")]
            },
            {
                "serie": "CAN-AUT-0008", "tipo": EquipamentoTipo.CANCELA_AUTOMATIZADA, "situacao": EquipamentoSituacao.MANUTENCAO,
                "manutencao": ManutencaoTipo.IMEDIATA, "marca": "PPA", "modelo": "Barrier JetFlex",
                "props": [("tempo_abertura_seg", "1.5"), ("braco_mecanico", "avaria_colisao")]
            },
            # ATENÇÃO (Manutenção agendada nos próximos 2 a 3 dias)
            {
                "serie": "RAD-SEM-0022", "tipo": EquipamentoTipo.RADAR_SEMAFORO, "situacao": EquipamentoSituacao.OPERACIONAL,
                "manutencao": ManutencaoTipo.AGENDADA, "proxima": hoje + timedelta(days=2), "marca": "Splice", "modelo": "StopLight Pro",
                "props": [("direcoes_fiscalizadas", "Norte/Sul"), ("tempo_amarelo_segundos", "4")]
            },
            {
                "serie": "CAM-MON-0112", "tipo": EquipamentoTipo.CAMERA_MONITORAMENTO, "situacao": EquipamentoSituacao.OPERACIONAL,
                "manutencao": ManutencaoTipo.AGENDADA, "proxima": hoje + timedelta(days=3), "marca": "Bosch", "modelo": "AutoDome 7000",
                "props": [("resolucao", "1080p Full HD"), ("zoom_optico", "30x"), ("visao_noturna", "Sim")]
            },
            {
                "serie": "RAD-CON-0005", "tipo": EquipamentoTipo.RADAR_CONVERSAO, "situacao": EquipamentoSituacao.OPERACIONAL,
                "manutencao": ManutencaoTipo.AGENDADA, "proxima": hoje + timedelta(days=1), "marca": "FiscalTech", "modelo": "NoTurn 360",
                "props": [("manobra_fiscalizada", "Conversao a esquerda proibida"), ("horario_restricao", "07h as 19h")]
            },
        ]

        # Criar os equipamentos estratégicos
        for i, cfg in enumerate(equipamentos_config):
            local = LOCAIS[i % len(LOCAIS)]
            eq = Equipamento(
                numero_serie=cfg["serie"],
                marca=cfg["marca"],
                modelo=cfg["modelo"],
                tipo=cfg["tipo"],
                situacao=cfg["situacao"],
                manutencao_tipo=cfg["manutencao"],
                proxima_manutencao=cfg.get("proxima"),
                localizacao_bairro=local["bairro"],
                localizacao_rua=local["rua"],
                localizacao_referencia=local["ref"],
                localizacao_cidade="Marília",
                localizacao_uf="SP",
                latitude=local["lat"] + (random.uniform(-0.001, 0.001)),
                longitude=local["lon"] + (random.uniform(-0.001, 0.001)),
                orgao_responsavel=ORGAOS[i % len(ORGAOS)],
                ativo=True
            )
            for chave, valor in cfg["props"]:
                eq.propriedades.append(EquipamentoPropriedade(chave=chave, valor=valor))
            equipamentos_gerados.append(eq)

        # Gerar mais 50 equipamentos distribuídos, a maioria OPERACIONAL
        marcas_modelos = {
            EquipamentoTipo.RADAR_VELOCIDADE: [("FiscalTech", "SpeedMaster 400"), ("Splice", "SpeedTrack")],
            EquipamentoTipo.RADAR_SEMAFORO: [("Splice", "StopLight v2"), ("Consladel", "SemaCheck")],
            EquipamentoTipo.RADAR_CONVERSAO: [("FiscalTech", "NoTurn 360"), ("Splice", "TurnGuard")],
            EquipamentoTipo.CAMERA_MONITORAMENTO: [("Hikvision", "DarkFighter PTZ"), ("Bosch", "AutoDome 7000"), ("Intelbras", "VIP 5220")],
            EquipamentoTipo.BALANCA_CAMINHAO: [("Toledo", "RoadScale 80T"), ("Filizola", "WeighMaster")],
            EquipamentoTipo.VEICULO_FISCALIZACAO_ESTACIONAMENTO: [("Renault", "Kwid E-Tech OCR"), ("Fiat", "Mobi Fiscalizador")],
            EquipamentoTipo.CANCELA_AUTOMATIZADA: [("PPA", "Barrier JetFlex"), ("Garen", "SpeedBarrier")],
            EquipamentoTipo.VEICULO_TRANSPORTE: [("Mercedes-Benz", "Sprinter Escolar"), ("Chevrolet", "Spin Táxi Acessível")],
            EquipamentoTipo.TOTEM_ESTACIONAMENTO: [("DigiSat", "SmartTotem v3"), ("ParkHelp", "Terminal 4G")],
            EquipamentoTipo.PATINETE_ELETRICO: [("Ninebot", "Segway Max Pro"), ("Xiaomi", "Mi Electric 4")],
            EquipamentoTipo.MOTO_AGENTE: [("Yamaha", "Lander 250 Trânsito"), ("Honda", "XRE 300 EMDURB")],
            EquipamentoTipo.VIATURA_GUARDA: [("Toyota", "Hilux GCM Patrulha"), ("Renault", "Duster Guarda")],
            EquipamentoTipo.VIATURA_POLICIA: [("Toyota", "Corolla Cross PM"), ("Chevrolet", "Spin Rádio Patrulha")],
        }

        tipos_disponiveis = list(marcas_modelos.keys())

        for idx in range(10, 60):
            local = LOCAIS[idx % len(LOCAIS)]
            tipo = tipos_disponiveis[idx % len(tipos_disponiveis)]
            opcoes_marca = marcas_modelos[tipo]
            marca, modelo = random.choice(opcoes_marca)

            # 85% operacional, restante distribuído
            r = random.random()
            if r < 0.82:
                situacao = EquipamentoSituacao.OPERACIONAL
                manutencao = ManutencaoTipo.NENHUMA
                prox = None
            elif r < 0.88:
                situacao = EquipamentoSituacao.MANUTENCAO
                manutencao = ManutencaoTipo.AGENDADA
                prox = hoje + timedelta(days=random.randint(4, 30))
            elif r < 0.94:
                situacao = EquipamentoSituacao.NAO_INSTALADO
                manutencao = ManutencaoTipo.NENHUMA
                prox = None
            else:
                situacao = EquipamentoSituacao.DESATIVADO
                manutencao = ManutencaoTipo.NENHUMA
                prox = None

            prefixo = tipo.value[:3].upper()
            serie = f"{prefixo}-{random.randint(1000, 9999)}"

            # Dispersão suave nas coordenadas para cobrir o bairro
            lat_jitter = local["lat"] + random.uniform(-0.0035, 0.0035)
            lon_jitter = local["lon"] + random.uniform(-0.0035, 0.0035)

            eq = Equipamento(
                numero_serie=serie,
                marca=marca,
                modelo=modelo,
                tipo=tipo,
                situacao=situacao,
                manutencao_tipo=manutencao,
                proxima_manutencao=prox,
                localizacao_bairro=local["bairro"],
                localizacao_rua=local["rua"],
                localizacao_referencia=f"Próximo ao nº {random.randint(50, 1500)}",
                localizacao_cidade="Marília",
                localizacao_uf="SP",
                latitude=round(lat_jitter, 6),
                longitude=round(lon_jitter, 6),
                orgao_responsavel=random.choice(ORGAOS),
                ativo=True
            )

            # Injeta propriedades específicas do tipo
            if tipo == EquipamentoTipo.RADAR_VELOCIDADE:
                eq.propriedades.append(EquipamentoPropriedade(chave="velocidade_maxima", valor=str(random.choice([40, 50, 60, 70]))))
                eq.propriedades.append(EquipamentoPropriedade(chave="qtd_faixas", valor=str(random.choice([2, 3, 4]))))
            elif tipo == EquipamentoTipo.CAMERA_MONITORAMENTO:
                eq.propriedades.append(EquipamentoPropriedade(chave="resolucao", valor=random.choice(["4K UHD", "1080p Full HD"])))
                eq.propriedades.append(EquipamentoPropriedade(chave="visao_noturna", valor="Sim"))
            elif tipo in (EquipamentoTipo.VIATURA_GUARDA, EquipamentoTipo.VIATURA_POLICIA):
                eq.propriedades.append(EquipamentoPropriedade(chave="prefixo", valor=f"{prefixo}-{random.randint(10, 99)}"))
                eq.propriedades.append(EquipamentoPropriedade(chave="placa", valor=f"BRA{random.randint(1,9)}X{random.randint(10,99)}"))
            elif tipo == EquipamentoTipo.PATINETE_ELETRICO:
                eq.propriedades.append(EquipamentoPropriedade(chave="autonomia_km", valor=str(random.randint(15, 40))))

            equipamentos_gerados.append(eq)

        db.add_all(equipamentos_gerados)
        db.commit()
        logger.info(f"{len(equipamentos_gerados)} equipamentos cadastrados com sucesso!")

        # -----------------------------------------------------------------
        # Gerar 22+ Agentes de Campo
        # -----------------------------------------------------------------
        logger.info("Gerando 22+ agentes de campo com geolocalização...")
        nomes_agentes = [
            ("Marcos Antonio Vieira", AgenteTipo.AGENTE_TRANSITO, "EMDURB", "AGT-0101", "(14) 99781-1122"),
            ("Juliana Mendes Ramos", AgenteTipo.AGENTE_TRANSITO, "EMDURB", "AGT-0102", "(14) 99781-1123"),
            ("Ricardo Barbosa Leite", AgenteTipo.AGENTE_TRANSITO, "EMDURB", "AGT-0103", "(14) 99781-1124"),
            ("Fernanda Lima Prado", AgenteTipo.AGENTE_TRANSITO, "EMDURB", "AGT-0104", "(14) 99781-1125"),
            ("Roberto Alencar", AgenteTipo.AGENTE_TRANSITO, "EMDURB", "AGT-0105", "(14) 99781-1126"),
            ("Inspetor Cláudio Gomes", AgenteTipo.GUARDA_MUNICIPAL, "Guarda Civil", "GCM-0201", "(14) 99812-4401"),
            ("Sub-Inspetora Vanessa Rocha", AgenteTipo.GUARDA_MUNICIPAL, "Guarda Civil", "GCM-0202", "(14) 99812-4402"),
            ("Guarda Valmir Souza", AgenteTipo.GUARDA_MUNICIPAL, "Guarda Civil", "GCM-0203", "(14) 99812-4403"),
            ("Guarda Renata Dias", AgenteTipo.GUARDA_MUNICIPAL, "Guarda Civil", "GCM-0204", "(14) 99812-4404"),
            ("Guarda Emerson Nogueira", AgenteTipo.GUARDA_MUNICIPAL, "Guarda Civil", "GCM-0205", "(14) 99812-4405"),
            ("Guarda Tiago Silveira", AgenteTipo.GUARDA_MUNICIPAL, "Guarda Civil", "GCM-0206", "(14) 99812-4406"),
            ("Capitão Rodrigo Peixoto", AgenteTipo.POLICIAL_MILITAR, "9º BPM/I", "PM-0301", "(14) 99123-7701"),
            ("Tenente Camila Fonseca", AgenteTipo.POLICIAL_MILITAR, "9º BPM/I", "PM-0302", "(14) 99123-7702"),
            ("Sargento Lucas Antunes", AgenteTipo.POLICIAL_MILITAR, "9º BPM/I", "PM-0303", "(14) 99123-7703"),
            ("Cabo Marcelo Fagundes", AgenteTipo.POLICIAL_MILITAR, "9º BPM/I", "PM-0304", "(14) 99123-7704"),
            ("Cabo Priscila Meireles", AgenteTipo.POLICIAL_MILITAR, "9º BPM/I", "PM-0305", "(14) 99123-7705"),
            ("Soldado Bruno Vasconcelos", AgenteTipo.POLICIAL_MILITAR, "9º BPM/I", "PM-0306", "(14) 99123-7706"),
            ("Soldado Daniel Faria", AgenteTipo.POLICIAL_MILITAR, "9º BPM/I", "PM-0307", "(14) 99123-7707"),
            ("Agente Douglas Martins", AgenteTipo.AGENTE_TRANSITO, "EMDURB", "AGT-0106", "(14) 99781-1127"),
            ("Agente Patricia Zanin", AgenteTipo.AGENTE_TRANSITO, "EMDURB", "AGT-0107", "(14) 99781-1128"),
            ("Guarda Leonardo Castilho", AgenteTipo.GUARDA_MUNICIPAL, "Guarda Civil", "GCM-0207", "(14) 99812-4407"),
            ("Sargento Igor Bittencourt", AgenteTipo.POLICIAL_MILITAR, "9º BPM/I", "PM-0308", "(14) 99123-7708"),
        ]

        agentes_gerados = []
        for i, (nome, tipo, orgao, mat, tel) in enumerate(nomes_agentes):
            local = LOCAIS[i % len(LOCAIS)]
            # 16 em atividade, alguns de folga, férias ou afastados
            if i < 17:
                situacao = AgenteSituacao.EM_ATIVIDADE
                lat = local["lat"] + random.uniform(-0.002, 0.002)
                lon = local["lon"] + random.uniform(-0.002, 0.002)
            elif i < 19:
                situacao = AgenteSituacao.FORA_DE_SERVICO
                lat, lon = None, None
            elif i < 21:
                situacao = AgenteSituacao.FERIAS
                lat, lon = None, None
            else:
                situacao = AgenteSituacao.AFASTADO
                lat, lon = None, None

            agente = Agente(
                nome=nome,
                matricula=mat,
                tipo=tipo,
                orgao=orgao,
                telefone=tel,
                situacao=situacao,
                latitude=round(lat, 6) if lat else None,
                longitude=round(lon, 6) if lon else None,
                ativo=True
            )
            agentes_gerados.append(agente)

        db.add_all(agentes_gerados)
        db.commit()
        logger.info(f"{len(agentes_gerados)} agentes cadastrados com sucesso!")
        logger.info("SEED DE DEMONSTRAÇÃO CONCLUÍDO COM SUCESSO!")


if __name__ == "__main__":
    seed_demo_data()
