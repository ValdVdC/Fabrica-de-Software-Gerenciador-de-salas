"""
Ponto de entrada do FastAPI para o SIGAAS.
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
)

# Configuração de CORS para consumo pelo Angular SPA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
def docs_redirect():
    return RedirectResponse(url=f"{settings.API_V1_STR}/docs")


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url=settings.API_V1_STR)



@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
    }


@app.get(f"{settings.API_V1_STR}", tags=["Root"])
def root_api():
    return {
        "message": "Bem-vindo à API do SIGAAS - Sistema de Gestão de Salas e Escalas com IA",
        "docs": f"{settings.API_V1_STR}/docs"
    }


app.include_router(api_router, prefix=settings.API_V1_STR)

