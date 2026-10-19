import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import get_password_hash
from app.database.base import Base
from app.database.connection import engine, SessionLocal
from app.models.user import User, UserType

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create all database tables based on declared models."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


def seed_default_admin(db: Session) -> User:
    """Seed the default administrator if not present."""
    stmt = select(User).where(User.email == settings.DEFAULT_ADMIN_EMAIL)
    existing_admin = db.execute(stmt).scalar_one_or_none()

    if existing_admin:
        logger.info(f"Default admin '{settings.DEFAULT_ADMIN_EMAIL}' already exists.")
        return existing_admin

    logger.info(f"Creating default admin '{settings.DEFAULT_ADMIN_EMAIL}'...")
    admin = User(
        nome=settings.DEFAULT_ADMIN_NAME,
        email=settings.DEFAULT_ADMIN_EMAIL,
        senha_hash=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
        tipo=UserType.ADMIN,
        ativo=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    logger.info(f"Default admin created successfully with ID {admin.id}.")
    return admin


def run_seed() -> None:
    """Entry point to run DB initialization and seeding."""
    init_db()
    with SessionLocal() as db:
        seed_default_admin(db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_seed()
