# Sistema Integrado de Gestao Academica e Alocacao de Salas com IA (SIGAAS)

**Versao atual:** `v1.0.0-rc.1` (Release Candidate)

Sistema multi-campus de gestao academica com alocacao inteligente de salas e horarios. Combina um motor de otimizacao combinatoria em **C + OpenMP** (carregado via `ctypes`), um modulo preditivo de absenteismo em **Python / scikit-learn** sob governanca **Human-in-the-Loop**, uma API REST em **FastAPI** com isolamento multi-tenant no **PostgreSQL**, e uma interface SPA em **Angular**.

Projeto desenvolvido com metodologia **SDD + TDD** (Spec-Driven Development + Test-Driven Development), governanca de branches Trunk-Based Development, revisao adversarial multi-agente pre-PR e rastreamento no ClickUp.

---

## Documentacao Essencial

- **Documento Normativo Completo** (arquitetura, modelo de dados, backlog inicial): [`docs/projeto-gestao-salas-escalas.md`](docs/projeto-gestao-salas-escalas.md)
- **Regras para Agentes de IA**: [`AGENTS.md`](AGENTS.md)
- **Guia de Handoff e Prompts**: [`docs/handoff-guide.md`](docs/handoff-guide.md)
- **Catalogo do Squad de Agentes**: [`.agent/rules/squad-roles.md`](.agent/rules/squad-roles.md)
- **Ciclo de Desenvolvimento SDD + TDD**: [`.agent/workflows/sdd-cycle.md`](.agent/workflows/sdd-cycle.md)
- **Especificacoes Tecnicas por Feature**: [`docs/specs/`](docs/specs/)
- **Entregas e Relatorios Tecnicos**: [`docs/entregas/`](docs/entregas/)

---

## Arquitetura e Stack Tecnologica

A solucao adota uma arquitetura em camadas com separacao estrita de responsabilidades:

```text
+-----------------------------------------------------------------------------+
|                        Frontend SPA (Angular 20)                            |
|   Perfis RBAC: Admin | Coordenador | Secretaria | Professor | Aluno         |
+--------------------------------------+--------------------------------------+
                                       | HTTP / JSON + JWT (BearerAuth)
                                       v
+-----------------------------------------------------------------------------+
|                       Backend / API REST (FastAPI)                          |
|  Autenticacao JWT | Multi-Tenancy (campus_id) | CRUDs | Orquestracao        |
+-------------------+----------------------------------+----------------------+
                    | FFI (ctypes)                     | SQLAlchemy 2.0 / Alembic
                    v                                  v
+--------------------------------------+  +-----------------------------------+
|     Motor de Alocacao (C + OpenMP)   |  |       Banco de Dados              |
|  Heuristica construtiva O(T * S)     |  |       PostgreSQL (14 tabelas)     |
|  motor_alocacao.so (sem acesso DB)   |  +-----------------------------------+
+--------------------------------------+               ^
                                                       |
+------------------------------------------------------+----------------------+
|                 IA Preditiva de Absenteismo (scikit-learn)                  |
|  Job agendado (APScheduler) | Limiar 40% | Gera SugestaoRemanejamento       |
|  Regra inviolavel: nunca altera Horario diretamente (apenas pendente)       |
+-----------------------------------------------------------------------------+
```

| Camada | Tecnologia | Responsabilidade |
|---|---|---|
| **Frontend** | Angular 20 | SPA responsiva com navegacao baseada em perfis RBAC, sem regras de negocio pesadas |
| **Backend / API** | FastAPI (Python 3.12) | Ponto unico de entrada HTTP, autenticacao JWT, isolamento por `campus_id` e orquestracao |
| **Motor de Alocacao** | C11 + OpenMP (`.so`/`.dll` via `ctypes`) | Alocacao combinatoria paralela sem conflitos de horario/sala/professor |
| **IA Preditiva** | Python / scikit-learn + APScheduler | Predicao de baixa frequencia e criacao de `SugestaoRemanejamento` com status `pendente` |
| **Banco de Dados** | PostgreSQL + Alembic | Fonte unica da verdade com 14 tabelas, migrations versionadas e indices compostos |
| **Gestao e CI** | GitHub Actions + ClickUp | Pipeline automatizado (ruff, Pytest, Karma, gcc/OpenMP, Docker smoke test) |

---

## Documentacao Interativa da API (OpenAPI 3.1)

Com o backend em execucao (`http://localhost:8000`), a especificacao completa da API (`1.0.0-rc.1`, organizada em 17 tags de dominio + `Health` e `Root`, com esquema `BearerAuth` JWT) fica disponivel nos seguintes endpoints:

- **Swagger UI:** `http://localhost:8000/api/v1/docs` (atalho `/docs`)
- **ReDoc:** `http://localhost:8000/api/v1/redoc` (atalho `/redoc`)
- **Schema OpenAPI JSON:** `http://localhost:8000/api/v1/openapi.json`
- **Healthcheck:** `http://localhost:8000/health`

---

## Como Rodar com Docker Compose (Via Makefile)

O repositorio disponibiliza um `Makefile` na raiz para inicializar e gerenciar os containers (`db`, `backend`, `frontend`).

### 1. Configurar Variaveis de Ambiente
```bash
cp .env.example .env
```

### 2. Comandos Principais

- **Setup completo** (sobe os containers, aplica `alembic upgrade head` e executa `scripts/seed_db.py` de forma idempotente):
  ```bash
  make setup
  ```
- **Subir toda a stack em segundo plano:**
  ```bash
  make sigaas
  ```
- **Verificar status dos containers:**
  ```bash
  make ps
  ```
- **Subir apenas Banco de Dados e Backend:**
  ```bash
  make backend
  ```
- **Subir apenas o Banco de Dados:**
  ```bash
  make db
  ```
- **Aplicar migrations manualmente:**
  ```bash
  make migrate
  ```
- **Executar seed manualmente:**
  ```bash
  make seed
  ```
- **Parar todos os servicos:**
  ```bash
  make down
  ```
- **Resetar o ambiente** (remove containers e volumes do PostgreSQL e sobe a stack novamente):
  ```bash
  make reset
  ```
  > [!WARNING]
  > O comando `make reset` executa `docker compose down -v`, removendo o volume do PostgreSQL (`db_data`). Isso acarreta a perda permanente e irreversivel dos dados locais.

Apos `make setup`:
- **Aplicacao Web (Angular):** `http://localhost:4200`
- **API / Swagger UI:** `http://localhost:8000/api/v1/docs`

---

## Desenvolvimento Local (Hibrido)

Para executar backend e frontend diretamente no host com *hot-reloading*:

### 1. Iniciar PostgreSQL via Docker
```bash
make db
```

### 2. Backend (FastAPI + Motor C/OpenMP)
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python ../scripts/seed_db.py
uvicorn app.main:app --reload
```

Para compilar o motor de alocacao em C/OpenMP manualmente (quando necessario no host):
```bash
cd backend/motor_alocacao
make
```

### 3. Frontend (Angular)
```bash
cd frontend
npm install
npm start
```

### 4. Execucao de Testes
```bash
# Backend (Pytest + cobertura minima >= 85%)
pytest backend/tests/ --cov=backend/app --cov-fail-under=85

# Frontend (Karma / ChromeHeadless + build de producao)
cd frontend && npm test -- --watch=false --browsers=ChromeHeadless && npm run build
```

---

## Credenciais Oficiais de Homologacao

As credenciais abaixo sao populadas de forma idempotente por [`scripts/seed_db.py`](scripts/seed_db.py) para demonstracao e homologacao de todos os perfis RBAC (senha padrao: `sigaas123`):

| Perfil | Usuario | E-mail | Senha |
| :--- | :--- | :--- | :--- |
| **Admin** | Admin Central | `admin@sigaas.edu` | `sigaas123` |
| **Coordenador** | Coord. Computacao | `coord.cc@sigaas.edu` | `sigaas123` |
| **Secretaria** | Secretaria Academica | `secretaria@sigaas.edu` | `sigaas123` |
| **Professor** | Professor Padrao | `professor@sigaas.edu` | `sigaas123` |
| **Professor** | Prof. Alan Turing | `alan.turing@sigaas.edu` | `sigaas123` |
| **Professor** | Prof. Ada Lovelace | `ada.lovelace@sigaas.edu` | `sigaas123` |
| **Aluno** | Aluno Padrao | `aluno@sigaas.edu` | `sigaas123` |
| **Aluno** | Aluno Joao Silva | `joao.silva@sigaas.edu` | `sigaas123` |
| **Aluno** | Aluna Maria Souza | `maria.souza@sigaas.edu` | `sigaas123` |

---

## Resultados de Engenharia, Benchmarks e Qualidade

### Motor de Alocacao C + OpenMP (`N=10` repeticoes, 4 threads)
O problema de alocacao de turmas e salas (*Timetabling*) pertence a classe **NP-dificil** e e resolvido por uma **Heuristica Construtiva Gulosa Deterministica** (`O(T * S)` por tentativa, sem garantia de otimo global). Resultados oficiais em `backend/app/motor/relatorio_benchmark_c.md` (CPU AMD64 6C/12T 3,9 GHz, `gcc 15.2.0 -O3 -fopenmp`):

| Carga (Turmas x Salas) | Media Seq. (ms) | Media Par. (ms) | Speedup Real | Eficiencia | CV Max. (< 15%) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| `10 x 5` | `0,97` | `0,75` | `1,29x` | `32,2%` | `10,54%` |
| `50 x 20` | `2,91` | `0,99` | `2,94x` | `73,5%` | `6,96%` |
| `100 x 40` | `15,40` | `4,12` | **`3,74x`** | **`93,5%`** | `6,33%` |
| `500 x 150` | `259,00` | `84,59` | `3,06x` | `76,5%` | `9,33%` |

### IA Preditiva de Absenteismo (Limiar Operacional de 40%)
O classificador probabilistico calibrado utiliza o limiar operacional de **40% (`0.40`)** fundamentado pela funcao de custo assimetrica `C = 1,0 * FP + 2,0 * FN` (priorizando o recall para evitar salas grandes ociosas), com aprovacao humana obrigatoria via `PATCH /api/v1/sugestoes/{id}`. Na suite de validacao balanceada (`N=10`, `backend/tests/test_ml_evaluation.py`), o modelo registra **Acuracia `0.8000`**, **Precisao `0.8000`**, **Recall `0.8000`**, **F1-Score `0.8000`**, **AUC-ROC `0.9200`** e **Indice de Brier `0.1283`**.

### Suites Automatizadas e CI na `main` (`v1.0.0-rc.1`, commit `0a03b07`)
- **Backend (Pytest + Alembic):** **276 testes aprovados**, **93,65% de cobertura** (meta >= 85%), 14 tabelas PostgreSQL com paridade 100% ORM vs. migration `003_release_candidate_indexes.py`.
- **Frontend (Angular 20 / Karma):** **165/165 testes aprovados** em `ChromeHeadless` e build de producao limpo (`479.25 kB`, sem avisos de budget).
- **CI (GitHub Actions Run `#43639008716`):** 5/5 checks aprovados (`Code Quality & Policy Enforcement`, `Backend Tests & Coverage`, `Frontend Tests & Build`, `Allocation Engine C & OpenMP`, `Docker Environment Smoke Test`).

---

## Estrutura do Repositorio

```text
/backend            FastAPI (routers, models, services, alembic migrations)
  /motor_alocacao   Codigo C + OpenMP + bindings ctypes + Makefile
  /tests            Testes unitarios, integracao, schema e ML (Pytest)
/frontend           Aplicacao Angular 20 (SPA) e testes Karma/Jasmine
/ia_previsao        Scripts de dataset, treino e serving do modelo scikit-learn
/docs               Documentacao tecnica, requisitos normativos, specs e entregas
  /specs            Especificacoes SDD de cada sprint / feature
  /entregas         Relatorios tecnicos por sprint, consolidado e PDFs oficiais
/scripts            Automacoes (seed_db.py, clickup_sync.py, check_pr_size.py)
/.agent             Regras de governanca de IA, workflows e definicoes do Squad
```

---

## Identificacao Oficial — Grupo 31

- **Disciplina:** Fabrica de Software & Topicos Avancados em Computacao
- **Curso:** Curso de Bacharelado em Ciencia da Computacao — Turma 8MB - CC
- **Equipe:** Grupo 31 — SIGAAS

| Integrante | Matricula | Papel no Squad | Responsabilidade Tecnica Principal |
| :--- | :---: | :--- | :--- |
| **Ewerton Thyago Tavares da Silva** | `01573977` | Scrum Master (Lider) | Facilitacao agil, gestao de entregas, governanca de branches e submissao no Teams |
| **Wesclei Batista Da Cruz Junior** | `01606772` | Product Owner | Levantamento de requisitos, regras de negocio e validacao dos criterios de aceite |
| **Osvaldo Vasconcelos de Carvalho** | `01614171` | Dev Backend / Sistemas | Arquitetura de API, integracao FFI C/OpenMP (`ctypes`), endpoints e migrations |
| **Gabriel Porfirio dos Santos** | `01591399` | Dev Frontend | Interface SPA Angular 20, componentes, estados reativos e interceptors |
| **Flavio Vecch de Brito Farias** | `01600988` | DBA & Documentacao | Modelagem relacional PostgreSQL, scripts de seed, integridade e documentacao tecnica |
