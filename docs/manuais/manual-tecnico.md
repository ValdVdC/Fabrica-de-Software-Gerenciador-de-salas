# Manual Tecnico da Solucao — SIGAAS

- **Projeto:** Sistema Integrado de Gestao Academica e Alocacao de Salas com IA (SIGAAS)
- **Versao de Referencia:** `v1.0.0-rc.1` (Release Candidate — Sprint 11)
- **Data:** 21/11/2026
- **Disciplina:** Fabrica de Software & Topicos Avancados em Computacao
- **Curso / Turma:** Curso de Bacharelado em Ciencia da Computacao — Turma 8MB - CC
- **Equipe:** Grupo 31 — SIGAAS (Ewerton Thyago Tavares da Silva, Wesclei Batista Da Cruz Junior, Osvaldo Vasconcelos de Carvalho, Gabriel Porfirio dos Santos, Flavio Vecch de Brito Farias)

---

## 1. Visao Geral da Arquitetura

O SIGAAS adota uma **arquitetura em 3 camadas** com separacao estrita de responsabilidades, multi-tenancy por `campus_id`, integracao nativa de alto desempenho via FFI (`ctypes`) e inteligencia artificial preditiva sob governanca **Human-in-the-Loop**:

1. **Camada de Apresentacao (Frontend SPA — Angular 20):** interface web responsiva orientada a perfis RBAC (`admin`, `coordenador`, `secretaria`, `professor`, `aluno`). Nenhuma regra de negocio critica ou calculo combinatorio e executado no cliente.
2. **Camada de Aplicacao e Orquestracao (Backend REST — FastAPI / Python 3.12):** unico ponto de entrada HTTP. Responsavel por autenticacao JWT, controle de acesso por perfil (RBAC), isolamento multi-campus, CRUDs, geracao de relatorios, auditoria (`LogAlocacao`), orquestracao do motor de otimizacao em C/OpenMP e execucao do modulo preditivo de absenteismo (`scikit-learn`).
3. **Camada de Persistencia e Nucleos Especializados:**
   - **PostgreSQL 16:** fonte unica da verdade para a API e o modulo de IA, versionada por migrations Alembic.
   - **Motor de Alocacao (C11 + OpenMP):** biblioteca compartilhada (`motor_alocacao.so` / `motor_alocacao.dll`) carregada em processo pelo FastAPI via `ctypes`, sem dependencias externas e sem acesso direto ao banco de dados.
   - **IA Preditiva de Absenteismo (`scikit-learn` + `APScheduler` / `cron`):** estima a probabilidade de baixa frequencia discente e gera registros em `sugestao_remanejamento` com status `pendente`, jamais alterando a tabela `horario` de forma autonoma.

```mermaid
flowchart TD
    UI["Frontend SPA (Angular 20 + Nginx)"] -->|"HTTP/JSON + JWT (BearerAuth)"| API["Backend REST (FastAPI / Python 3.12)"]
    API -->|"FFI (ctypes, structs 64-bit)"| MotorC["Motor de Alocacao (C11 + OpenMP)<br/>motor_alocacao.so (sem acesso DB)"]
    API -->|"SQLAlchemy 2.0 + Alembic"| DB[("PostgreSQL 16<br/>14 tabelas + indices compostos")]
    API -->|"Inferencia / Job Agendado"| IA["IA Preditiva (scikit-learn)<br/>HistGradientBoosting + CalibratedClassifierCV"]
    IA -->|"Leitura Frequencia / Escrita Sugestao pendente"| DB
```

### Fluxo Ponta a Ponta Unificado
1. **Cadastros Estruturais:** Admin e Secretaria cadastram campi, usuarios, salas, equipamentos, cursos, disciplinas, turmas e matriculas (com atualizacao atomica de `turma.num_matriculados`).
2. **Otimizacao Combinatoria (C/OpenMP):** Admin ou Coordenador aciona `POST /api/v1/alocacao/otimizar`. O FastAPI serializa turmas e salas do campus em structs C, invoca `otimizar_alocacao_salas` via `ctypes`, persiste a grade em `horario` e registra a auditoria em `log_alocacao`.
3. **Predicao de Absenteismo e Remanejamento (IA + Human-in-the-Loop):** A execucao de `POST /api/v1/ia/analisar` (ou job agendado) calcula a probabilidade calibrada de falta, persiste `previsao_falta` e, se a ociosidade esperada atingir o limiar de `40%` (`0.40`) com desperdicio minimo de 10 lugares, cria uma `sugestao_remanejamento` com status `pendente`.
4. **Decisao Humana e Auditoria:** Admin ou Coordenador aprova ou rejeita a sugestao via `PATCH /api/v1/sugestoes/{sugestao_id}`. Apenas na aprovacao o `horario.sala_id` e atualizado e um evento `remanejamento` e gravado em `log_alocacao`.
5. **Monitoramento e Relatorios:** Dashboard (`/api/v1/dashboard/resumo`, `/ocupacao`), relatorios (`/api/v1/relatorios/ocupacao-salas`, `/remanejamentos`) e trilha de auditoria (`/api/v1/logs`) consolidam a operacao por campus.

---

## 2. Tecnologias, Linguagens e Bibliotecas Utilizadas

### 2.1 Backend (`backend/requirements.txt`) — Python 3.12

| Categoria | Biblioteca | Versao Minima | Finalidade |
| :--- | :--- | :---: | :--- |
| API / Servidor ASGI | `fastapi` | `>=0.110.0` | Framework REST e geracao OpenAPI 3.1 |
| API / Servidor ASGI | `uvicorn[standard]` | `>=0.28.0` | Servidor ASGI de producao/desenvolvimento |
| Validacao / Config | `pydantic` | `>=2.6.0` | Validacao estrita de contratos (v2) |
| Validacao / Config | `pydantic-settings` | `>=2.2.0` | Carregamento tipado de variaveis de ambiente |
| Validacao / Config | `email-validator` | `>=2.1.0` | Validacao de e-mails nos schemas Pydantic |
| Banco / ORM | `sqlalchemy` | `>=2.0.28` | ORM e consultas SQL tipadas |
| Banco / ORM | `sqlmodel` | `>=0.0.16` | Suporte complementar de modelagem SQL/Pydantic |
| Banco / ORM | `alembic` | `>=1.13.1` | Versionamento e migracoes de schema PostgreSQL |
| Banco / ORM | `psycopg2-binary` | `>=2.9.9` | Driver PostgreSQL para Python |
| Seguranca / Auth | `python-jose[cryptography]` | `>=3.3.0` | Assinatura e verificacao de tokens JWT (HS256) |
| Seguranca / Auth | `passlib[bcrypt]` | `>=1.7.4` | Hashing seguro de senhas com bcrypt |
| Seguranca / Auth | `python-multipart` | `>=0.0.9` | Parsing de formularios OAuth2/multipart |
| Agendamento | `apscheduler` | `>=3.10.4` | Agendamento de rotinas periodicas da IA |
| IA Preditiva | `numpy` | `>=1.26.0` | Computacao numerica vetorial |
| IA Preditiva | `pandas` | `>=2.2.0` | Manipulacao de datasets cronologicos de frequencia |
| IA Preditiva | `scikit-learn` | `>=1.4.0` | Pipeline ML (`HistGradientBoosting`, calibracao, metricas) |
| IA Preditiva | `joblib` | `>=1.3.2` | Serializacao do artefato de modelo treinado |
| Testes / Qualidade | `pytest` | `>=8.1.0` | Suíte de testes unitarios e de integracao |
| Testes / Qualidade | `pytest-asyncio` | `>=0.23.5` | Suporte a testes assincronos |
| Testes / Qualidade | `pytest-cov` | `>=4.1.0` | Medicao de cobertura (piso >= 85%) |
| Testes / Qualidade | `httpx` | `>=0.27.0` | Cliente HTTP para testes de endpoints FastAPI |
| Testes / Qualidade | `ruff` | `>=0.3.0` | Linter e analise estatica Python |
| Testes / Qualidade | `bandit` | `>=1.7.8` | Auditoria estatica de seguranca Python |

### 2.2 Frontend (`frontend/package.json`) — Node.js 22 / TypeScript `~5.9.2`

| Categoria | Pacote | Versao | Finalidade |
| :--- | :--- | :---: | :--- |
| Framework SPA | `@angular/core`, `common`, `compiler`, `forms`, `platform-browser`, `router` | `^20.2.0` | Componentes standalone, roteamento e formularios reativos |
| Reatividade / Runtime | `rxjs` / `zone.js` / `tslib` | `~7.8.0` / `~0.15.0` / `^2.3.0` | Fluxos assincronos HTTP e deteccao de mudancas |
| Build / CLI | `@angular/build`, `@angular/cli` | `^20.2.2` | Compilacao de desenvolvimento e producao |
| Compilacao | `@angular/compiler-cli` | `^20.2.0` | Compilador AOT do Angular |
| Testes Unitarios | `karma` (`~6.4.0`), `jasmine-core` (`~5.9.0`), `karma-jasmine` (`~5.1.0`), `karma-chrome-launcher` (`~3.2.0`), `karma-coverage` (`~2.2.0`) | Conforme `package.json` | Execucao de specs unitarios e de fluxo em ChromeHeadless |
| Formatacao | `prettier` | `^3.9.6` | Padronizacao automatica de `.ts`, `.html`, `.scss`, `.json` |

### 2.3 Motor HPC, Banco e Infraestrutura
- **Motor Combinatorio:** C11 (`-std=c11`) compilado com GCC (`-O3 -fPIC -fopenmp -shared`) e paralelismo **OpenMP**.
- **Banco de Dados:** PostgreSQL `16-alpine`.
- **Proxy / Servidor Web SPA:** Nginx `1.27-alpine` (roteamento SPA + proxy reverso `/api/`).
- **CI/CD:** GitHub Actions (`.github/workflows/ci.yml` e `release.yml`).

---

## 3. Organizacao dos Modulos e Componentes

```text
SIGAAS/
├── backend/
│   ├── alembic/                    # Configuracao Alembic e migrations (001 a 003)
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py             # Dependencias de autenticacao JWT, RBAC e escopo multi-campus
│   │   │   └── v1/
│   │   │       ├── api.py          # Registro central dos 17 roteadores da API v1
│   │   │       └── endpoints/      # auth, campi, usuarios, cursos, disciplinas, salas,
│   │   │                           # equipamentos, turmas, matriculas, horarios, motor,
│   │   │                           # alocacao, sugestoes (+ ia_router), logs, dashboard, relatorios
│   │   ├── core/security.py        # bcrypt (com DUMMY_HASH) e criacao/validacao JWT HS256
│   │   ├── db/session.py           # Engine SQLAlchemy, SessionLocal e dependencia get_db
│   │   ├── ml/                     # Relatorios de metricas ML e artefato modelo_absenteismo.joblib
│   │   ├── models/                 # 14 modelos ORM (academico, alocacao, campus, ia, sala, usuario, enums)
│   │   ├── motor/                  # Header FFI e relatorios de benchmark C/OpenMP (JSON/MD)
│   │   ├── schemas/                # Contratos Pydantic v2 de entrada e saida por dominio
│   │   ├── services/               # Logica de negocio (motor_service, ia_service, ml_evaluator,
│   │   │                           # dashboard_service, relatorio_service, export_service, log_service)
│   │   ├── config.py               # Settings via Pydantic Settings (.env)
│   │   └── main.py                 # Instancia FastAPI, CORS, OpenAPI tags, /health e redirects
│   ├── motor_alocacao/             # Codigo-fonte C/OpenMP (motor.h, motor.c, benchmark.c, Makefile)
│   ├── scripts/                    # evaluate_model.py e run_benchmarks_ci.py
│   └── tests/                      # 29 modulos Pytest (API, RBAC, multi-campus, C/OpenMP, ML, migrations)
├── frontend/
│   └── src/app/
│       ├── guards/                 # auth.guard.ts e role.guard.ts (protecao de rotas por perfil)
│       ├── interceptors/           # auth.interceptor.ts (injecao automatica do Bearer token)
│       ├── layout/shell/           # ShellComponent (navegacao lateral e cabecalho por perfil)
│       ├── pages/                  # login, admin, secretaria, professor, aluno, dashboard,
│       │                           # grade-horaria, relatorios, historico (+ specs unitarios/integracao)
│       └── services/               # Servicos HTTP tipados (auth, admin, secretaria, alocacao,
│                                   # horario, ia, dashboard, relatorio, log)
├── docker/
│   ├── backend/Dockerfile          # Python 3.12-slim + build-essential + compilacao do motor C/OpenMP
│   ├── frontend/                   # Multi-stage Node 22 + Nginx 1.27-alpine e nginx.conf
│   ├── cron/                       # Container cron (Dockerfile, crontab a cada 6h, entrypoint.sh)
│   └── compose/                    # docker-compose.local.yml, homolog.yml e prod.yml
├── scripts/                        # seed_db.py, seed_data.py, check_pr_size.py, clickup_sync.py
├── docs/                           # Arquitetura, specs SDD, manuais e relatorios de entregas
├── Makefile                        # Atalhos operacionais Docker (setup, sigaas, migrate, seed, down, reset)
└── docker-compose.yml              # Inclusao padrao de docker/compose/docker-compose.local.yml
```

---

## 4. Estrutura Completa do Banco de Dados

O schema relacional no PostgreSQL e composto por **14 tabelas** gerenciadas por 3 migrations sequenciais do Alembic (`backend/alembic/versions/`). O isolamento multi-tenant ancora-se na tabela `campus` via chave estrangeira `campus_id`.

### 4.1 Catalogo das 14 Tabelas

| # | Tabela | Chave Primaria | Isolamento / Chaves Estrangeiras Principais | Restricoes Relevantes |
| :-: | :--- | :--- | :--- | :--- |
| 1 | `campus` | `id` | Raiz de multi-tenancy | `ativo` default `true`, timestamps UTC |
| 2 | `usuario` | `id` | `campus_id -> campus.id` (`RESTRICT`) | `UNIQUE(email)`, `perfil` (`admin`, `coordenador`, `secretaria`, `professor`, `aluno`) |
| 3 | `equipamento` | `id` | Catalogo global de recursos | `UNIQUE(nome)` |
| 4 | `sala` | `id` | `campus_id -> campus.id` (`RESTRICT`) | `UNIQUE(campus_id, bloco, numero)`, `CHECK(capacidade > 0)`, `turnos_disponiveis` (JSON) |
| 5 | `sala_equipamento` | `(sala_id, equipamento_id)` | `sala_id -> sala.id` (`CASCADE`), `equipamento_id -> equipamento.id` (`RESTRICT`) | `CHECK(quantidade > 0)` |
| 6 | `curso` | `id` | `campus_id -> campus.id` (`RESTRICT`) | `UNIQUE(campus_id, codigo)` |
| 7 | `disciplina` | `id` | `curso_id -> curso.id` (`RESTRICT`) | `UNIQUE(curso_id, codigo)`, `CHECK(carga_horaria > 0)` |
| 8 | `turma` | `id` | `disciplina_id -> disciplina.id` (`RESTRICT`), `professor_id -> usuario.id` (`SET NULL`) | `CHECK(num_matriculados >= 0)` |
| 9 | `matricula` | `id` | `aluno_id -> usuario.id` (`RESTRICT`), `turma_id -> turma.id` (`CASCADE`) | `UNIQUE(aluno_id, turma_id)`, `status` default `ativa` |
| 10 | `horario` | `id` | `campus_id -> campus.id`, `sala_id -> sala.id` (`RESTRICT`), `turma_id -> turma.id` (`CASCADE`) | `CHECK(hora_inicio < hora_fim)`, `CHECK(dia_semana BETWEEN 0 AND 6)` |
| 11 | `log_alocacao` | `id` | `horario_id -> horario.id` (`SET NULL`), `usuario_responsavel -> usuario.id` (`RESTRICT`), `campus_id -> campus.id` (`SET NULL`) | `snapshot_evento` (JSON), `tipo_evento`, `timestamp` UTC |
| 12 | `frequencia` | `id` | `matricula_id -> matricula.id` (`CASCADE`), `horario_id -> horario.id` (`CASCADE`) | `data`, `presente` (boolean) — base de treino da IA |
| 13 | `previsao_falta` | `id` | `turma_id -> turma.id` (`CASCADE`), `horario_id -> horario.id` (`CASCADE`) | `prob_ausencia`, `versao_modelo`, `data_prevista` |
| 14 | `sugestao_remanejamento` | `id` | `horario_id -> horario.id` (`CASCADE`), `sala_atual_id` / `sala_sugerida_id -> sala.id` (`RESTRICT`), `aprovado_por -> usuario.id` (`SET NULL`) | `status` default `pendente` (`pendente`, `aprovado`, `rejeitado`) |

### 4.2 Historico de Migrations Alembic (`001` a `003`)

1. **`001_initial_schema`** (`07/09/2026`): criacao integral das 14 tabelas, chaves estrangeiras, `CHECK` constraints, unicidades e indices simples de busca (`ix_usuario_campus_id`, `ix_usuario_email`, `ix_sala_campus_id`, `ix_curso_campus_id`, `ix_disciplina_curso_id`, `ix_turma_disciplina_id`, `ix_turma_professor_id`, `ix_turma_periodo_letivo`, `ix_matricula_aluno_id`, `ix_matricula_turma_id`, `ix_horario_campus_id`, `ix_horario_sala_id`, `ix_horario_turma_id`, `ix_log_alocacao_horario_id`, `ix_log_alocacao_timestamp`, `ix_frequencia_data`, `ix_frequencia_horario_id`, `ix_frequencia_matricula_id`, `ix_previsao_falta_horario_id`, `ix_previsao_falta_turma_id`, `ix_sugestao_remanejamento_horario_id`).
2. **`002_add_campus_id_to_log_alocacao`** (`18/10/2026`): adicao de `campus_id` em `log_alocacao` com FK (`SET NULL`), backfill automatico a partir de `horario.campus_id`, indice `ix_log_alocacao_campus_id` e indice composto `ix_log_alocacao_campus_id_timestamp (campus_id, timestamp)`.
3. **`003_release_candidate_indexes`** (`14/11/2026`): criacao de 6 indices compostos para acelerar consultas criticas de grade horaria, deteccao de conflitos, frequencia, previsoes e triagem de sugestoes:
   - `ix_horario_turma_dia_hora` em `horario (turma_id, dia_semana, hora_inicio)`
   - `ix_horario_sala_dia_hora` em `horario (sala_id, dia_semana, hora_inicio, hora_fim)`
   - `ix_horario_campus_dia_hora` em `horario (campus_id, dia_semana, hora_inicio)`
   - `ix_frequencia_horario_data` em `frequencia (horario_id, data)`
   - `ix_previsao_falta_horario_data` em `previsao_falta (horario_id, data_prevista)`
   - `ix_sugestao_remanejamento_status_criado_em` em `sugestao_remanejamento (status, criado_em)`

---

## 5. Requisitos de Ambiente e Dependencias

### Modo Conteinerizado (Recomendado)
- **Docker Engine** >= 24.0 e **Docker Compose** v2 (`docker compose`).
- **GNU Make** (opcional; os comandos tambem podem ser executados diretamente via `docker compose`).
- Portas locais livres: `4200` (Frontend Nginx), `8000` (Backend FastAPI) e `5432` (PostgreSQL).

### Modo Hibrido (Desenvolvimento Local no Host)
- **Python 3.12** com `pip` e `venv`.
- **Node.js 22** com `npm`.
- **Compilador C com OpenMP:** GCC (`build-essential` + `libomp-dev` em Linux/WSL, ou MSYS2 MinGW-w64 GCC no Windows).
- **PostgreSQL 16** (local ou via container `make db`).
- **Git** >= 2.40.

---

## 6. Instalacao, Configuracao e Procedimentos de Execucao

### 6.1 Preparacao Inicial
```bash
git clone https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas.git
cd Fabrica-de-Software-Gerenciador-de-salas
cp .env.example .env
```
Edite `.env` caso deseje personalizar portas, senha local do banco ou `SECRET_KEY`.

### 6.2 Execucao Full-Stack com Docker Compose (via `Makefile`)
O arquivo `docker-compose.yml` na raiz inclui `docker/compose/docker-compose.local.yml`, orquestrando os 4 containers: `sigaas_postgres`, `sigaas_backend`, `sigaas_frontend` e `sigaas_cron`.

```bash
# Setup completo: sobe os servicos, executa alembic upgrade head e popula dados iniciais (idempotente)
make setup
```

Demais alvos disponiveis no `Makefile`:
- `make sigaas` — inicia toda a stack em segundo plano (`docker compose up -d`).
- `make backend` — inicia apenas `db` e `backend`.
- `make db` — inicia apenas o container PostgreSQL.
- `make ps` — lista o status e healthcheck dos containers.
- `make migrate` — aplica as migrations pendentes (`alembic upgrade head`).
- `make seed` — executa `/scripts/seed_db.py` de forma idempotente.
- `make down` — interrompe e remove os containers preservando o volume `db_data`.
- `make reset` — remove containers e volume `db_data` (`docker compose down -v`) e recria a stack (causa perda permanente dos dados locais).

Para ambientes de homologacao ou producao:
```bash
docker compose -f docker/compose/docker-compose.homolog.yml up --build -d
docker compose -f docker/compose/docker-compose.prod.yml up --build -d
```

**Enderecos apos inicializacao:**
- Aplicacao Web (Angular via Nginx): `http://localhost:4200`
- API REST / Swagger UI: `http://localhost:8000/api/v1/docs`
- Documentacao ReDoc: `http://localhost:8000/api/v1/redoc`
- Healthcheck da API e PostgreSQL: `http://localhost:8000/health`

### 6.3 Execucao em Modo Hibrido (Host)
1. **Banco de Dados:**
   ```bash
   make db
   ```
2. **Compilacao do Motor C/OpenMP e Backend FastAPI:**
   ```bash
   cd backend/motor_alocacao && make clean && make && cd ..
   python -m venv .venv
   # Linux/macOS: source .venv/bin/activate | Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   python ../scripts/seed_db.py
   uvicorn app.main:app --reload --port 8000
   ```
3. **Frontend Angular:**
   ```bash
   cd frontend
   npm ci
   npm start
   ```

---

## 7. Configuracao de Variaveis de Ambiente

As variaveis sao carregadas por `backend/app/config.py` (`pydantic-settings`) a partir do arquivo `.env` (ignorado pelo Git). O modelo versionado em `.env.example` define apenas valores de referencia local, sem credenciais reais:

| Variavel | Valor de Referencia (`.env.example`) | Obrigatoria | Descricao |
| :--- | :--- | :---: | :--- |
| `POSTGRES_HOST` | `localhost` (ou `db` no Docker) | Sim | Host do servidor PostgreSQL |
| `POSTGRES_PORT` | `5432` | Sim | Porta TCP do PostgreSQL |
| `POSTGRES_DB` | `gestao_salas` | Sim | Nome do banco de dados |
| `POSTGRES_USER` | `gestao_salas` | Sim | Usuario de conexao ao banco |
| `POSTGRES_PASSWORD` | `changeme_local_only` | Sim | Senha do banco (substituir obrigatoriamente fora do ambiente local) |
| `DATABASE_URL` | `postgresql://gestao_salas:changeme_local_only@localhost:5432/gestao_salas` | Sim | URI completa de conexao SQLAlchemy/Alembic |
| `SECRET_KEY` | `super-secret-key-change-in-production-min-32-chars` | Sim | Chave simetrica de assinatura JWT (minimo 32 caracteres aleatorios em producao) |
| `ALGORITHM` | `HS256` | Nao | Algoritmo de assinatura dos tokens JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Nao | Tempo de expiracao do token de acesso em minutos |
| `CLICKUP_API_KEY` | `pk_your_clickup_api_key_here` | Nao | Token opcional usado apenas pelo script utilitario `scripts/clickup_sync.py` |
| `CLICKUP_LIST_ID` | `your_clickup_list_id_here` | Nao | ID da lista de tarefas no ClickUp (automacao SDD) |
| `CLICKUP_WORKSPACE_ID` / `CLICKUP_SPACE_ID` | *(vazio)* | Nao | Metadados opcionais para automacao ClickUp |

> [!CAUTION]
> Nunca versione o arquivo `.env` nem insira tokens, senhas ou chaves reais em codigo-fonte, commits ou documentacao. Em homologacao e producao, gere `SECRET_KEY` criptograficamente forte (ex.: `openssl rand -hex 32`) e substitua `POSTGRES_PASSWORD`.

---

## 8. Descricao das APIs REST

A API v1 (`prefix=/api/v1`, versao `1.0.0-rc.1`) segue a especificacao OpenAPI 3.1 com documentacao interativa nativa:
- **Swagger UI:** `/api/v1/docs` (redirecionado de `/docs`)
- **ReDoc:** `/api/v1/redoc` (redirecionado de `/redoc`)
- **Schema JSON:** `/api/v1/openapi.json`
- **Healthcheck:** `GET /health` (retorna `status: ok|degraded`, `service`, `version` e `database: connected|disconnected`)

### 8.1 Autenticacao JWT e Controle de Acesso (RBAC / Multi-Campus)
- **Login:** `POST /api/v1/auth/login` valida credenciais com `bcrypt` e protecao contra *timing attacks* via `DUMMY_HASH` em tempo constante, retornando token `Bearer` assinado em `HS256` (`exp` padrao de 60 minutos).
- **Identificacao:** `GET /api/v1/auth/me` devolve o perfil autenticado (`id`, `nome`, `email`, `perfil`, `campus_id`, `ativo`).
- **RBAC:** 5 perfis (`admin`, `coordenador`, `secretaria`, `professor`, `aluno`) validados via dependencias em `backend/app/api/deps.py`.
- **Multi-Tenancy:** usuarios nao-admin tem suas consultas e mutacoes automaticamente filtradas e validadas pelo seu `campus_id`, bloqueando acesso cruzado entre campi (protecao BOLA/IDOR).

### 8.2 Mapa Consolidado de Endpoints (`/api/v1`)

| Tag OpenAPI | Prefixo | Metodos e Rotas Principais | Escopo Funcional |
| :--- | :--- | :--- | :--- |
| `Autenticacao` | `/auth` | `POST /login`, `GET /me` | Emissao de JWT e perfil autenticado |
| `Campi` | `/campi` | `GET ""`, `POST ""`, `GET /{campus_id}` | Gestao de unidades academicas |
| `Usuarios` | `/usuarios` | `GET ""`, `GET /{usuario_id}`, `POST ""`, `PATCH /{usuario_id}` | Cadastro e gestao de perfis RBAC |
| `Cursos` | `/cursos` | `GET ""`, `GET /{curso_id}`, `POST ""` | Cursos por campus |
| `Disciplinas` | `/disciplinas` | `GET ""`, `GET /{disciplina_id}`, `POST ""` | Disciplinas e carga horaria |
| `Salas` | `/salas` | `GET ""`, `POST ""`, `GET/PATCH/PUT/DELETE /{sala_id}`, `POST /{sala_id}/equipamentos` | Inventario de salas, turnos e equipamentos |
| `Equipamentos` | `/equipamentos` | `GET ""`, `POST ""` | Catalogo de recursos das salas |
| `Turmas` | `/turmas` | `GET ""`, `GET /{turma_id}`, `POST ""`, `PATCH /{turma_id}` | Oferta de turmas por periodo e docente |
| `Matriculas` | `/matriculas` | `GET ""`, `POST ""`, `DELETE /{matricula_id}` | Vinculacao de alunos com contagem atomica |
| `Horarios` | `/horarios` | `GET /meus`, `GET ""`, `GET /{horario_id}` | Grade horaria pessoal e institucional |
| `Motor` | `/motor` | `GET /status`, `POST /teste-integracao` | Diagnostico e validacao FFI (`ctypes`) |
| `Alocacao` | `/alocacao` | `POST /otimizar`, `POST /benchmark` | Alocacao C/OpenMP e benchmark cientifico |
| `Sugestoes` | `/sugestoes` | `GET ""`, `PATCH /{sugestao_id}`, `POST /analisar` | Triagem e aprovacao Human-in-the-Loop |
| `IA Preditiva` | `/ia` | `POST /analisar` | Disparo de inferencia `scikit-learn` |
| `Logs` | `/logs` | `GET ""` | Trilha de auditoria (`LogAlocacao`) filtravel |
| `Dashboard` | `/dashboard` | `GET /resumo`, `GET /ocupacao` | Indicadores agregados de ocupacao por campus |
| `Relatorios` | `/relatorios` | `GET /ocupacao-salas`, `GET /remanejamentos` | Relatorios gerenciais (JSON e exportacao CSV) |

---

## 9. Motor de Otimizacao C/OpenMP e Componente de IA Preditiva

### 9.1 Motor de Otimizacao Combinatoria (`backend/motor_alocacao/`)
- **Classificacao Algoritmica:** Heuristica Construtiva Gulosa Deterministica com Priorizacao de Restricoes Rigidas e Capacidade Minima Viavel (*Best-Fit Decreasing* com *multi-start* perturbado deterministico em OpenMP).
- **Classe de Complexidade:** Problema de Timetabling Universitario **NP-dificil**.
- **Complexidade Temporal por Tentativa:** `O(T * S)` (onde `T` = numero de turmas e `S` = numero de salas), sem garantia de otimo global, priorizando viabilidade em tempo polinomial e zero conflitos de sala/horario.
- **Compilacao:** `gcc -Wall -Wextra -pedantic -std=c11 -O3 -fPIC -fopenmp -shared -o motor_alocacao.so motor.c`.
- **Contrato FFI (`ctypes` em `backend/app/services/motor_service.py`):**
  - Structs alinhadas em 64-bit: `SalaC`, `TurmaC`, `AlocacaoItemC` e `MetricasAlocacaoC` (com campo `int padding` explicito para evitar desalinhamento de memoria).
  - Funcoes exportadas: `otimizar_alocacao_salas`, `executar_benchmark_cenario`, `obter_versao_motor` e `testar_integracao_ctypes`.
  - Restricao arquitetural inviolavel: zero bibliotecas externas e zero conexoes de banco no codigo C.

#### Resultados Estatisticos de Benchmark (`backend/app/motor/relatorio_benchmark_c.md`)
Coletados com **N=10 repeticoes** e **4 threads OpenMP** em CPU AMD64 (6 nucleos fisicos / 12 logicos, 3901 MHz, 13.89 GB RAM, GCC 15.2.0):

| Carga (Turmas x Salas) | Media Seq (ms) | Desvio Seq (ms) | Media Par (ms) | Desvio Par (ms) | Speedup Real | Eficiencia (%) | Estabilidade (`CV < 15%`) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `10 x 5` | 0.97 | 0.05 | 0.75 | 0.08 | `1.29x` | 32.2% | Aprovado |
| `50 x 20` | 2.91 | 0.20 | 0.99 | 0.03 | `2.94x` | 73.5% | Aprovado |
| `100 x 40` | 15.40 | 0.98 | 4.12 | 0.19 | `3.74x` | 93.5% | Aprovado |
| `500 x 150` | 259.00 | 4.88 | 84.59 | 7.89 | `3.06x` | 76.5% | Aprovado |

Anomalias criticas mapeadas e blindadas por testes de regressao: `BUG-HPC-01` (alinhamento 64-bit), `BUG-HPC-02` (penalidade contra canibalizacao de laboratorios), `BUG-HPC-03` (falso positivo de exigencia de laboratorio por substring) e `BUG-HPC-04` (retorno explicito de turmas pendentes sem sala disponivel).

### 9.2 Componente de IA Preditiva (`backend/app/services/ia_service.py`)
- **Arquitetura do Pipeline (`scikit-learn`):**
  - Pre-processamento via `ColumnTransformer`: `StandardScaler` para atributos numericos (`dia_semana`, `hora_inicio_minutos`, `num_matriculados`, `capacidade_sala`, `razao_ocupacao`) e `OneHotEncoder(handle_unknown="ignore")` para atributo categorico (`turno`).
  - Estimador base: `HistGradientBoostingClassifier(random_state=42, max_iter=100, min_samples_leaf=5, learning_rate=0.08)`.
  - Calibracao probabilistica: `CalibratedClassifierCV(estimator=base_clf, method="sigmoid", cv=2)` para emitir probabilidades calibradas no intervalo `[0.0, 1.0]`.
  - Artefato persistido: `backend/app/ml/modelo_absenteismo.joblib` (`VERSAO_MODELO = "v1.0-histgb"`).
- **Prevencao de Vazamento Temporal:** extracao ordenada cronologicamente (`ORDER BY Frequencia.data ASC`) e avaliacao com `TimeSeriesSplit`. Em bancos recem-inicializados sem historico de frequencia, priors sinteticos inicializam o estimador de forma segura.
- **Regra de Decisao e Limiar de 40%:**
  - Calcula `presentes_esperados = max(1, ceil(num_matriculados * (1 - prob_ausencia)))` e `taxa_ociosidade = (capacidade_sala - presentes_esperados) / capacidade_sala`.
  - Aciona sugestao quando `taxa_ociosidade >= 0.40` (40%) e `desperdicio >= 10` lugares, selecionando a menor sala livre compativel (mesmo campus e mesmo tipo). O limiar de 40% foi escolhido na analise de sensibilidade (`backend/app/ml/relatorio_metricas_ml.md`) por minimizar falsos negativos de alto custo operacional.
- **Governanca Human-in-the-Loop (Inviolavel):** o servico de IA **nunca** modifica `horario.sala_id`. Ele registra `previsao_falta` e cria `sugestao_remanejamento` com status `pendente` (com idempotencia por horario). A efetivacao da troca exige aprovacao explicita de Admin ou Coordenador via `PATCH /api/v1/sugestoes/{id}`.

---

## 10. Orientacoes Basicas para Manutencao, Testes e Evolucao

### 10.1 Execucao Local das Suites de Testes e Qualidade

| Camada | Comando | Criterio de Aprovacao |
| :--- | :--- | :--- |
| Backend (Pytest + Cobertura) | `cd backend && pytest tests -v --cov=app --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=85` | 100% testes passando e cobertura `>= 85%` |
| Qualidade / Seguranca Python | `ruff check backend/ scripts/` e `bandit -r backend/app -ll -ii` | Sem vulnerabilidades criticas ou erros de lint |
| Motor C/OpenMP | `cd backend/motor_alocacao && make clean && make` | Compilacao limpa sem warnings impeditivos e geracao de `motor_alocacao.so` |
| Frontend (Karma + Build) | `cd frontend && npx ng test --no-watch --browsers=ChromeHeadless && npm run build -- --configuration production` | 100% specs passando e build de producao sem erros |
| Formatacao Frontend | `cd frontend && npm run format:check` | 100% aderente ao Prettier |
| Avaliacao ML / Benchmarks | `python backend/scripts/evaluate_model.py` e `python backend/scripts/run_benchmarks_ci.py` | Atualizacao reprodutivel dos relatorios JSON/MD |

### 10.2 Pipeline de Integracao Continua (`.github/workflows/ci.yml`)
Todo Pull Request com alteracoes de codigo executa 3 estagios automatizados no GitHub Actions:
1. `stage-governance`: tamanho de PR (`scripts/check_pr_size.py`), `py_compile`, `ruff`, `bandit` e `prettier --check`.
2. `test-backend`, `test-motor-c` e `test-frontend`: executados em paralelo (Pytest >= 85%, GCC/OpenMP, Karma ChromeHeadless + `ng build --configuration production`).
3. `docker-smoke-test`: `docker compose config`, build das imagens, inicializacao completa da stack e verificacao HTTP em `/health`, `/docs`, `/api/v1/motor/status`, frontend `:4200` e proxy reverso Nginx.

### 10.3 Boas Praticas para Evolucao Segura
- **Alteracoes de Schema:** toda modificacao em `backend/app/models/` deve gerar uma nova migration Alembic (`alembic revision -m "..."`) com funcoes `upgrade()` e `downgrade()` testadas em `backend/tests/test_migrations.py`.
- **Evolucao do Motor C:** qualquer mudanca nas structs de `backend/motor_alocacao/motor.h` exige atualizacao espelhada imediata em `backend/app/services/motor_service.py` (alinhamento 64-bit) e revalidacao de `test_motor_c.py`.
- **Fluxo de Branches e PRs:** adotar Trunk-Based Development (sem push direto em `main`), Conventional Commits (`feat`, `fix`, `docs`, `test`, `perf`, `refactor`, `chore`, `ci`), PRs atomicos (`<= 400` linhas de codigo), revisao adversarial pre-PR e merge exclusivo via Squash and Merge.
