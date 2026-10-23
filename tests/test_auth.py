"""Test Suite — Autenticação e Segurança (AuthService & Security)

Valida:
- Registro de novos usuários com sanitização e validação de duplicidade
- Autenticação com verificação de hash bcrypt
- Bloqueio de senhas incorretas e usuários inativos
- Emissão e integridade de tokens JWT assinados
"""

import unittest
import uuid
from fastapi import HTTPException
from app.core.security import decode_access_token, verify_password
from app.database.connection import SessionLocal
from app.models.user import User, UserType
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import AuthService


class TestAuthService(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()
        self.service = AuthService(self.db)
        self.unique_id = uuid.uuid4().hex[:8]
        self.test_email = f"test.user.{self.unique_id}@prometheus.gov"
        self.test_password = "SecretPassword123!"

    def tearDown(self):
        # Limpar registros criados durante o teste
        user = self.db.query(User).filter(User.email == self.test_email).first()
        if user:
            self.db.delete(user)
            self.db.commit()
        self.db.close()

    def test_registro_usuario_sucesso(self):
        user_in = UserCreate(
            nome="Operador Teste Unificado",
            email=self.test_email,
            senha=self.test_password,
            tipo=UserType.OPERADOR
        )
        user = self.service.register(user_in)

        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, self.test_email)
        self.assertEqual(user.tipo, UserType.OPERADOR)
        self.assertTrue(user.ativo)
        # Garante que a senha não foi salva em texto plano
        self.assertNotEqual(user.senha_hash, self.test_password)
        self.assertTrue(verify_password(self.test_password, user.senha_hash))

    def test_registro_email_duplicado_lanca_excecao(self):
        user_in = UserCreate(
            nome="Primeiro Usuario",
            email=self.test_email,
            senha=self.test_password,
            tipo=UserType.OPERADOR
        )
        self.service.register(user_in)

        # Tentativa de registrar mesmo e-mail
        with self.assertRaises(HTTPException) as ctx:
            self.service.register(user_in)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("já está em uso", ctx.exception.detail)

    def test_autenticacao_sucesso(self):
        user_in = UserCreate(
            nome="Usuario Autenticacao",
            email=self.test_email,
            senha=self.test_password,
            tipo=UserType.OPERADOR
        )
        self.service.register(user_in)

        login_data = UserLogin(email=self.test_email, senha=self.test_password)
        auth_user = self.service.authenticate(login_data)
        self.assertIsNotNone(auth_user)
        self.assertEqual(auth_user.email, self.test_email)

    def test_autenticacao_senha_incorreta(self):
        user_in = UserCreate(
            nome="Usuario Senha Incorreta",
            email=self.test_email,
            senha=self.test_password,
            tipo=UserType.OPERADOR
        )
        self.service.register(user_in)

        login_data = UserLogin(email=self.test_email, senha="SenhaErrada999")
        with self.assertRaises(HTTPException) as ctx:
            self.service.authenticate(login_data)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("E-mail ou senha incorretos", ctx.exception.detail)

    def test_autenticacao_usuario_inativo_bloqueado(self):
        user_in = UserCreate(
            nome="Usuario Inativo",
            email=self.test_email,
            senha=self.test_password,
            tipo=UserType.OPERADOR
        )
        user = self.service.register(user_in)
        user.ativo = False
        self.db.commit()

        login_data = UserLogin(email=self.test_email, senha=self.test_password)
        with self.assertRaises(HTTPException) as ctx:
            self.service.authenticate(login_data)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("desativado", ctx.exception.detail)

    def test_geracao_e_validacao_token_jwt(self):
        user_in = UserCreate(
            nome="Token Tester",
            email=self.test_email,
            senha=self.test_password,
            tipo=UserType.ADMIN
        )
        user = self.service.register(user_in)

        token_response = self.service.create_user_token(user)
        self.assertIsNotNone(token_response.access_token)
        self.assertEqual(token_response.token_type, "bearer")
        self.assertEqual(token_response.user.email, self.test_email)

        # Decodificar e validar claims
        payload = decode_access_token(token_response.access_token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get("sub"), str(user.id))
        self.assertEqual(payload.get("email"), self.test_email)
        self.assertEqual(payload.get("tipo"), UserType.ADMIN.value)


if __name__ == "__main__":
    unittest.main()
