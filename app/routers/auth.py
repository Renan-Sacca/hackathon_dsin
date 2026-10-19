from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse, summary="Autenticação de Usuário")
def login(
    login_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Autentica o usuário com email e senha, retornando token JWT e gravando cookie de sessão."""
    service = AuthService(db)
    user = service.authenticate(login_data)
    token_resp = service.create_user_token(user)

    # Configura cookie HTTP para navegação em templates web
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_resp.access_token}",
        httponly=False,  # Permite que JavaScript leia se necessário
        max_age=86400,
        path="/",
        samesite="lax"
    )

    return token_resp


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Usuário (Apenas Admin)"
)
def register(
    user_in: UserCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Cadastra um novo usuário no sistema. Requer privilégio de Administrador."""
    service = AuthService(db)
    new_user = service.register(user_in)
    return UserResponse.model_validate(new_user)


@router.get("/me", response_model=UserResponse, summary="Dados do Usuário Atual")
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna os dados do usuário atualmente autenticado via JWT ou Cookie."""
    return UserResponse.model_validate(current_user)


@router.post("/logout", summary="Logout de Usuário")
def logout(response: Response):
    """Limpa o cookie de autenticação."""
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Sessão encerrada com sucesso"}
