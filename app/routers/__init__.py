"""API and HTML routers package."""
from app.routers.auth import router as auth_router
from app.routers.equipamentos import router as equipamentos_router
from app.routers.agentes import router as agentes_router
from app.routers.pages import router as pages_router

__all__ = [
    "auth_router",
    "equipamentos_router",
    "agentes_router",
    "pages_router",
]
