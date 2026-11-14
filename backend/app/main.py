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

API_DESCRIPTION = (
    "API REST oficial do Sistema Integrado de Gestao Academica e Alocacao de Salas com IA (SIGAAS). "
    "Construida sobre arquitetura em 3 camadas: SPA Angular para apresentacao por perfis, "
    "FastAPI para orquestracao, autenticacao JWT e RBAC multi-campus (Admin, Coordenador, Secretaria, Professor e Aluno), "
    "motor combinatorio de alocacao de salas em C com paralelismo OpenMP via ctypes, "
    "e modulo preditivo de absenteismo em Python/scikit-learn com aprovacao Human-in-the-Loop."
)

OPENAPI_TAGS = [
    {"name": "Autenticacao", "description": "Login em tempo constante, emissao de JWT e identificacao do usuario autenticado."},
    {"name": "Campi", "description": "Gestao multi-campus de unidades academicas."},
    {"name": "Usuarios", "description": "Cadastro, listagem e controle de perfis RBAC de usuarios."},
    {"name": "Cursos", "description": "Gerenciamento de cursos de graduacao e pos-graduacao por campus."},
    {"name": "Disciplinas", "description": "Cadastro de disciplinas, carga horaria e requisitos de laboratorio."},
    {"name": "Salas", "description": "Inventario de salas, capacidade, turnos disponiveis e status operacional."},
    {"name": "Equipamentos", "description": "Controle de recursos e equipamentos vinculados as salas."},
    {"name": "Turmas", "description": "Gestao de turmas por periodo letivo, vagas e docente responsavel."},
    {"name": "Matriculas", "description": "Vinculacao de alunos as turmas ofertadas."},
    {"name": "Horarios", "description": "Consulta e manutencao da grade de horarios alocados."},
    {"name": "Motor", "description": "Diagnostico e teste de integracao FFI (ctypes) com o motor C/OpenMP."},
    {"name": "Alocacao", "description": "Otimizacao combinatoria de salas com OpenMP, metricas de speedup e benchmark cientifico."},
    {"name": "Sugestoes", "description": "Listagem e aprovacao Human-in-the-Loop de sugestoes de remanejamento de salas."},
    {"name": "IA Preditiva", "description": "Execucao da inferencia scikit-learn para previsao de absenteismo e ociosidade."},
    {"name": "Logs", "description": "Trilha imutavel de auditoria de alocacoes e remanejamentos."},
    {"name": "Dashboard", "description": "Indicadores consolidados de ocupacao, capacidade e operacao por campus."},
    {"name": "Relatorios", "description": "Exportacao de relatorios gerenciais e grade horaria em CSV/PDF."},
    {"name": "Health", "description": "Verificacao de disponibilidade da API e conectividade com o PostgreSQL."},
    {"name": "Root", "description": "Informacoes iniciais e atalhos da API v1."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=API_DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_tags=OPENAPI_TAGS,
    contact={
        "name": "Grupo 31 - SIGAAS",
    },
    license_info={
        "name": "Uso Academico - Fabrica de Software & Topicos Avancados",
    },
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


@app.get("/redoc", include_in_schema=False)
def redoc_redirect():
    return RedirectResponse(url=f"{settings.API_V1_STR}/redoc")


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
        "docs": f"{settings.API_V1_STR}/docs",
        "redoc": f"{settings.API_V1_STR}/redoc",
    }


app.include_router(api_router, prefix=settings.API_V1_STR)
