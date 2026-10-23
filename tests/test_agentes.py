"""Test Suite — Gestão de Agentes de Campo (AgenteService)

Valida:
- Cadastro de novos agentes de trânsito, guarda e polícia
- Validação geográfica de coordenadas do agente
- Bloqueio de matrícula duplicada
- Atualização cadastral e alteração de situação/turno
- Filtros por situação operacional, órgão e busca textual
- Soft delete (inativação lógica)
"""

import unittest
import uuid
from fastapi import HTTPException
from app.database.connection import SessionLocal
from app.models.agente import Agente, AgenteSituacao, AgenteTipo
from app.schemas.agente import AgenteCreate, AgenteUpdate
from app.services.agente_service import AgenteService


class TestAgenteService(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()
        self.service = AgenteService(self.db)
        self.unique_id = uuid.uuid4().hex[:6].upper()
        self.test_matricula = f"AGT-{self.unique_id}"
        self.created_ids = []

    def tearDown(self):
        # Limpar agentes criados durante os testes
        for agt_id in self.created_ids:
            agt = self.db.query(Agente).filter(Agente.id == agt_id).first()
            if agt:
                self.db.delete(agt)
        self.db.commit()
        self.db.close()

    def test_cadastro_agente_sucesso(self):
        agt_in = AgenteCreate(
            nome="Agente Marcos Oliveira",
            matricula=self.test_matricula,
            tipo=AgenteTipo.AGENTE_TRANSITO,
            orgao="EMDURB",
            telefone="(14) 99888-7766",
            situacao=AgenteSituacao.EM_ATIVIDADE,
            latitude=-22.2140,
            longitude=-49.9530
        )
        agente = self.service.create_agente(agt_in)
        self.created_ids.append(agente.id)

        self.assertIsNotNone(agente.id)
        self.assertEqual(agente.matricula, self.test_matricula)
        self.assertEqual(agente.situacao, AgenteSituacao.EM_ATIVIDADE)
        self.assertTrue(agente.ativo)

    def test_cadastro_matricula_duplicada_bloqueada(self):
        agt_in = AgenteCreate(
            nome="Agente Original",
            matricula=self.test_matricula,
            tipo=AgenteTipo.GUARDA_MUNICIPAL,
            orgao="Guarda Municipal",
            latitude=-22.21,
            longitude=-49.95
        )
        agente = self.service.create_agente(agt_in)
        self.created_ids.append(agente.id)

        with self.assertRaises(HTTPException) as ctx:
            self.service.create_agente(agt_in)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("já cadastrado", ctx.exception.detail)

    def test_cadastro_coordenadas_invalidas_bloqueadas(self):
        agt_in = AgenteCreate(
            nome="Agente Fora do Mapa",
            matricula=f"{self.test_matricula}-INV",
            tipo=AgenteTipo.POLICIAL_MILITAR,
            orgao="Polícia Militar",
            latitude=-120.0,  # Inválido (< -90)
            longitude=-49.95
        )
        with self.assertRaises(HTTPException) as ctx:
            self.service.create_agente(agt_in)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Latitude inválida", ctx.exception.detail)

    def test_atualizacao_agente(self):
        agt_in = AgenteCreate(
            nome="Agente Para Atualizar",
            matricula=self.test_matricula,
            tipo=AgenteTipo.AGENTE_TRANSITO,
            orgao="EMDURB",
            situacao=AgenteSituacao.EM_ATIVIDADE
        )
        agente = self.service.create_agente(agt_in)
        self.created_ids.append(agente.id)

        update_in = AgenteUpdate(
            situacao=AgenteSituacao.FORA_DE_SERVICO,
            telefone="(14) 91111-2222"
        )
        updated = self.service.update_agente(agente.id, update_in)
        self.assertEqual(updated.situacao, AgenteSituacao.FORA_DE_SERVICO)
        self.assertEqual(updated.telefone, "(14) 91111-2222")

    def test_listagem_com_filtros_e_busca(self):
        agt_in = AgenteCreate(
            nome="Agente Nome Exclusivo Para Teste",
            matricula=self.test_matricula,
            tipo=AgenteTipo.GUARDA_MUNICIPAL,
            orgao="Guarda Municipal",
            situacao=AgenteSituacao.EM_ATIVIDADE
        )
        agente = self.service.create_agente(agt_in)
        self.created_ids.append(agente.id)

        itens, total = self.service.list_agentes(busca="Exclusivo Para Teste")
        self.assertGreaterEqual(total, 1)
        self.assertTrue(any(a.id == agente.id for a in itens))

    def test_soft_delete_agente(self):
        agt_in = AgenteCreate(
            nome="Agente A Inativar",
            matricula=self.test_matricula,
            tipo=AgenteTipo.AGENTE_TRANSITO,
            orgao="EMDURB"
        )
        agente = self.service.create_agente(agt_in)
        self.created_ids.append(agente.id)

        self.service.delete_agente(agente.id)

        # Não deve constar na listagem de ativos
        itens, _ = self.service.list_agentes()
        self.assertFalse(any(a.id == agente.id for a in itens))


if __name__ == "__main__":
    unittest.main()
