"""API and HTML routers package."""
from app.routers.auth import router as auth_router
from app.routers.equipamentos import router as equipamentos_router
from app.routers.agentes import router as agentes_router
from app.routers.dashboard import router as dashboard_router
from app.routers.predictive import router as predictive_router
from app.routers.pages import router as pages_router

__all__ = [
    "auth_router",
    "equipamentos_router",
    "agentes_router",
    "dashboard_router",
    "predictive_router",
    "pages_router",
]

