from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User, UserType
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_users(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = True) -> List[User]:
        stmt = select(User)
        if apenas_ativos:
            stmt = stmt.where(User.ativo.is_(True))
        stmt = stmt.offset(skip).limit(limit).order_by(User.id.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(self, user_in: UserCreate) -> User:
        user = User(
            nome=user_in.nome,
            email=user_in.email,
            senha_hash=get_password_hash(user_in.senha),
            tipo=user_in.tipo,
            ativo=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, user_in: UserUpdate) -> User:
        update_data = user_in.model_dump(exclude_unset=True)
        if "senha" in update_data and update_data["senha"]:
            user.senha_hash = get_password_hash(update_data.pop("senha"))

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete(self, user: User) -> User:
        user.ativo = False
        self.db.commit()
        self.db.refresh(user)
        return user
