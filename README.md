# Sistema de Gestão de Salas e Escalas com IA (SIGAAS)

Sistema multi-campus de gestão acadêmica com alocação inteligente de salas e horários.
Motor de otimização em C/OpenMP + modelo de previsão de falta em Python/scikit-learn,
orquestrados por um backend FastAPI e consumidos por um frontend Angular.

Projeto desenvolvido com engenharia de software orientada por IA (**SDD + TDD**), utilizando o **Antigravity** como orquestrador e integração com o **ClickUp**.

---

## Documentação Essencial
- 📄 **Documento Normativo Completo** (arquitetura, modelo de dados, backlog inicial): [`docs/projeto-gestao-salas-escalas.md`](docs/projeto-gestao-salas-escalas.md)
- 🤖 **Regras para Agentes de IA**: [`AGENTS.md`](AGENTS.md)
- 👥 **Catálogo do Squad de Agentes**: [`.agent/rules/squad-roles.md`](.agent/rules/squad-roles.md)
- 🔄 **Ciclo de Desenvolvimento SDD + TDD**: [`.agent/workflows/sdd-cycle.md`](.agent/workflows/sdd-cycle.md)
- 📋 **Especificações Técnicas por Feature**: [`docs/specs/`](docs/specs/)

---

## Stack Tecnológica
| Camada | Tecnologia | Responsabilidade |
|---|---|---|
| **Frontend** | Angular | SPA para visualização e operações por perfil (Admin, Professor, Aluno, Secretaria) |
| **Backend / API** | FastAPI (Python) | Autenticação (JWT), isolamento multi-tenant, CRUDs, orquestração |
| **Motor de Alocação** | C + OpenMP (`.so` via `ctypes`) | Otimização paralela da grade de salas sem conflitos |
| **IA Preditiva** | Python / scikit-learn | Modelo de probabilidade de baixa frequência e sugestão de remanejamento |
| **Banco de Dados** | PostgreSQL | Persistência com migrações Alembic |
| **Gestão de Tarefas** | ClickUp | Backlog, épicos, histórias e auditoria de status |

---

## Como Rodar Localmente

### 1. Configurar Ambiente
```bash
cp .env.example .env   # Preencha as variáveis de ambiente (banco e ClickUp)
```

### 2. Subir Banco de Dados via Docker
```bash
docker compose up -d db
```

### 3. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Frontend (Angular)
```bash
cd frontend
npm install
ng serve
```

### 5. Sincronização e Automação do ClickUp
```bash
pip install -r scripts/requirements.txt
python scripts/clickup_sync.py test-connection
python scripts/clickup_sync.py import-csv docs/clickup_backlog_import.csv
```

---

## Estrutura do Repositório
```
/backend            FastAPI (routers, models, services, migrations)
  /motor_alocacao   Código C + OpenMP + bindings ctypes + Makefile
  /tests            Testes unitários e de integração (Pytest)
/frontend           Aplicação Angular (SPA)
/ia_previsao        Scripts de dataset, treino e serving do modelo scikit-learn
/docs               Documentação técnica, requisitos normativos e specs
  /specs            Especificações SDD de cada sprint / feature
/scripts            Automações (ClickUp sync, benchmarks, scripts auxiliares)
/.agent             Regras de governança de IA, workflows e definições do Squad
```

---

## Equipe
- Scrum Master
- Product Owner (PO)
- Dev Backend
- Dev Frontend
- Responsável BD / Documentação