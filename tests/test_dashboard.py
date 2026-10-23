"""Test Suite — Central de Operações e Dashboard (DashboardService)

Valida:
- Agregação de KPIs operacionais da cidade em tempo real
- Estruturação dos marcadores de mapa para Leaflet (equipamentos e viaturas)
- Lista de alertas operacionais ativos priorizados por criticidade
- Avaliação de integridade e saúde operacional por bairro/região
"""

import unittest
from app.database.connection import SessionLocal
from app.services.dashboard_service import DashboardService


class TestDashboardService(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()
        self.service = DashboardService(self.db)

    def tearDown(self):
        self.db.close()

    def test_kpis_metricas_dashboard(self):
        kpis = self.service.get_metrics()
        self.assertIsInstance(kpis, dict)

        # Campos obrigatórios do resumo executivo
        self.assertIn("total_equipamentos", kpis)
        self.assertIn("operacionais", kpis)
        self.assertIn("indisponiveis", kpis)
        self.assertIn("percentual_disponibilidade", kpis)
        self.assertIn("manutencao_imediata", kpis)
        self.assertIn("total_agentes", kpis)
        self.assertIn("agentes_em_atividade", kpis)
        self.assertIn("por_tipo", kpis)
        self.assertIn("por_situacao", kpis)

        # Validação numérica
        self.assertGreaterEqual(kpis["total_equipamentos"], 0)
        self.assertGreaterEqual(kpis["operacionais"], 0)
        self.assertGreaterEqual(kpis["percentual_disponibilidade"], 0.0)
        self.assertLessEqual(kpis["percentual_disponibilidade"], 100.0)

    def test_mapa_dados_geolocalizados(self):
        map_data = self.service.get_map_data()
        self.assertIsInstance(map_data, dict)
        self.assertIn("equipamentos", map_data)
        self.assertIn("agentes", map_data)

        # Verificar se os equipamentos possuem coordenadas para renderização
        for eq in map_data["equipamentos"]:
            self.assertIn("id", eq)
            self.assertIn("latitude", eq)
            self.assertIn("longitude", eq)
            self.assertIsNotNone(eq["latitude"])
            self.assertIsNotNone(eq["longitude"])
            self.assertIn("tipo", eq)
            self.assertIn("situacao", eq)

        # Verificar se os agentes em atividade possuem coordenadas
        for ag in map_data["agentes"]:
            self.assertIn("id", ag)
            self.assertIn("latitude", ag)
            self.assertIn("longitude", ag)
            self.assertIn("nome", ag)

    def test_alertas_priorizados(self):
        alerts = self.service.get_alerts()
        self.assertIsInstance(alerts, list)

        # Se houver alertas, validar schema esperado
        for a in alerts:
            self.assertIn("equipamento_id", a)
            self.assertIn("numero_serie", a)
            self.assertIn("tipo", a)
            self.assertIn("bairro", a)
            self.assertIn("severidade", a)
            self.assertIn("prioridade", a)

    def test_saude_das_regioes(self):
        regioes = self.service.get_regions_health()
        self.assertIsInstance(regioes, list)
        self.assertGreater(len(regioes), 0, "Deve haver bairros avaliados no sistema.")

        for r in regioes:
            self.assertIn("bairro", r)
            self.assertIn("total", r)
            self.assertIn("operacionais", r)
            self.assertIn("problemas", r)
            self.assertIn("percentual_saude", r)
            self.assertIn("lat", r)
            self.assertIn("lon", r)
            self.assertGreaterEqual(r["percentual_saude"], 0.0)
            self.assertLessEqual(r["percentual_saude"], 100.0)


if __name__ == "__main__":
    unittest.main()
