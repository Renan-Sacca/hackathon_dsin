"""Test Suite — PARTE 3 — Cidade Preditiva (PROMETHEUS F.O.G.O.)

Valida todos os requisitos especificados em TASKS.md:
- P3-TEST-01: Cálculo do índice de risco por região com dados históricos
- P3-TEST-02: Identificação de equipamentos com padrão de falha recorrente
- P3-TEST-03: Geração de alertas preventivos
- P3-TEST-04: Visualização e estrutura do mapa de calor de risco
- P3-TEST-05: Explicabilidade das previsões (dados usados e justificativas)
- P3-TEST-06: Correlação de falhas simultâneas em zona de infraestrutura compartilhada
- P3-TEST-07: Projeção de custo de manutenção (30/60/90 dias) compatível com histórico real
- P3-TEST-08: Score de prioridade de instalação maior em regiões de alto risco
"""

import unittest
from app.database.connection import SessionLocal
from app.services.correlacao_service import CorrelacaoService
from app.services.custo_service import CustoService
from app.services.predictive_service import PredictiveService
from app.services.prioridade_instalacao_service import PrioridadeInstalacaoService
from app.services.reforco_service import ReforcoService


class TestCidadePreditiva(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()
        self.pred_service = PredictiveService(self.db)
        self.reforco_service = ReforcoService(self.db)
        self.correlacao_service = CorrelacaoService(self.db)
        self.custo_service = CustoService(self.db)
        self.prioridade_service = PrioridadeInstalacaoService(self.db)

    def tearDown(self):
        self.db.close()

    # -------------------------------------------------------------------------
    # P3-TEST-01: Testar cálculo do índice de risco por região com dados históricos
    # -------------------------------------------------------------------------
    def test_p3_01_calculo_indice_risco_regioes(self):
        risco_regioes = self.pred_service.calcular_risco_regioes(dias=180)
        self.assertIsInstance(risco_regioes, list)
        self.assertGreater(len(risco_regioes), 0, "Deveria retornar pelo menos uma região calculada.")

        # Verificar se campos obrigatórios existem e estão dentro da faixa esperada
        for r in risco_regioes:
            self.assertIn("bairro", r)
            self.assertIn("score_geral", r)
            self.assertIn("nivel_risco", r)
            self.assertIn("periodo_mais_critico", r)
            self.assertIn("detalhes_periodos", r)
            self.assertGreaterEqual(r["score_geral"], 0.0)
            self.assertLessEqual(r["score_geral"], 100.0)

            # Verificar que os 4 períodos do dia foram calculados
            periodos = r["detalhes_periodos"]
            for p in ["manha", "tarde", "noite", "madrugada"]:
                self.assertIn(p, periodos)
                self.assertGreaterEqual(periodos[p]["score_risco"], 0.0)

        # Regiões devem vir ordenadas por maior score no topo
        scores = [r["score_geral"] for r in risco_regioes]
        self.assertEqual(scores, sorted(scores, reverse=True), "Regiões devem vir ordenadas por maior risco.")

    # -------------------------------------------------------------------------
    # P3-TEST-02: Testar identificação de equipamentos com padrão de falha recorrente
    # -------------------------------------------------------------------------
    def test_p3_02_identificacao_padrao_falha_recorrente(self):
        previsoes = self.pred_service.prever_falhas_equipamentos()
        self.assertIsInstance(previsoes, list)
        self.assertGreater(len(previsoes), 0, "Deveria identificar equipamentos com histórico de falhas recorrentes.")

        for p in previsoes:
            self.assertIn("equipamento_id", p)
            self.assertIn("numero_serie", p)
            self.assertIn("mtbf_dias", p)
            self.assertIn("probabilidade_falha_percentual", p)
            self.assertIn("data_prevista_proxima_falha", p)
            self.assertGreater(p["total_falhas_registradas"], 1)
            self.assertGreater(p["mtbf_dias"], 0.0)
            self.assertGreaterEqual(p["probabilidade_falha_percentual"], 0.0)
            self.assertLessEqual(p["probabilidade_falha_percentual"], 100.0)

        # Equipamento no topo da lista deve ter alta probabilidade
        self.assertGreaterEqual(previsoes[0]["probabilidade_falha_percentual"], 50.0)

    # -------------------------------------------------------------------------
    # P3-TEST-03: Testar geração de alertas preventivos
    # -------------------------------------------------------------------------
    def test_p3_03_geracao_alertas_preventivos(self):
        alertas = self.pred_service.gerar_alertas_preventivos()
        self.assertIsInstance(alertas, list)
        self.assertGreater(len(alertas), 0, "Deveria gerar alertas preventivos proativos.")

        for a in alertas:
            self.assertIn("tipo", a)
            self.assertIn("severidade", a)
            self.assertIn("titulo", a)
            self.assertIn("mensagem", a)
            self.assertIn("acao_recomendada", a)
            self.assertIn(a["severidade"], ["CRITICO", "ALTO", "MODERADO"])

    # -------------------------------------------------------------------------
    # P3-TEST-04: Testar visualização do mapa de calor de risco
    # -------------------------------------------------------------------------
    def test_p3_04_visualizacao_mapa_risco(self):
        risco_regioes = self.pred_service.calcular_risco_regioes(dias=180)
        # Cada região deve possuir coordenadas válidas para renderização no mapa
        for r in risco_regioes:
            self.assertIsInstance(r["latitude"], float)
            self.assertIsInstance(r["longitude"], float)
            self.assertNotEqual(r["latitude"], 0.0)
            self.assertNotEqual(r["longitude"], 0.0)

    # -------------------------------------------------------------------------
    # P3-TEST-05: Verificar que as previsões são explicáveis (quais dados foram usados e por quê)
    # -------------------------------------------------------------------------
    def test_p3_05_explicabilidade_previsoes(self):
        # 1. Explicabilidade de Risco
        risco_regioes = self.pred_service.calcular_risco_regioes()
        for r in risco_regioes:
            self.assertIn("explicacao", r)
            self.assertTrue(len(r["explicacao"]) > 20, "A explicação de risco regional deve ser descritiva.")

        # 2. Explicabilidade de Falha MTBF
        previsoes = self.pred_service.prever_falhas_equipamentos()
        for p in previsoes:
            self.assertIn("explicacao", p)
            self.assertIn("MTBF", p["explicacao"])
            self.assertIn("falhas", p["explicacao"])

        # 3. Explicabilidade de Reforço de Agentes
        reforcos = self.reforco_service.estimar_reforco_agentes()
        if reforcos:
            self.assertIn("justificativa", reforcos[0])
            self.assertTrue(len(reforcos[0]["justificativa"]) > 20)

    # -------------------------------------------------------------------------
    # P3-TEST-06: Testar correlação de falhas simultâneas em zona suspeita
    # -------------------------------------------------------------------------
    def test_p3_06_correlacao_falhas_zona_suspeita(self):
        zonas = self.correlacao_service.detectar_zonas_correlacao(dias=180, janela_horas=2.0)
        self.assertIsInstance(zonas, list)
        self.assertGreater(len(zonas), 0, "Deveria detectar a zona de falha simultânea inserida no histórico.")

        zona_top = zonas[0]
        self.assertIn("bairro", zona_top)
        self.assertIn("score_correlacao", zona_top)
        self.assertIn("causa_provavel", zona_top)
        self.assertIn("equipamentos", zona_top)
        self.assertGreaterEqual(zona_top["total_equipamentos_afetados"], 2, "A zona deve ter 2+ equipamentos afetados.")
        self.assertGreaterEqual(zona_top["total_episodios_simultaneos"], 1)

    # -------------------------------------------------------------------------
    # P3-TEST-07: Testar projeção de custo: coerência 30/60/90 dias com histórico real
    # -------------------------------------------------------------------------
    def test_p3_07_projecao_custo_manutencao(self):
        custos = self.custo_service.projetar_custos_manutencao(dias_historico=180)
        self.assertIsInstance(custos, dict)
        self.assertIn("custo_real_acumulado", custos)
        self.assertIn("projecao_30_dias", custos)
        self.assertIn("projecao_60_dias", custos)
        self.assertIn("projecao_90_dias", custos)

        # Projeção de 90 dias deve ser acumulativamente maior que 60 dias, e 60 maior que 30
        self.assertGreaterEqual(custos["projecao_60_dias"], custos["projecao_30_dias"])
        self.assertGreaterEqual(custos["projecao_90_dias"], custos["projecao_60_dias"])

        # Custo real acumulado deve ser positivo baseado no seed
        self.assertGreater(custos["custo_real_acumulado"], 0.0)

    # -------------------------------------------------------------------------
    # P3-TEST-08: Testar score de prioridade de instalação (região de alto risco > região calma)
    # -------------------------------------------------------------------------
    def test_p3_08_prioridade_instalacao_score(self):
        fila = self.prioridade_service.calcular_prioridade_instalacao()
        self.assertIsInstance(fila, list)
        self.assertGreater(len(fila), 0, "Deveria haver equipamentos não instalados na fila de priorização.")

        # Verificar se está ordenado de forma decrescente pelo score
        scores = [item["score_urgencia"] for item in fila]
        self.assertEqual(scores, sorted(scores, reverse=True), "Fila deve estar ordenada por maior score.")

        # Verificar que o equipamento para o Centro ou Nova Marília (alto risco) tem score superior a regiões calmas
        item_top = fila[0]
        self.assertGreater(item_top["score_risco_bairro"], 30.0, "O item do topo deve ter destino com risco considerável.")
        self.assertIn("justificativa", item_top)


if __name__ == "__main__":
    unittest.main()
