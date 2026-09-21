# Sistema de Gestão de Salas e Escalas com IA (SIGAAS)

Sistema multi-campus de gestão acadêmica com alocação inteligente de salas e horários.
Motor de otimização em C/OpenMP + modelo de previsão de falta em Python/scikit-learn,
orquestrados por um backend FastAPI e consumidos por um frontend Angular.

Projeto desenvolvido com engenharia de software orientada por IA (**SDD + TDD**), utilizando o **Antigravity** como orquestrador e integração com o **ClickUp**.

---

## Documentacao Essencial
- **Documento Normativo Completo** (arquitetura, modelo de dados, backlog inicial): [`docs/projeto-gestao-salas-escalas.md`](docs/projeto-gestao-salas-escalas.md)
- **Regras para Agentes de IA**: [`AGENTS.md`](AGENTS.md)
- **Guia de Handoff e Prompts**: [`docs/handoff-guide.md`](docs/handoff-guide.md)
- **Catalogo do Squad de Agentes**: [`.agent/rules/squad-roles.md`](.agent/rules/squad-roles.md)
- **Ciclo de Desenvolvimento SDD + TDD**: [`.agent/workflows/sdd-cycle.md`](.agent/workflows/sdd-cycle.md)
- **Especificacoes Tecnicas por Feature**: [`docs/specs/`](docs/specs/)

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

## Como Rodar Localmente (Via Makefile)

O projeto possui um `Makefile` na raiz para simplificar o gerenciamento do ambiente Docker de forma rápida.

### 1. Configurar Ambiente
```bash
cp .env.example .env   # Preencha as variáveis de ambiente (banco e ClickUp)
```

### 2. Comandos de Inicialização (Atalhos)

*   **Setup completo** (Sobe os containers, aplica migrações e popula os dados de teste):
    ```bash
    make setup
    ```
*   **Subir toda a stack** (Banco, API, Frontend e Cron) em segundo plano:
    ```bash
    make sigaas
    ```
*   **Verificar status dos containers**:
    ```bash
    make ps
    ```
*   **Subir apenas o Banco de Dados e a API Backend**:
    ```bash
    make backend
    ```
*   **Subir apenas o Banco de Dados**:
    ```bash
    make db
    ```
*   **Parar todos os serviços**:
    ```bash
    make down
    ```
*   **Resetar o ambiente** (Para todos os containers, limpa os volumes/dados do banco e inicia a stack do zero novamente):
    ```bash
    make reset
    ```
    > [!WARNING]
    > O comando `make reset` executa `docker compose down -v`, removendo o volume do PostgreSQL (`db_data`). Isso acarreta a perda permanente e irreversível de todos os dados locais. Recomenda-se realizar backup antes da execução caso existam dados que necessitem de preservação.

---

## Desenvolvimento Local (Híbrido)

Se você estiver desenvolvendo ativamente e preferir rodar as aplicações no seu próprio host para contar com o *hot-reloading* instantâneo de cada framework:

### 1. Inicie o banco de dados via Docker
```bash
make db
```

### 2. Backend (FastAPI)
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

### 3. Frontend (Angular)
```bash
cd frontend
npm install
ng serve
```

### 4. Sincronização e Automação do ClickUp
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