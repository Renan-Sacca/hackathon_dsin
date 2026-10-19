from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models.user import User, UserType

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_token_from_request(
    request: Request,
    header_token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[str]:
    """Extract token from Authorization header or from cookies."""
    if header_token:
        return header_token

    # Check cookies for access token
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            return cookie_token[7:]
        return cookie_token

    return None


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """Validate token and return current active user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_id_int = int(user_id)
        stmt = select(User).where(User.id == user_id_int)
    except ValueError:
        # Fallback if subject is email
        stmt = select(User).where(User.email == user_id)

    user = db.execute(stmt).scalar_one_or_none()
    if user is None:
        raise credentials_exception

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado pelo administrador"
        )

    return user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Validate that current user has ADMIN privileges."""
    if current_user.tipo != UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: permissão de administrador necessária"
        )
    return current_user
