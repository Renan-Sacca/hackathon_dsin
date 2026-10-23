"""Test Suite — Histórico de Manutenções dos Equipamentos

Valida:
- Consulta do histórico de manutenções por equipamento (GET /api/equipamentos/{id}/historico)
- Registro de nova intervenção técnica de manutenção (POST /api/equipamentos/{id}/historico)
- Atualização automática da situação do equipamento e registro de custos/downtime
- Registro automático de histórico na alteração de situação via update
"""

import unittest
from datetime import datetime, timezone
from app.database.connection import SessionLocal
from app.models.equipamento import Equipamento, EquipamentoSituacao, EquipamentoTipo, ManutencaoTipo
from app.schemas.equipamento import EquipamentoUpdate, HistoricoManutencaoCreate
from app.services.equipamento_service import EquipamentoService


class TestHistoricoManutencao(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()
        self.service = EquipamentoService(self.db)

    def tearDown(self):
        self.db.close()

    def test_consulta_historico_equipamento(self):
        # Buscar primeiro equipamento
        eq = self.db.query(Equipamento).filter(Equipamento.ativo.is_(True)).first()
        self.assertIsNotNone(eq, "Deve existir ao menos um equipamento no banco.")

        historico = self.service.get_historico(eq.id)
        self.assertIsInstance(historico, list)
        self.assertGreater(len(historico), 0, "Equipamento deve possuir histórico registrado.")

        item = historico[0]
        self.assertEqual(item.equipamento_id, eq.id)
        self.assertIsNotNone(item.data_mudanca)
        self.assertIsNotNone(item.situacao_nova)

    def test_registro_nova_manutencao(self):
        eq = self.db.query(Equipamento).filter(Equipamento.ativo.is_(True)).first()
        self.assertIsNotNone(eq)

        novo_evento = HistoricoManutencaoCreate(
            situacao_nova=EquipamentoSituacao.OPERACIONAL,
            motivo="Troca preventiva de fiação e revisão elétrica geral",
            custo_manutencao=450.00,
            tempo_inatividade_horas=3.5
        )

        registro = self.service.add_historico(eq.id, novo_evento)
        self.assertIsNotNone(registro.id)
        self.assertEqual(registro.equipamento_id, eq.id)
        self.assertEqual(registro.situacao_nova, EquipamentoSituacao.OPERACIONAL)
        self.assertEqual(registro.custo_manutencao, 450.00)
        self.assertEqual(registro.tempo_inatividade_horas, 3.5)
        self.assertEqual(registro.motivo, "Troca preventiva de fiação e revisão elétrica geral")

        # Verificar se equipamento teve a situação atualizada no banco
        self.db.refresh(eq)
        self.assertEqual(eq.situacao, EquipamentoSituacao.OPERACIONAL)
        self.assertEqual(eq.manutencao_tipo, ManutencaoTipo.NENHUMA)

    def test_auto_registro_historico_ao_atualizar_situacao(self):
        eq = self.db.query(Equipamento).filter(Equipamento.ativo.is_(True)).first()
        self.assertIsNotNone(eq)

        qtd_antes = len(self.service.get_historico(eq.id))

        # Altera para uma situação diferente da atual
        nova_situacao = (
            EquipamentoSituacao.MANUTENCAO
            if eq.situacao != EquipamentoSituacao.MANUTENCAO
            else EquipamentoSituacao.MAU_FUNCIONAMENTO
        )
        update_data = EquipamentoUpdate(situacao=nova_situacao)
        self.service.update_equipamento(eq.id, update_data)

        historico_depois = self.service.get_historico(eq.id)
        self.assertEqual(len(historico_depois), qtd_antes + 1)
        self.assertEqual(historico_depois[0].situacao_nova, nova_situacao)


if __name__ == "__main__":
    unittest.main()
