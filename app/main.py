import os
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.connection import SessionLocal
from app.database.seed import init_db, seed_default_admin
from app.routers import (
    agentes_router,
    auth_router,
    equipamentos_router,
    pages_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("prometheus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to initialize database and seed on startup."""
    logger.info("Initializing PROMETHEUS — F.O.G.O. application...")
    init_db()
    with SessionLocal() as db:
        seed_default_admin(db)
    logger.info("System startup routine completed successfully.")
    yield
    logger.info("PROMETHEUS — F.O.G.O. shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema inteligente de monitoramento urbano para catalogação, operação em tempo real e análise preditiva.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")

if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API Routers
app.include_router(auth_router)
app.include_router(equipamentos_router)
app.include_router(agentes_router)

# Include HTML Pages Router
app.include_router(pages_router)


@app.get("/health", tags=["Infraestrutura"])
@app.get("/api/health", tags=["Infraestrutura"])
async def health_check():
    """Health check endpoint to verify API and infrastructure availability."""
    return {
        "status": "healthy",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
