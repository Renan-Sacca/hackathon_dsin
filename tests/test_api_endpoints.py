"""Test Suite — Integração HTTP de Endpoints RESTful (PROMETHEUS API)

Valida o ciclo completo de vida da API HTTP contra o servidor ativo:
- Disponibilidade da documentação OpenAPI/Swagger
- Login automatizado com emissão de token JWT Bearer
- Acesso autenticado a endpoints protegidos (/me, /equipamentos, /agentes)
- Endpoints operacionais do Dashboard em tempo real
- Endpoints analíticos da Cidade Preditiva (risco, custos, reforço)
"""

import json
import unittest
import urllib.request
import urllib.error


class TestApiEndpointsIntegration(unittest.TestCase):

    BASE_URL = "http://localhost:8000"

    @classmethod
    def setUpClass(cls):
        # Realiza login para obter o Bearer Token que será compartilhado nos testes
        login_payload = json.dumps({
            "email": "admin@prometheus.gov",
            "senha": "admin123"
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{cls.BASE_URL}/api/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as response:
                cls.token = ""
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    cls.token = data.get("access_token", "")
        except urllib.error.URLError:
            cls.token = ""

    def _make_request(self, path: str, method: str = "GET", body: dict = None, auth: bool = True):
        headers = {"Content-Type": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(f"{self.BASE_URL}{path}", data=data, headers=headers, method=method)
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}

    def test_01_openapi_schema(self):
        req = urllib.request.Request(f"{self.BASE_URL}/openapi.json")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("openapi", data)
            self.assertIn("paths", data)

    def test_02_login_e_token_valido(self):
        self.assertTrue(bool(self.token), "Token JWT não foi obtido durante o login inicial.")

    def test_03_perfil_usuario_autenticado(self):
        status_code, data = self._make_request("/api/auth/me")
        self.assertEqual(status_code, 200)
        self.assertEqual(data.get("email"), "admin@prometheus.gov")

    def test_04_endpoint_dashboard_metricas(self):
        status_code, data = self._make_request("/api/dashboard/metricas")
        self.assertEqual(status_code, 200)
        self.assertIn("total_equipamentos", data)
        self.assertIn("operacionais", data)

    def test_05_endpoint_dashboard_mapa(self):
        status_code, data = self._make_request("/api/dashboard/mapa")
        self.assertEqual(status_code, 200)
        self.assertIn("equipamentos", data)
        self.assertIn("agentes", data)

    def test_06_endpoint_listar_equipamentos(self):
        status_code, data = self._make_request("/api/equipamentos?limit=10")
        self.assertEqual(status_code, 200)
        self.assertIn("items", data)
        self.assertIn("total", data)

    def test_07_endpoint_listar_agentes(self):
        status_code, data = self._make_request("/api/agentes?limit=10")
        self.assertEqual(status_code, 200)
        self.assertIn("items", data)
        self.assertIn("total", data)

    def test_08_endpoint_preditivo_resumo(self):
        status_code, data = self._make_request("/api/preditivo/resumo")
        self.assertEqual(status_code, 200)
        self.assertIn("bairro_maior_risco", data)
        self.assertIn("total_equipamentos_em_risco", data)

    def test_09_endpoint_preditivo_risco_regioes(self):
        status_code, data = self._make_request("/api/preditivo/risco-regioes")
        self.assertEqual(status_code, 200)
        self.assertIsInstance(data, list)
        if len(data) > 0:
            self.assertIn("bairro", data[0])
            self.assertIn("score_geral", data[0])

    def test_10_endpoint_preditivo_custo_projecao(self):
        status_code, data = self._make_request("/api/preditivo/custo-projecao")
        self.assertEqual(status_code, 200)
        self.assertIn("projecao_30_dias", data)
        self.assertIn("projecao_60_dias", data)
        self.assertIn("projecao_90_dias", data)


if __name__ == "__main__":
    unittest.main()
