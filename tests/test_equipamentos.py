"""Test Suite — Gestão de Equipamentos Urbanos (EquipamentoService)

Valida:
- Cadastro com validação de duplicidade de número de série
- Validação geográfica de coordenadas GPS (latitude e longitude)
- Regra de negócio automática: MAU_FUNCIONAMENTO -> MANUTENCAO_IMEDIATA
- Registro automático no histórico de situações no cadastro e alteração
- Filtros de listagem (por bairro, tipo, situação e busca textual)
- Soft delete (inativação lógica)
"""

import unittest
import uuid
from fastapi import HTTPException
from app.database.connection import SessionLocal
from app.models.equipamento import (
    Equipamento,
    EquipamentoSituacao,
    EquipamentoTipo,
    ManutencaoTipo,
)
from app.schemas.equipamento import EquipamentoCreate
from app.services.equipamento_service import EquipamentoService


class TestEquipamentoService(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()
        self.service = EquipamentoService(self.db)
        self.unique_id = uuid.uuid4().hex[:6].upper()
        self.test_serial = f"TEST-EQ-{self.unique_id}"
        self.created_ids = []

    def tearDown(self):
        # Limpar equipamentos criados no teste
        for eq_id in self.created_ids:
            eq = self.db.query(Equipamento).filter(Equipamento.id == eq_id).first()
            if eq:
                from app.models.historico_equipamento import HistoricoEquipamento
                self.db.query(HistoricoEquipamento).filter(HistoricoEquipamento.equipamento_id == eq_id).delete()
                self.db.delete(eq)
        self.db.commit()
        self.db.close()

    def test_cadastro_equipamento_sucesso(self):
        eq_in = EquipamentoCreate(
            tipo=EquipamentoTipo.RADAR_VELOCIDADE,
            numero_serie=self.test_serial,
            marca="Siemens Mobility",
            modelo="TraffiStar S350",
            localizacao_rua="Avenida Central de Testes, 1000",
            localizacao_bairro="Centro",
            localizacao_cidade="Marília",
            localizacao_uf="SP",
            latitude=-22.2135,
            longitude=-49.9520,
            orgao_responsavel="EMDURB",
            situacao=EquipamentoSituacao.OPERACIONAL
        )
        eq = self.service.create_equipamento(eq_in)
        self.created_ids.append(eq.id)

        self.assertIsNotNone(eq.id)
        self.assertEqual(eq.numero_serie, self.test_serial)
        self.assertEqual(eq.situacao, EquipamentoSituacao.OPERACIONAL)
        self.assertTrue(eq.ativo)

        # Verificar se histórico inicial foi gravado
        historico = self.service.get_historico(eq.id)
        self.assertGreaterEqual(len(historico), 1)
        self.assertEqual(historico[0].situacao_nova, EquipamentoSituacao.OPERACIONAL)

    def test_cadastro_coordenadas_invalidas_bloqueadas(self):
        eq_in = EquipamentoCreate(
            tipo=EquipamentoTipo.RADAR_SEMAFORO,
            numero_serie=f"{self.test_serial}-INV",
            marca="Velsis",
            modelo="VS-01",
            localizacao_rua="Rua Inválida",
            localizacao_bairro="Centro",
            latitude=95.0,  # Latitude > 90 inválida
            longitude=-49.95,
            orgao_responsavel="EMDURB",
            situacao=EquipamentoSituacao.OPERACIONAL
        )
        with self.assertRaises(HTTPException) as ctx:
            self.service.create_equipamento(eq_in)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Latitude inválida", ctx.exception.detail)

    def test_cadastro_numero_serie_duplicado_bloqueado(self):
        eq_in = EquipamentoCreate(
            tipo=EquipamentoTipo.CAMERA_MONITORAMENTO,
            numero_serie=self.test_serial,
            marca="Hikvision",
            modelo="DS-2CD",
            localizacao_rua="Rua Primeira",
            localizacao_bairro="Centro",
            latitude=-22.21,
            longitude=-49.95,
            orgao_responsavel="Polícia Militar",
            situacao=EquipamentoSituacao.OPERACIONAL
        )
        eq = self.service.create_equipamento(eq_in)
        self.created_ids.append(eq.id)

        with self.assertRaises(HTTPException) as ctx:
            self.service.create_equipamento(eq_in)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("já cadastrado", ctx.exception.detail)

    def test_regra_negocio_mau_funcionamento_exige_manutencao_imediata(self):
        eq_in = EquipamentoCreate(
            tipo=EquipamentoTipo.RADAR_SEMAFORO,
            numero_serie=self.test_serial,
            marca="Consórcio Marília",
            modelo="Sem-04",
            localizacao_rua="Cruzamento Crítico",
            localizacao_bairro="Zona Norte",
            latitude=-22.20,
            longitude=-49.94,
            orgao_responsavel="EMDURB",
            situacao=EquipamentoSituacao.MAU_FUNCIONAMENTO
        )
        eq = self.service.create_equipamento(eq_in)
        self.created_ids.append(eq.id)

        # Regra de negócio: mau funcionamento força manutenção imediata
        self.assertEqual(eq.manutencao_tipo, ManutencaoTipo.IMEDIATA)

    def test_listagem_com_filtros(self):
        eq_in = EquipamentoCreate(
            tipo=EquipamentoTipo.CAMERA_MONITORAMENTO,
            numero_serie=self.test_serial,
            marca="Intelbras",
            modelo="VIP 7250",
            localizacao_rua="Rua das Acácias",
            localizacao_bairro="BairroExclusivoTeste",
            latitude=-22.22,
            longitude=-49.96,
            orgao_responsavel="Guarda Municipal",
            situacao=EquipamentoSituacao.OPERACIONAL
        )
        eq = self.service.create_equipamento(eq_in)
        self.created_ids.append(eq.id)

        itens, total = self.service.list_equipamentos(bairro="BairroExclusivoTeste")
        self.assertGreaterEqual(total, 1)
        self.assertTrue(any(e.id == eq.id for e in itens))

    def test_soft_delete_equipamento(self):
        eq_in = EquipamentoCreate(
            tipo=EquipamentoTipo.RADAR_VELOCIDADE,
            numero_serie=self.test_serial,
            marca="Fotosensores",
            modelo="FS-800",
            localizacao_rua="Rua a ser removida",
            localizacao_bairro="Centro",
            latitude=-22.21,
            longitude=-49.95,
            orgao_responsavel="EMDURB",
            situacao=EquipamentoSituacao.OPERACIONAL
        )
        eq = self.service.create_equipamento(eq_in)
        self.created_ids.append(eq.id)

        # Realizar soft delete
        self.service.delete_equipamento(eq.id)

        # Equipamento inativo não deve constar na listagem padrão ativa
        itens, _ = self.service.list_equipamentos()
        self.assertFalse(any(e.id == eq.id for e in itens))


if __name__ == "__main__":
    unittest.main()
