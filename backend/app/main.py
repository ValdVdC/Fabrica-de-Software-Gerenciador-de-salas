"""
Ponto de entrada do FastAPI para o SIGAAS.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
)

# Configuração de CORS para consumo pelo Angular SPA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get(f"{settings.API_V1_STR}", tags=["Root"])
def root_api():
    return {
        "message": "Bem-vindo à API do SIGAAS - Sistema de Gestão de Salas e Escalas com IA",
        "docs": f"{settings.API_V1_STR}/docs"
    }
