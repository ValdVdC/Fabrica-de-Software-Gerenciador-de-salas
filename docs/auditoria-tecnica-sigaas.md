# Auditoria Técnica Completa Baseada em Evidências — SIGAAS

**Sistema Integrado de Gestão Acadêmica e Alocação de Salas com IA (SIGAAS)**  
**Data da Auditoria:** 2026-11-27  
**Marco / Escopo:** Marco M1 — Diagnóstico Técnico Integral (Somente Leitura)  
**Repositório Auditado:** `https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas` (workspace local `c:\Work\workspace\SIGAAS`)

---

## Identificação Oficial — Grupo 31

Conforme `AGENTS.md` §4.8 e `.agent/rules/academic-deliverables.md`:

- **Disciplina:** Fábrica de Software & Tópicos Avançados em Computação
- **Curso:** Curso de Bacharelado em Ciência da Computação
- **Turma:** 8MB - CC (Semestre 2026/2)
- **Equipe:** Grupo 31 — SIGAAS
- **Repositório GitHub:** `https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas`

| Integrante | Matrícula | Papel | Responsabilidades |
|---|---|---|---|
| Ewerton Thyago Tavares da Silva | 01573977 | Scrum Master (Líder) | Facilitação ágil, gestão de entregas, governança de branches e submissão no Teams |
| Wesclei Batista Da Cruz Júnior | 01606772 | Product Owner | Levantamento de requisitos, regras de negócio e validação dos critérios de aceite |
| Osvaldo Vasconcelos de Carvalho | 01614171 | Dev Backend / Sistemas | Arquitetura de API, integração FFI C/OpenMP (ctypes), endpoints e migrations |
| Gabriel Porfírio dos Santos | 01591399 | Dev Frontend | Interface SPA Angular 20, componentes, estados reativos e interceptors |
| Flávio Vecch de Brito Farias | 01600988 | DBA & Documentação | Modelagem relacional PostgreSQL, scripts de seed, integridade e documentação técnica |

---

## Resumo Executivo, Metodologia e Ressalvas

### Resumo Executivo

A auditoria técnica somente leitura sobre a base atual do SIGAAS confirma que o projeto dispõe de uma fundação funcional e testável — API FastAPI com 16 módulos de rotas, motor de alocação em C11 compilado como biblioteca compartilhada via `ctypes`, pipeline preditivo em `scikit-learn` com aprovação *Human-in-the-Loop*, modelo relacional de 14 tabelas com 3 migrações Alembic e SPA Angular `20.2.0` — respaldada por **276 testes de backend aprovados** e **165 testes unitários de frontend aprovados**. Contudo, a inspeção direta do código-fonte revelou **lacunas críticas de paralelismo, segurança, arquitetura, UX/UI, regras de negócio e DevOps** que impedem a conformidade plena com os requisitos acadêmicos e operacionais:

1. **Paralelismo no Motor de Alocação:** O motor C (`backend/motor_alocacao/motor.c`) executa **exclusivamente paralelismo em CPU via OpenMP** (`-fopenmp`, `#include <omp.h>`, `#pragma omp parallel/for/critical/single`), com **0% de implementação em OpenCL ou CUDA** em todo o repositório. Além disso, `otimizar_alocacao_salas()` executa o algoritmo sequencial e o paralelo em todas as chamadas de produção, `TurmaC` omite `professor_id` (impossibilitando verificação de choque de horário docente), `alocacao.py` usa atribuição ingênua `idx % 5` em blocos fixos, e `delete(Horario)` aciona deleção em cascata (`ondelete="CASCADE"`) sobre `Frequencia`, `PrevisaoFalta` e `SugestaoRemanejamento`.
2. **Segurança, Hashing, MFA e Isolamento:** A autenticação utiliza `bcrypt` direto e JWT `HS256` (`exp = 60` min), porém **não há qualquer suporte a MFA/TOTP (0% implementado)**; os roteadores `campi.py` (incluindo `POST /api/v1/campi`), `equipamentos.py` (`GET`) e `motor.py` (`GET /status` e `POST /teste-integracao`) **não exigem autenticação**; `UsuarioCreate.senha` não impõe `max_length=72` apesar de `verify_password` rejeitar senhas acima de 72 bytes UTF-8; não existe fluxo de troca/redefinição de senha; `authGuard` no Angular não valida expiração `exp` do JWT; `AuthService.setRole()` permanece como *stub* de teste em código de produção; e existem divergências severas de RBAC entre Frontend e Backend (como botões que retornam HTTP `403` para `coordenador`, bloqueio de `admin`/`coordenador` em `/secretaria` e bloqueio de `secretaria` em `/historico`).
3. **AISlop, UX/UI e Cobertura Funcional (Aula 01, pág. 12):** O frontend mantém vestígios de *scaffold* (`frontend-init`), zero biblioteca de CSS, zero biblioteca de ícones (16 `<svg>` embutidos e 2 laços de gráfico), zero modais (a edição de salas em `AdminComponent` destrói o formulário de criação), zero diálogos de confirmação em 5 ações destrutivas/sobrescritoras, ausência de paginação em 9 tabelas (com erro *off-by-one* em `temProximaPagina` nas 2 tabelas paginadas), rótulos crus `#ID`, jargão interno (`Sprint 05`, `Human-in-the-Loop`), menções a `@ufma.br` em 3 arquivos `*.spec.ts`, e ausência completa de UI para `Usuários`, `Campi` e `Frequência`, além de **0% de suporte a upload de arquivos e exportação PDF**. No backend/infra, `APScheduler` está morto em `requirements.txt`, `docker/cron/crontab` executa um `echo` simulado, `relatorio_metricas_ml.json` reflete avaliação sobre apenas 2 amostras sintéticas (`acuracia = 0.5`), todos os testes rodam exclusivamente em SQLite e o CI flexibiliza o limite de *diff* de 400 para 1.200 linhas com `|| true` em `ruff` e `bandit`.
4. **Fluxo "Cancelar Matrícula" (Aluno) e Regras de Negócio:** O perfil `aluno` dispõe de botão de clique único sem confirmação, exibindo apenas `Turma #<id>` (sem nome da disciplina, horário ou docente), conectado diretamente a `DELETE /api/v1/matriculas/{id}`, sem janela de calendário acadêmico/trancamento ou aprovação da Secretaria/Coordenação, distorcendo `Turma.num_matriculados`, alocação prévia de salas e o cálculo de `razao_ocupacao` do modelo de IA enquanto preserva registros de `Frequencia` ligados à matrícula cancelada.

### Metodologia e Ressalvas (Limitações)

- **Auditoria Estática Somente Leitura:** Nenhuma linha de código de aplicação, banco ou infraestrutura foi alterada. Todas as afirmações neste documento baseiam-se em leitura direta de código-fonte, arquivos de configuração, migrações, contratos OpenAPI, scripts e suítes de testes.
- **Baselines de Testes Automatizados Verificados:**
  - **Backend:** Execução completa de `python -m pytest tests --no-cov -o cache_dir=... -q` em `backend/` resultou em **`276 passed, 1 warning in 63.51s`** (29 arquivos `test_*.py`), utilizando banco em memória/arquivo **SQLite** e a biblioteca nativa `backend/motor_alocacao/motor_alocacao.dll`. Nenhuma suíte de testes automatizados foi executada contra uma instância viva do PostgreSQL 16 ou dentro de contêineres Docker.
  - **Frontend:** Execução completa de `npx ng test --watch=false --browsers=ChromeHeadless` em `frontend/` (22 arquivos `*.spec.ts` com `HttpTestingController`) resultou em **`TOTAL: 165 SUCCESS`** (código de saída `0`). Não foi executada sessão E2E contra backend e PostgreSQL ativos.
- **Ausência de PDFs Externos no Repositório:** Conforme busca recursiva em todo o repositório, os documentos externos mencionados nos requisitos — o PDF da disciplina **"Fábrica de Software - Aula 01"** (págs. 6, 10–12, 20 e 28–33) e o **enunciado do Projeto Final de DevOps (07/12/2026)** — **não estão presentes como arquivos em `c:\Work\workspace\SIGAAS`**. Apenas os relatórios e PDFs produzidos pelo próprio Grupo 31 constam em `docs/entregas/`. Portanto, todos os itens do checklist de funcionalidades (pág. 12) e critérios de DevOps/paralelismo aqui verificados derivam diretamente de `ORIGINAL_REQUEST.md` e das normas e especificações internas do repositório (`AGENTS.md`, `docs/`).
- **Artefatos Locais Não Versionados:** Os arquivos `.env`, `sigaas_local.db`, binários compilados (`motor_alocacao.so`, `motor_alocacao.dll`, `benchmark.exe`) e `modelo_absenteismo.joblib` existem no disco local, porém são ignorados pelo `.gitignore` e não fazem parte do índice Git (`git ls-files`). O conteúdo de `.env` e `sigaas_local.db` não foi lido para evitar exposição de dados locais de ambiente.

---

## Seção 1 — Arquitetura Atual e Fluxos Ponta a Ponta

O sistema SIGAAS adota arquitetura em camadas desacopladas composta por SPA Angular 20, API REST em FastAPI, biblioteca nativa em C11 + OpenMP carregada via `ctypes`, módulo de IA preditiva em `scikit-learn`, banco relacional PostgreSQL 16 com Alembic e orquestração em Docker Compose. Contudo, a inspeção detalhada expõe quebras importantes nas fronteiras arquiteturais documentadas e omissões de camadas previstas nas skills do projeto.

### 1.1 Frontend (Angular 20.2.0)

- **Empacotamento e Bootstrapping (`frontend/`):**
  - `frontend/package.json:2,27-51` e `frontend/angular.json:6,32-34,64,67,75-94`: Projeto batizado como `"frontend-init"`, Angular `^20.2.0` (`@angular/core`, `@angular/common`, `@angular/forms`, `@angular/router`, `@angular/platform-browser`), `rxjs ~7.8.0`, `zone.js ~0.15.0`, executor de testes Karma `~6.4.0` + Jasmine `~5.9.0`.
  - `frontend/src/index.html:2,5`: `<html lang="pt-BR">` e `<title>SIGAAS - Gestao de Salas e Escalas</title>`.
  - `frontend/src/app/app.config.ts:12-18`: Registra `provideZoneChangeDetection({ eventCoalescing: true })`, `provideRouter(routes)` e `provideHttpClient(withInterceptors([authInterceptor]))`.
  - `frontend/src/app/app.ts:10-12`: Componente raiz `App` com `<router-outlet />` e sinal não utilizado `protected readonly title = signal('frontend-init')` (`app.ts:11`).
- **Estilização, Ícones e Primitivas:**
  - **Zero framework CSS:** Não há Tailwind CSS, Bootstrap ou Angular Material em `package.json` ou `angular.json`. A folha global `frontend/src/styles.scss` possui 1.220 linhas com variáveis CSS (`:1-25`), complementada por arrays inline `styles: [...]` em 4 componentes (`login`, `secretaria`, `aluno`, `grade-horaria`).
  - **Zero biblioteca de ícones:** Não há `lucide-angular`, `@fortawesome` ou Material Icons. Existem **16 elementos `<svg>` de ícones embutidos** distribuídos em 6 templates (`shell.component.ts:22,44,64,84,109,127,150,176` [8 ícones], `admin.component.ts:354,369,373,387` [4 ícones], `secretaria.component.ts:134` [1 ícone], `aluno.component.ts:28` [1 ícone], `relatorios.component.ts:24` [1 ícone], `historico.component.ts:24` [1 ícone]), além de **2 laços `<svg class="bar-svg">` de gráficos** em `dashboard.component.ts:103,119`.
  - **Zero modais e zero componentes próprios de formulário:** Zero ocorrências de `<dialog>` ou overlays modais; todos os formulários usam `<select>`, `<input type="date">`, `<input type="number">` e `<input type="checkbox">` nativos (zero `<textarea>`).
- **Roteamento, Guards e Interceptor:**
  - `frontend/src/app/app.routes.ts:14-67`: Define `/login` (pública) e rota pai `''` protegida por `authGuard` (`ShellComponent`) com 7 rotas filhas protegidas por `roleGuard`: `dashboard`, `relatorios`, `historico`, `admin`, `secretaria`, `professor`, `aluno`, além de redirecionamento `'' -> 'admin'` (`:63`) e wildcard `'**' -> 'login'` (`:66`).
  - `frontend/src/app/guards/auth.guard.ts:5-14`: Consulta `authService.isAuthenticated()`, que verifica apenas `Boolean(this._token() && this._currentRole())` (`auth.service.ts:86-88`).
  - `frontend/src/app/guards/role.guard.ts:5-28`: Lê `route.data['roles']` ou `route.data['role']` e verifica `roles.some((r) => authService.hasRole(r))` (`:22`); em caso de negação, dispara `notifyAccessDenied(...)` e redireciona para `authService.getHomeRoute()`.
  - `frontend/src/app/interceptors/auth.interceptor.ts:7-28`: Injeta `Authorization: Bearer <token>` em requisições `/api/v1/` (exceto `/api/v1/auth/login`), realiza logout e redireciona para `/login` em HTTP `401`, e notifica erro de acesso em HTTP `403`.
- **Componentes de Layout e Páginas (11 componentes standalone):**
  - Layout: `ShellComponent` (`frontend/src/app/layout/shell/shell.component.ts`).
  - Páginas (9 arquivos em `frontend/src/app/pages/`): `LoginComponent` (`login/login.component.ts`), `AdminComponent` (`admin/admin.component.ts`), `SecretariaComponent` (`secretaria/secretaria.component.ts`), `ProfessorComponent` (`professor/professor.component.ts`), `AlunoComponent` (`aluno/aluno.component.ts`), `GradeHorariaComponent` (`grade-horaria/grade-horaria.component.ts` — reutilizável, sem rota direta), `DashboardComponent` (`dashboard/dashboard.component.ts`), `RelatoriosComponent` (`relatorios/relatorios.component.ts`), `HistoricoComponent` (`historico/historico.component.ts`).
- **Serviços Angular (9 arquivos em `frontend/src/app/services/`):**
  - `AuthService` (`auth.service.ts`), `AdminService` (`admin.service.ts`), `SecretariaService` (`secretaria.service.ts`), `AlocacaoService` (`alocacao.service.ts`), `IaService` (`ia.service.ts`), `HorarioService` (`horario.service.ts`), `DashboardService` (`dashboard.service.ts`), `RelatorioService` (`relatorio.service.ts`), `LogService` (`log.service.ts`).

### 1.2 Backend (FastAPI)

- **Entrypoint e Configuração:**
  - `backend/app/main.py:44-110`: Instancia `FastAPI`, configura `CORSMiddleware` para `["http://localhost:4200", "http://localhost:8000"]` (`:61-67`), define redirecionamentos `/docs`, `/redoc`, `/`, endpoint `/health` com `SELECT 1` (`:85-98`), rota raiz `/api/v1` (`:101-107`) e monta `api_router` em `/api/v1` (`:110`).
  - `backend/app/config.py:8-29`: `Settings(BaseSettings)` com `VERSION = "1.0.0-rc.1"`, `ALGORITHM = "HS256"`, `ACCESS_TOKEN_EXPIRE_MINUTES = 60` e valores *fallback* embutidos para `POSTGRES_PASSWORD`, `DATABASE_URL` e `SECRET_KEY`.
  - `backend/app/api/deps.py:11-96`: Define `reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`, `get_current_user` (`:14-50`), `require_role(*roles)` (`:53-62`), `require_campus_access(resource_campus_id, current_user)` (`:65-85`, *fail-closed* com HTTP `404` para não-`ADMIN`) e `montar_padrao_ilike(q)` (`:88-96`).
- **Ausência da Camada `repositories/`:**
  - Verificou-se que o diretório `backend/app/repositories/` **não existe** no repositório. Os 16 roteadores em `backend/app/api/v1/endpoints/` executam consultas e mutações SQLAlchemy diretamente sobre `Session = Depends(get_db)`, violando a separação estrita `Routers -> Services -> Repositories` descrita na skill `fastapi-domain-patterns`.
- **Roteadores e Serviços (`backend/app/api/v1/api.py:28-44` e `backend/app/services/`):**
  - 16 módulos de endpoints montados sob 17 prefixos em `/api/v1`: `/auth` (`auth.py`), `/campi` (`campi.py`), `/usuarios` (`usuarios.py`), `/cursos` (`cursos.py`), `/disciplinas` (`disciplinas.py`), `/salas` (`salas.py`), `/equipamentos` (`equipamentos.py`), `/turmas` (`turmas.py`), `/matriculas` (`matriculas.py`), `/horarios` (`horarios.py`), `/motor` (`motor.py`), `/alocacao` (`alocacao.py`), `/sugestoes` e `/ia` (`sugestoes.py`), `/logs` (`logs.py`), `/dashboard` (`dashboard.py`) e `/relatorios` (`relatorios.py`).
  - 7 módulos de serviço em `backend/app/services/`: `dashboard_service.py`, `export_service.py` (streaming CSV com UTF-8 BOM, sanitização contra CSV injection `PREFIXOS_PERIGOSOS_CSV` e teto `MAX_EXPORT_ROWS = 10000`), `ia_service.py`, `log_service.py`, `ml_evaluator.py`, `motor_service.py` e `relatorio_service.py`.

### 1.3 Motor de Alocação em C e Ponte FFI (`ctypes`)

- **Arquivos Fonte e Build:**
  - `backend/motor_alocacao/motor.h:1-87`: Define as structs de contrato `SalaC`, `TurmaC`, `AlocacaoItemC` e `MetricasAlocacaoC` (com campo `int padding;` na linha 60 para alinhamento de 64 bits) e os 4 símbolos exportados: `otimizar_alocacao_salas`, `executar_benchmark_cenario`, `obter_versao_motor` e `testar_integracao_ctypes`.
  - `backend/motor_alocacao/motor.c:1-435`: Implementa heurística construtiva gulosa *Best-Fit Decreasing* (BFD) multi-start com perturbação determinística de ordenação (`gerar_ordem_turmas`, `:102-117`) e penalização por uso indevido de salas especializadas (`+500` para laboratório, `+300` para auditório/reunião em turmas regulares, `:162-166`).
  - `backend/motor_alocacao/benchmark.c:1-46`: Executável CLI para cenários `20x10`, `100x40` e `500x150` em `{1, 2, 4, 8}` threads.
  - `backend/motor_alocacao/Makefile:1-23`: Compila com `gcc` e flags `-Wall -Wextra -pedantic -std=c11 -O3 -fPIC -fopenmp` / `-shared -fopenmp`.
  - `backend/app/motor/motor_alocacao.h:1-6`: Cabeçalho ponte que inclui `../../motor_alocacao/motor.h`.
- **Integração `ctypes` (`backend/app/services/motor_service.py:124-328`):**
  - `MotorAlocacaoService` localiza `motor_alocacao.dll` (Windows) ou `motor_alocacao.so` (Linux), auto-compila via `gcc` se ausente (`_compilar_se_necessario`, `:133-149`), carrega com `ctypes.CDLL` (`_carregar_biblioteca`, `:168-174`), configura explicitamente `argtypes` e `restype` (`_configurar_assinaturas`, `:176-201`) e expõe `get_status()`, `executar_teste()`, `otimizar_alocacao()` e `executar_benchmark()`.

### 1.4 Módulo de IA Preditiva, Agendador e Human-in-the-Loop

- **Pipeline Preditivo (`backend/app/services/ia_service.py:38-205`):**
  - `criar_pipeline_absenteismo` (`:38-75`) constrói um `Pipeline` do `scikit-learn` com `ColumnTransformer` (`StandardScaler` sobre `["dia_semana", "hora_inicio_minutos", "num_matriculados", "capacidade_sala", "razao_ocupacao"]` e `OneHotEncoder` sobre `["turno"]`), seguido por `HistGradientBoostingClassifier(random_state=42, max_iter=100, min_samples_leaf=5, learning_rate=0.08)` encapsulado em `CalibratedClassifierCV(estimator=base_clf, method="sigmoid", cv=2)`.
  - `extrair_dataset_frequencias` (`:98-146`) ordena cronologicamente por `Frequencia.data.asc()` e recorre a 10 linhas sintéticas fixas em `_gerar_dados_sinteticos_priors()` (`:78-95`) quando a tabela `frequencia` está vazia.
  - `treinar_modelo_absenteismo` (`:149-205`) aplica `TimeSeriesSplit(n_splits=min(3, len(X) // 5))` quando `len(X) >= 15` e serializa o artefato em `backend/app/ml/modelo_absenteismo.joblib` (`31.302` bytes no disco local, ignorado pelo Git).
  - **Avaliação (`backend/app/services/ml_evaluator.py` e `backend/scripts/evaluate_model.py`):** O relatório commitado em `backend/app/ml/relatorio_metricas_ml.json:1-18` foi gerado sobre apenas `total_amostras = 2` (20% dos 10 *priors* sintéticos), registrando `acuracia: 0.5`, `precisao: 0.5`, `recall: 1.0`, `f1_score: 0.6667`, `roc_auc: 0.5` e `brier_score: 0.25`.
- **Agendador (`APScheduler` morto vs. `cron` simulado):**
  - `apscheduler>=3.10.4` está declarado em `backend/requirements.txt:20`, mas possui **zero importações ou chamadas** em `backend/app/main.py` ou qualquer outro arquivo Python.
  - O serviço `cron` no Docker (`docker/cron/crontab:4`, `docker/cron/Dockerfile`, `docker/cron/entrypoint.sh`) executa a cada 6 horas apenas um comando fictício (`echo "Execucao periodica de rotinas agendadas..." >> /var/log/cron.log 2>&1`), jamais acionando inferência ou retreinamento da IA.
- **Fluxo Human-in-the-Loop (`backend/app/api/v1/endpoints/sugestoes.py:94-205`):**
  - `gerar_sugestoes_remanejamento` (`ia_service.py:266-425`) jamais altera `Horario.sala_id`; apenas grava `PrevisaoFalta` e cria `SugestaoRemanejamento` com `status = StatusSugestao.PENDENTE` quando `taxa_ociosidade >= 0.40` e o desperdício de assentos é `>= 10`.
  - A alteração real de sala ocorre exclusivamente via `PATCH /api/v1/sugestoes/{sugestao_id}` (`aprovar_ou_rejeitar_sugestao`, restrito a `ADMIN`/`COORDENADOR`), utilizando bloqueio pessimista `.with_for_update()` (ignorado pelo SQLite nos testes), isolamento por campus, checagem de conflito de sala (`409 Conflict`), atualização de `horario.sala_id` e gravação de `LogAlocacao` (com falha de classificação de evento: registra `TipoEventoLog.ALTERACAO` na linha 185 em vez de `TipoEventoLog.REMANEJAMENTO`, e não grava log algum em caso de `REJEITADO` nas linhas 196-200).

### 1.5 Banco de Dados (PostgreSQL 16 / SQLAlchemy 2.0 / Alembic)

- **Esquema de 14 Tabelas em 8 Módulos (`backend/app/models/`):**
  - `campus` (`campus.py`), `usuario` (`usuario.py`), `equipamento`, `sala`, `sala_equipamento` (`sala.py`), `curso`, `disciplina`, `turma`, `matricula` (`academico.py`), `horario`, `log_alocacao` (`alocacao.py`), `frequencia`, `previsao_falta`, `sugestao_remanejamento` (`ia.py`).
- **3 Migrações Alembic (`backend/alembic/versions/`):**
  1. `001_initial_schema.py`: Cria as 14 tabelas, chaves estrangeiras, `UniqueConstraint`s e restrições numéricas/temporais (`capacidade > 0`, `hora_inicio < hora_fim`, `dia_semana >= 0 AND dia_semana <= 6`).
  2. `002_add_campus_id_to_log_alocacao.py`: Adiciona `campus_id` (`ON DELETE SET NULL`), índices e *backfill* a partir de `horario`.
  3. `003_release_candidate_indexes.py`: Cria 6 índices compostos para consultas de `horario`, `frequencia`, `previsao_falta` e `sugestao_remanejamento`.
- **Lacunas Estruturais Identificadas no Banco:**
  - **Ausência de `CHECK` constraints de Enums na migração inicial:** Os modelos SQLAlchemy declaram `SQLEnum(..., native_enum=False, create_constraint=True)`, mas `001_initial_schema.py` cria colunas `sa.String(...)` simples sem restrições SQL `CHECK` para `usuario.perfil` (L40), `sala.tipo` (L69), `turma.turno_preferido` (L134), `log_alocacao.tipo_evento` (L192) e `sugestao_remanejamento.status` (L246).
  - **Ausência de `Turma.vagas` / `capacidade_maxima`:** `Turma` (`academico.py:52-71`) armazena apenas `num_matriculados`, sem limite de vagas ofertadas.
  - **Campo `Matricula.status` sem enum:** Declarado como `String(20)` sem enum nem restrição `CHECK` (`academico.py:84`, `001_initial_schema.py:153`).
  - **Ausência de `btree_gist` / `ExclusionConstraint` em `Horario`:** Zero ocorrências no repositório; sobreposições de sala ou docente no mesmo dia/horário não são bloqueadas pelo PostgreSQL.
  - **Cadeias `ondelete="CASCADE"` destrutivas:** `horario.turma_id` (`alocacao.py:33`) e os relacionamentos `frequencia.horario_id` (`ia.py:27`), `previsao_falta.horario_id` (`ia.py:44`) e `sugestao_remanejamento.horario_id` (`ia.py:61`) usam `CASCADE`.

### 1.6 Docker Compose e CI/CD

- **Docker Compose (`docker/compose/docker-compose.{local,homolog,prod}.yml` e `docker-compose.yml` raiz):**
  - Todos os 3 ambientes orquestram 4 serviços: `db` (`postgres:16-alpine`), `backend` (`python:3.12-slim` + `build-essential` + `make` do motor C), `frontend` (multi-stage `node:22-alpine` -> `nginx:1.27-alpine` com proxy `/api/` -> `http://backend:8000/api/`) e `cron`.
  - **Falha no `docker/backend/Dockerfile:23`:** O `CMD` inicia `uvicorn app.main:app` diretamente sem executar `alembic upgrade head` na subida do contêiner (dependendo de execução manual via `Makefile:setup` ou `migrate`).
  - **Sombreamento de binário C em `docker-compose.local.yml:43`:** O *bind mount* `../../backend:/app` sobrepõe o diretório `/app/motor_alocacao` compilado no build Linux da imagem, expondo o contêiner ao `motor_alocacao.so` compilado no host Windows.
- **CI/CD (`.github/workflows/` e `.coderabbit.yaml`):**
  - `ci.yml` executa apenas em `push`/`pull_request` para `main` (jobs `stage-governance`, `test-backend`, `test-motor-c`, `test-frontend`, `docker-smoke-test`).
  - `release.yml` publica *releases* no GitHub apenas para tags `v*.*.*` e `v*.*.*-sprint*`.
  - **Ausências de DevOps (0% no repositório):** Zero ocorrências de `zabbix`, `grafana`, `postman`, workflows de deploy em nuvem AWS (`EC2`/`ECS`/`SSH`) ou pipelines de branch `Staging`.

### 1.7 Fluxos Ponta a Ponta Principais

#### Fluxo A — Autenticação, Sessão JWT e Proteção de Rotas
```text
[LoginComponent] (email, senha)
   |  POST /api/v1/auth/login (AuthService.login)
   v
[auth.py:login] -> busca Usuario -> bcrypt.checkpw (ou DUMMY_HASH em tempo constante)
   |  gera JWT HS256 (sub, email, perfil, campus_id, exp=60m)
   v
[AuthService] grava sigaas_token + sigaas_user em localStorage -> navega por perfil
   |  rotas filhas de ShellComponent
   v
[authGuard] verifica apenas presenca de token e perfil (NAO valida exp do JWT)
   |
[roleGuard] chama hasRole() (ATENCAO: hasRole('admin') aceita 'coordenador')
   |
[authInterceptor] injeta Authorization: Bearer <token>; trata 401 (logout) e 403 (banner)
```

#### Fluxo B — Otimização Combinatória de Salas (C/OpenMP) e Persistência
```text
[AdminComponent] (aba Alocacao, formSalvarNoBanco=true sem modal de confirmacao)
   |  POST /api/v1/alocacao/otimizar (AlocacaoService.otimizarAlocacao)
   v
[alocacao.py:otimizar_alocacao_endpoint] (ADMIN ou COORDENADOR)
   |  converte Turma -> TurmaC (sem professor_id; dia = idx % 5; bloco fixo 2h/4h)
   |  converte Sala  -> SalaC
   v
[motor_service.py:otimizar_alocacao] -> ctypes.CDLL -> otimizar_alocacao_salas()
   |  [motor.c:325-334] executa busca 1x SEQUENCIAL (descarta res_seq) + 1x PARALELA (OpenMP)
   v
[alocacao.py:295] se salvar_no_banco=True:
   |  DELETE FROM horario WHERE turma_id IN (...)  --> CASCADE apaga Frequencia, PrevisaoFalta, Sugestao
   |  INSERT novos Horario + LogAlocacao (CRIACAO)
```

#### Fluxo C — IA Preditiva de Absenteísmo e Remanejamento Human-in-the-Loop
```text
[AdminComponent] (aba Remanejamento -> "Executar Analise Preditiva")
   |  POST /api/v1/ia/analisar (IaService.dispararAnalise)
   v
[sugestoes.py] -> [ia_service.py:gerar_sugestoes_remanejamento]
   |  carrega modelo_absenteismo.joblib (HistGradientBoosting + CalibratedClassifierCV)
   |  grava PrevisaoFalta + SugestaoRemanejamento(status='pendente') se ociosidade >= 40% e >= 10 vagas
   |  (NUNCA altera Horario.sala_id diretamente)
   v
[AdminComponent] usuario clica Aprovar ou Rejeitar (sem modal de confirmacao)
   |  PATCH /api/v1/sugestoes/{id} (IaService.aprovarSugestao / rejeitarSugestao)
   v
[sugestoes.py:94-205] (.with_for_update(), checa conflito 409)
   |  se APROVADO : atualiza Horario.sala_id + LogAlocacao(tipo_evento='alteracao' [bug: deveria ser 'remanejamento'])
   |  se REJEITADO: atualiza SugestaoRemanejamento (sem gerar LogAlocacao)
```

---

## Seção 2 — Verificação Empírica do Paralelismo no Motor de Alocação

### 2.1 Prova Técnica: Exclusivamente OpenMP em CPU (0% OpenCL / CUDA)

A busca exaustiva em todo o repositório (excluindo binários, `node_modules`, `.git`, `.angular`, `dist`, `__pycache__` e PDFs de entregas) para o padrão `OpenCL|clCreate|CL/cl\.h|-lOpenCL|__global__|cudaMalloc|nvcc|\bCUDA\b|cuda\.h` retornou **zero ocorrências**. Em contrapartida, todas as camadas de compilação, cabeçalho, implementação C e *wrapper* Python utilizam exclusivamente OpenMP em CPU:

1. **Sistema de Build e Dockerfiles (`-fopenmp`):**
   - `backend/motor_alocacao/Makefile:2-4`:
     ```makefile
     CC = gcc
     CFLAGS = -Wall -Wextra -pedantic -std=c11 -O3 -fPIC -fopenmp
     LDFLAGS = -shared -fopenmp
     ```
   - `backend/Dockerfile:18` e `docker/backend/Dockerfile:19`:
     ```dockerfile
     RUN cd /app/motor_alocacao && make clean && make
     ```
   - `backend/app/services/motor_service.py:139-142`: A auto-compilação em tempo de execução invoca `gcc` com `"-O3", "-fPIC", "-fopenmp", "-shared"`.
2. **Diretivas e Chamadas de Runtime OpenMP em `backend/motor_alocacao/motor.c`:**
   - Inclusão exclusiva de OpenMP (`motor.c:4`): `#include <omp.h>`
   - Região paralela e distribuição dinâmica de iterações multi-start (`motor.c:224-245`):
     ```c
     #pragma omp parallel num_threads(num_threads) default(none) \
         shared(turmas, num_turmas, salas, num_salas, num_iteracoes, ordem_base_bfd, \
                melhor_resultado, melhor_score_global, global_alocados, global_pendentes)
     {
         ...
         #pragma omp for schedule(dynamic, 16)
         for (int iter = 0; iter < num_iteracoes; iter++) {
     ```
   - Seção crítica para redução da melhor solução global (`motor.c:266-274`):
     ```c
     #pragma omp critical
     {
         if (melhor_score_thread > melhor_score_global) {
             melhor_score_global = melhor_score_thread;
             ...
     ```
   - Consulta de núcleos e temporização OpenMP (`motor.c:309, 325, 327, 331, 333`): `omp_get_num_procs()` e `omp_get_wtime()`.
   - Identificação e teste de integração (`motor.c:421-435`): `obter_versao_motor()` retorna `"SIGAAS Motor de Alocacao v0.2.0 (OpenMP Parallel Best-Fit)"` e `testar_integracao_ctypes` utiliza `#pragma omp parallel` + `#pragma omp single`.

### 2.2 Defeitos Algorítmicos, Estruturais e de Integridade no Subsistema de Alocação

1. **Dupla Execução (Sequencial + Paralela) em Chamadas de Produção (`motor.c:325-334`):**
   ```c
   double t0_seq = omp_get_wtime();
   executar_busca_combinatoria(turmas, num_turmas, salas, num_salas, 1, num_iteracoes, res_seq, &seq_alocado, &seq_pendente);
   double t1_seq = omp_get_wtime();
   ...
   double t0_par = omp_get_wtime();
   executar_busca_combinatoria(turmas, num_turmas, salas, num_salas, threads_alvo, num_iteracoes, resultado_out, &par_alocado, &par_pendente);
   double t1_par = omp_get_wtime();
   ```
   Toda chamada em produção a `POST /api/v1/alocacao/otimizar` (`alocacao.py:224-228` -> `motor_service.py:256-264`) executa toda a busca combinatória duas vezes (1 thread e depois `threads_alvo` threads) e descarta `res_seq` (`motor.c:336`), multiplicando o tempo de resposta apenas para preencher `tempo_sequencial_ms` e `speedup`.
2. **Ausência de `professor_id` em `TurmaC` e Zero Verificação de Conflito Docente:**
   O modelo `Turma` possui `professor_id` (`backend/app/models/academico.py:60`), mas a struct C `TurmaC` (`backend/motor_alocacao/motor.h:32-40`) e o espelho Python `TurmaC(ctypes.Structure)` (`backend/app/services/motor_service.py:87-96`) contêm apenas 7 campos (`id`, `num_matriculados`, `tipo_exigido`, `turno`, `dia_semana_sugerido`, `hora_inicio_min`, `hora_fim_min`). Em `motor.c:147-173` (`executar_tentativa`), verifica-se exclusivamente `sala_tem_conflito(...)` (`:154-156`), permitindo que o mesmo professor seja alocado simultaneamente em duas salas diferentes no mesmo horário.
3. **Heurística Ingênua `idx % 5` e Blocos Fixos em `alocacao.py:178-195`:**
   ```python
   for idx, t in enumerate(turmas_db):
       ...
       turno_int = _converter_turno_enum(t.turno_preferido)
       dia_sugerido = idx % 5  # Segunda (0) a Sexta (4)
       if turno_int == TURNO_MATUTINO:
           ini_min, fim_min = 480, 600  # 08:00 - 10:00
       elif turno_int == TURNO_VESPERTINO:
           ini_min, fim_min = 840, 960  # 14:00 - 16:00
       elif turno_int == TURNO_NOTURNO:
           ini_min, fim_min = 1140, 1260  # 19:00 - 21:00
       else:
           ini_min, fim_min = 480, 720  # 08:00 - 12:00
   ```
   O código ignora `Disciplina.carga_horaria` e atribui um único bloco fixo de 2h (ou 4h no integral) por turno e dia `idx % 5`, impedindo distribuição por janelas horárias alternativas e causando colisões inevitáveis entre turmas de mesmo índice modular e turno.
4. **Exclusão Destrutiva em Cascata em Reotimizações (`alocacao.py:295`):**
   Quando `salvar_no_banco=True`, `alocacao.py:295` executa `db.execute(delete(Horario).where(Horario.turma_id.in_(turmas_ids)))`. Como `Frequencia.horario_id` (`backend/app/models/ia.py:27`), `PrevisaoFalta.horario_id` (`ia.py:44`) e `SugestaoRemanejamento.horario_id` (`ia.py:61`) definem `ondelete="CASCADE"`, reexecutar a alocação apaga permanentemente todo o histórico de frequência, previsões e sugestões de remanejamento das turmas reprocessadas (enquanto `LogAlocacao.horario_id` usa `ondelete="SET NULL"`).
5. **Clamping Estatístico no Benchmark, Contrato `MotorStatusResponse` e Risco de Sombreamento Binário:**
   - **Clamping (`backend/scripts/run_benchmarks_ci.py:205-212`):** Amostras com desvio superior a 14% da mediana são grampeadas em `[0.88 * med, 1.12 * med]` antes do cálculo do coeficiente de variação (`CV < 15%`), mascarando oscilações reais de escalonamento.
   - **Perda de campo na API (`motor.py:21-25` vs. `motor_service.py:218`):** `MotorStatusResponse` omite o campo `"heuristica"` retornado por `motor_service.get_status()`, fazendo o FastAPI descartá-lo na resposta HTTP.
   - **Binário Windows no diretório `.so`:** Embora `.so`, `.dll`, `.exe` e `.joblib` estejam no `.gitignore` (e ausentes de `git ls-files`), o diretório local `backend/motor_alocacao/` contém `motor_alocacao.dll` e `motor_alocacao.so` com exatamente `103.964` bytes cada (compilado em Windows), além de `benchmark.exe` (`146.688` bytes). Em `docker/compose/docker-compose.local.yml:43`, o volume `../../backend:/app` sobrescreve o `.so` Linux compilado durante o build da imagem Docker.

---

## Seção 3 — Auditoria de Segurança, Hashing, MFA e Isolamento

### 3.1 Hashing de Senhas e Política de Credenciais

- **Implementação de Hashing (`backend/app/core/security.py:4,11,14-28`):**
  - Utiliza diretamente a biblioteca `bcrypt` (`import bcrypt`, linha 4), com `DUMMY_HASH` constante (`linha 11`) avaliado em `auth.py:36-37` para mitigar ataques de *timing* na enumeração de e-mails.
  - `backend/requirements.txt:16` lista `passlib[bcrypt]>=1.7.4`, dependência morta não importada em nenhum arquivo do projeto.
- **Assimetria Crítica do Limite de 72 Bytes do `bcrypt`:**
  - `verify_password` (`security.py:17-20`) verifica explicitamente `if len(raw_bytes) > 72: return False`.
  - Em contrapartida, `UsuarioCreate.senha` (`backend/app/schemas/usuario.py:17`) exige apenas `min_length=6` (**sem `max_length=72`**), e `get_password_hash` (`security.py:25-28`) repassa `password.encode("utf-8")` diretamente a `bcrypt.hashpw`, podendo causar `ValueError` em versões recentes de `bcrypt` no cadastro ou criar contas impossíveis de autenticar.
- **Ausência de Troca e Redefinição de Senha:** `UsuarioUpdate` (`schemas/usuario.py:20-25`) declara `ConfigDict(extra="forbid")` apenas com `nome`, `email`, `perfil` e `ativo`, sem campo `senha`, e nenhum endpoint em `auth.py` ou `usuarios.py` permite alteração ou recuperação de senha.

### 3.2 Tokens JWT, Segredos e Exposição em Frontend

- **Emissão e Validação Backend (`security.py:31-46`, `config.py:20-26`):**
  - Tokens são assinados via `python-jose` com `HS256` e expiração padrão `ACCESS_TOKEN_EXPIRE_MINUTES = 60`.
  - `backend/app/config.py:20-24` e os arquivos `docker/compose/docker-compose.local.yml:9,33-35,72-73` e `docker-compose.homolog.yml:9,33-34,68-69` mantêm segredos *fallback* em texto claro (`changeme_local_only`, `changeme_homolog_only`, `super-secret-key-change-in-production-min-32-chars`). (`docker-compose.prod.yml` exige variáveis de ambiente sem valor padrão; `.env` e `sigaas_local.db` existem no disco local, porém são ignorados pelo `.gitignore` e não constam no `git ls-files`).
- **Vulnerabilidades de Sessão no Frontend:**
  - `authGuard` / `AuthService.isAuthenticated()` (`frontend/src/app/services/auth.service.ts:86-88`) verifica apenas `Boolean(this._token() && this._currentRole())`, **sem decodificar o JWT ou checar o claim `exp`**, mantendo sessões expiradas como autenticadas na interface até a próxima falha `401` de rede.
  - `AuthService.setRole()` (`auth.service.ts:121-128`) permanece compilado no serviço de produção, permitindo injetar `session_${role}_token` sintético em memória para troca artificial de perfil.

### 3.3 Ausência Total de MFA / 2FA

- A busca em todo o código-fonte de backend, infraestrutura e frontend por `pyotp|totp|mfa|2fa` retornou **0 ocorrências**. Não há segredo TOTP na tabela `usuario`, nem desafio de segundo fator no fluxo de `POST /api/v1/auth/login` ou na interface de `LoginComponent`.

### 3.4 Endpoints Sem Autenticação e Controle de Acesso

Foram comprovados **6 endpoints expostos sem `Depends(get_current_user)` ou `require_role(...)`**:
- `backend/app/api/v1/endpoints/campi.py:16-40`: `GET /api/v1/campi`, **`POST /api/v1/campi` (CRÍTICO: criação anônima de campus no banco)** e `GET /api/v1/campi/{campus_id}`.
- `backend/app/api/v1/endpoints/equipamentos.py:17-25`: `GET /api/v1/equipamentos`.
- `backend/app/api/v1/endpoints/motor.py:34-74`: `GET /api/v1/motor/status` (consultado sem auth pelo *smoke test* em `.github/workflows/ci.yml:199,203`) e **`POST /api/v1/motor/teste-integracao` (executa código nativo C via FFI sem autenticação)**.

### 3.5 Matriz Completa de RBAC e Isolamento Multi-Campus (Backend vs. Frontend)

| Recurso / Prefixo | Backend (`require_role` e Isolamento de Campus) | Frontend (`app.routes.ts`, `ShellComponent` e Páginas) | Divergências / Falhas Verificadas |
|---|---|---|---|
| `/auth` (`auth.py`) | `POST /login` público; `GET /me` autenticado | `LoginComponent` (`/login`) | Sem MFA; sem troca/reset de senha; `authGuard` não valida `exp` |
| `/campi` (`campi.py`) | **Sem autenticação** em `GET ""`, `POST ""`, `GET /{id}` | Inexistente (Dashboard usa lista estática `#1/#2/#3`) | Criação e enumeração anônimas no backend; sem UI |
| `/usuarios` (`usuarios.py`) | `GET/POST/PATCH`: `ADMIN`, `COORDENADOR`, `SECRETARIA`; `GET /{id}`: todos (self para `ALUNO`/`PROFESSOR`); hierarquia e campus isolados | Inexistente (`AdminService.listarUsuarios()` não utilizado) | CRUD completo no backend sem nenhuma tela/rota no frontend |
| `/cursos` & `/disciplinas` | `GET`: todos autenticados (campus filtrado); `POST`: `ADMIN`, `COORDENADOR`, `SECRETARIA` | `/secretaria` restrito exclusivamente a `role: 'secretaria'` | `admin` e `coordenador` bloqueados pelo `roleGuard` no frontend; sem `PATCH`/`DELETE` e sem `LogAlocacao` |
| `/salas` (`salas.py`) | `GET`: todos (campus); `POST/PATCH/PUT/equip`: `ADMIN`, `COORDENADOR`; `DELETE /{id}`: apenas `ADMIN` (sem `require_campus_access`, confia no papel global) | `/admin` aceita `admin` e `coordenador` (`hasRole('admin')` retorna `true` para `coordenador`) | `coordenador` enxerga botão `Excluir` e recebe **403**; `admin` fica preso ao próprio `campus_id` na UI |
| `/equipamentos` | `GET`: **sem auth**; `POST`: `ADMIN`, `COORDENADOR` | `/admin` (aba Equipamentos) | `GET` público sem JWT; sem `PATCH`/`DELETE`/desvinculação |
| `/turmas` (`turmas.py`) | `GET`: todos (campus); `POST/PATCH`: `ADMIN`, `COORDENADOR`, `SECRETARIA` | `/secretaria` (somente criação/listagem; sem edição) | `admin`/`coordenador` bloqueados na UI; `PATCH /turmas/{id}` não exposto no frontend |
| `/matriculas` (`matriculas.py`) | `GET`: filtrado por perfil; `POST`: `ADMIN`, `COORDENADOR`, `SECRETARIA`; `DELETE`: inclui **`ALUNO`** (própria matrícula) | `/secretaria` (`POST`/`DELETE`) e `/aluno` (`DELETE` sem confirmação) | `POST` sem checagem de vagas/capacidade nem `LogAlocacao`; `DELETE` irrestrito para `ALUNO` |
| `/horarios` (`horarios.py`) | `GET /meus`, `GET ""`, `GET /{id}`: autenticados; `ADMIN` com `campus_id` no cadastro fica silenciosamente filtrado em `/meus` (`:43-45`) | `/professor` e `/aluno` (`GradeHorariaComponent` via `/meus`); `listarHorarios()` morto | Filtro silencioso para `ADMIN` em `/meus`; `GET /horarios` aberto a todos do campus |
| `/motor` (`motor.py`) | `GET /status` e `POST /teste-integracao`: **sem auth** | Não consumido diretamente pelo Angular | Execução FFI nativa anônima; `MotorStatusResponse` descarta `"heuristica"` |
| `/alocacao` (`alocacao.py`) | `POST /otimizar`: `ADMIN`, `COORDENADOR`; `POST /benchmark`: apenas `ADMIN` | `/admin` (aba Alocação) exibe ambos a `coordenador` | `coordenador` enxerga botão `Benchmark Cientifico` e recebe **403**; `admin` sem seletor de campus |
| `/sugestoes` & `/ia` | `GET`, `PATCH /{id}`, `POST /analisar`: `ADMIN`, `COORDENADOR` (campus) | `/admin` (aba Remanejamento) | `REJEITADO` não grava `LogAlocacao`; `APROVADO` grava `ALTERACAO` em vez de `REMANEJAMENTO` |
| `/logs` (`logs.py`) | `GET ""`: `ADMIN`, `COORDENADOR`, `SECRETARIA` (campus) | `/historico` aceita apenas `['admin', 'coordenador']` (`app.routes.ts:37`, `shell.component.ts:147`) | `secretaria` impedida de acessar `/historico` na UI apesar de autorizada no backend |
| `/dashboard` & `/relatorios` | `GET`: `ADMIN`, `COORDENADOR`, `SECRETARIA` (`resolver_escopo_campus`) | `/dashboard` e `/relatorios` (`['admin', 'coordenador', 'secretaria']`) | Dashboard com campi fixos `#1/#2/#3`; Relatórios sem PDF e com bug `temProximaPagina` |
| Rota raiz `''` (Frontend) | N/A | `app.routes.ts:63` redireciona `''` para `'admin'` | `secretaria`, `professor` e `aluno` ao acessar `/` recebem banner `"Acesso restrito..."` antes do redirect |

---

## Seção 4 — Inventário de AISlop, Dívidas Técnicas e Cobertura das Funcionalidades (Aula 01, pág. 12)

### 4.1 Inventário de AISlop e Dívidas Técnicas no Frontend

| Categoria | Arquivo e Linha(s) | Evidência Verificada |
|---|---|---|
| **Restos de *scaffold* (`frontend-init`)** | `frontend/package.json:2`; `frontend/angular.json:6,64,67`; `frontend/src/app/app.ts:11` | `"name": "frontend-init"`, chaves `"frontend-init"` no `angular.json` e `signal('frontend-init')` não utilizado em `App`. |
| **Opções estáticas e padrões mágicos** | `dashboard.component.ts:49-51`; `admin.component.ts:444,512,610,709,724`; `secretaria.component.ts:191`; `ia.service.ts:129` | Seletor de campus fixo em `Campus #1`, `#2`, `#3`; período letivo `'2026.1'` chumbado; benchmark `'medio'` chumbado; limiar `0.4` chumbado; `['matutino', 'vespertino', 'noturno']` omitindo `'integral'`. |
| **Código, sinais e CSS mortos** | `admin.service.ts:70-71,97-102`; `secretaria.service.ts:114-117`; `horario.service.ts:47-48,84-99`; `grade-horaria.component.ts:133-135`; `auth.service.ts:121-128`; `styles.scss:962-995`; `dashboard.component.ts:131` | `usuarios`/`listarUsuarios()`, `obterTurma()`, `listaHorarios`/`listarHorarios()` e `formatarHorario()` sem nenhum chamador; `AuthService.setRole()` *stub* de teste em produção; `.roles-list`/`.btn-role` sem uso; classe `.table-card-header` referenciada sem definição em `styles.scss`. |
| **CSS conflitante e estilos duplicados** | `styles.scss:398-406` vs. `:1165-1168`; `styles.scss:652-679` vs. `:1037-1053`; `secretaria.component.ts:151-165`; `aluno.component.ts:37-47`; `grade-horaria.component.ts:51-77`; `login.component.ts:57-65` | `.shell-header` e `.kpi-card`/`.kpi-label`/`.kpi-value` declarados duas vezes com regras conflitantes; 4 componentes com `styles: [...]` inline divergentes do `styles.scss` (`.btn-primary`, `.tabs-nav`, `.btn-danger-sm` vs. `.btn-delete`, azul `#0284c7` isolado). |
| **Rótulos crus de dump de banco (`#ID`)** | `shell.component.ts:173`; `secretaria.component.ts:75,111,123,134`; `aluno.component.ts:25`; `dashboard.component.ts:150-151`; `historico.component.ts:62`; `admin.component.ts:145,241,309` | Exibição literal de `Campus #{{ campusId }}`, `Curso #{{ d.curso_id }}`, `Disciplina #{{ t.disciplina_id }}`, `Prof. #{{ t.professor_id }}`, `Turma #{{ m.turma_id }}`, `Aluno #{{ m.aluno_id }}`, `Usuario #{{ ev.usuario_responsavel }}`, `#{{ eq.id }}`. |
| **Jargão interno de sprint/dev na UI** | `admin.component.ts:26,157,264`; `historico.component.ts:20` | Títulos e subtítulos para usuário final expondo `"Motor de Alocacao Paralelo OpenMP (Sprint 05)"`, `"(Human-in-the-Loop)"` e `"(LogAlocacao)"`. |
| **Menções a `@ufma.br` nos testes** | `admin.component.spec.ts:26,71,517`; `secretaria.component.spec.ts:29,36,194`; `admin.service.spec.ts:209` | E-mails de mock `@ufma.br` em desacordo com `AGENTS.md` §4.8 (proibição de extrapolação institucional não documentada). |
| **Acessibilidade (WCAG) e acentuação** | `admin.component.ts`, `secretaria.component.ts`, `styles.scss:223-226`, `login.component.ts:62`, `index.html:5` e todas as páginas | Campos sem `<label>` (apenas `placeholder`), **0 ocorrências** de `aria-live` e `scope="col"` em `frontend/src/`, `outline: none` em `:focus` sem anel de foco alternativo, e omissão sistemática de acentuação/cedilha em português em toda a UI (`Gestao`, `Usuario`, `Matricula`, `Acoes`, `Ocupacao`, `Historico`, `Relatorios`, `Terca-feira`, `Sabado`). |

### 4.2 Inventário de AISlop e Dívidas Técnicas no Backend, IA e Infraestrutura

| Categoria | Arquivo e Linha(s) | Evidência Verificada |
|---|---|---|
| **Contêiner `cron` simulado (*stub*)** | `docker/cron/crontab:4`; `docker/cron/Dockerfile`; `docker/cron/entrypoint.sh` | Executa apenas `echo "Execucao periodica de rotinas agendadas..." >> /var/log/cron.log 2>&1`. |
| **Dependências mortas** | `backend/requirements.txt:16,20` | `passlib[bcrypt]>=1.7.4` e `apscheduler>=3.10.4` declarados sem nenhuma importação no código. |
| **Relatório ML de brinquedo (2 amostras)** | `backend/app/ml/relatorio_metricas_ml.json:1-18`; `backend/scripts/evaluate_model.py:63-83` | Avaliação sobre `total_amostras = 2` (split 20% de 10 *priors* sintéticos), com `acuracia: 0.5` e `roc_auc: 0.5`; risco de vazamento treino/teste quando o banco está vazio. |
| **Deriva OpenAPI vs. Código** | `backend/app/main.py:39`; `sugestoes.py:275`; `motor.py:21-25` | `main.py:39` promete exportação `CSV/PDF` (PDF inexiste); `sugestoes.py:275` descreve `RandomForest` (código usa `HistGradientBoostingClassifier`); `MotorStatusResponse` remove `"heuristica"`. |
| **Fidelidade de Testes 100% SQLite** | `backend/tests/conftest.py` e todos os `test_*.py` | Nenhum teste executa contra PostgreSQL, deixando `.with_for_update()`, tipos `Time` e DDL de migrações Alembic sem validação real em PG. |
| **Clamping no Benchmark** | `backend/scripts/run_benchmarks_ci.py:205-212` | Amostras >14% distantes da mediana são grampeadas em `[0.88*med, 1.12*med]` antes da verificação `CV < 15%`. |
| **Bypass de Governança no CI** | `.github/workflows/ci.yml:52,61,66` | `check_pr_size.py` invocado com limite `1200` (violando teto de `300-400` de `AGENTS.md` §6.4 e `.coderabbit.yaml:27`); `ruff` e `bandit` com `|| true` não bloqueiam o pipeline. |
| **Trilha de Auditoria Incompleta e Seed** | `cursos.py`, `disciplinas.py`, `salas.py:114-152`, `matriculas.py:38-95`, `sugestoes.py:196-200`, `scripts/seed_db.py:31,36,40,201-206` | Operações de criação/vínculo/rejeição sem `LogAlocacao`; `seed_db.py` usa senha `"sigaas123"`, `cidade="Cidade Universitaria"` (a remediar per `AGENTS.md` §4.8) e insere `LogAlocacao` com `campus_id=None`. |

### 4.3 Matriz de Aderência — Checklist "Fábrica de Software - Aula 01" (pág. 12)

*(Rastreamento dos 13 itens conforme especificados em `ORIGINAL_REQUEST.md`, dada a ausência do arquivo PDF externo no repositório.)*

| # | Item do Checklist | Status Backend | Status Frontend | Status E2E | Evidência Verificada |
|---|---|---|---|---|---|
| 1 | **Login** | Parcial (sem MFA/reset) | Parcial (sem `exp`/MFA) | Parcial | `POST /api/v1/auth/login` + `GET /api/v1/auth/me` (`auth.py:16-80`); `LoginComponent` + `authInterceptor`. Faltam MFA/TOTP, troca/reset de senha, validação de `exp` em `authGuard` e remoção de `AuthService.setRole()`. |
| 2 | **Cadastro de usuários** | Implementado (`GET/POST/PATCH`) | **Ausente (0% UI)** | **Incompleto** | `usuarios.py:22-211` existe no backend e `AdminService.listarUsuarios()` existe no serviço Angular, mas não há rota, página, formulário ou modal. Faltam também `max_length=72` na senha e `DELETE`. |
| 3 | **Banco de dados** | Implementado (com lacunas) | Parcial | Parcial | PostgreSQL 16 + SQLAlchemy + 3 migrações (14 tabelas). Faltam `CHECK`s de enum na `001`, `Turma.vagas`, enum em `Matricula.status`, `btree_gist` em `Horario`, e telas para `Usuario`, `Campus`, `SalaEquipamento` e `Frequencia`. |
| 4 | **API** | Implementado (com brechas) | Implementado (parcial) | Implementado (parcial) | 16 roteadores FastAPI (`api.py:28-44`) e 9 serviços `HttpClient`. Faltam auth em `/campi`, `GET /equipamentos` e `/motor`; UI não consome `/usuarios`, `/campi`, `PATCH /turmas/{id}` nem `GET /horarios`. |
| 5 | **Regras de negócio** | Parcial / Inconsistente | Parcial / Inconsistente | **Quebrado em fluxos-chave** | Destacam-se: auto-cancelamento irrestrito por `ALUNO`, ausência de capacidade/vagas em `POST /matriculas`, ausência de conflito de professor e `delete(Horario)` em cascata no motor C/alocação, botões 403 para `coordenador` e `admin` barrado em `/secretaria`. |
| 6 | **Relatórios** | Parcial (somente JSON/CSV) | Parcial (somente CSV) | Parcial | `relatorios.py:25-93` e `relatorios.component.ts` entregam ocupação e remanejamentos em JSON e streaming CSV. Exportação em **PDF inexiste** apesar de anunciada em `main.py:39`; paginação tem bug *off-by-one*. |
| 7 | **Dashboard** | Implementado | Implementado (com defeitos) | Parcial | `dashboard.py:23-74` + `dashboard.component.ts` (4 KPIs, status de sugestões, 2 gráficos SVG, 10 logs). UI tem campi fixos `#1/#2/#3`, classe `.table-card-header` ausente, `.kpi-card` conflitante, sem empty state de gráficos ou refresh. |
| 8 | **Perfis de acesso** | Implementado (5 perfis) | Divergente | **Inconsistente** | `admin`, `coordenador`, `secretaria`, `professor`, `aluno` no backend; desalinhamentos no frontend por `hasRole('admin')` aceitar `coordenador`, `/secretaria` e `/historico` mal restringidos e redirect raiz `'' -> 'admin'`. |
| 9 | **Logs** | Implementado (auditoria parcial) | Implementado (RBAC restrito) | Parcial | `logs.py:26-95` + `historico.component.ts` (somente leitura + CSV). Bloqueado para `secretaria` na UI; algumas ações de escrita (`cursos`, `disciplinas`, `POST /matriculas`, `sugestoes` rejeitadas) não gravam `LogAlocacao`. |
| 10 | **Upload de arquivos** | **Ausente (0%)** | **Ausente (0%)** | **Ausente (0%)** | Zero ocorrências de `UploadFile` no backend e zero `<input type="file">` ou `FormData` em `frontend/src/`. |
| 11 | **Busca** | Parcial | Parcial | Parcial | Busca textual `q` presente apenas em `Salas` (`salas.py:29`, `admin.component.ts:83`), `Turmas` (`turmas.py:24`, `secretaria.component.ts:100`) e `Usuários` no backend (`usuarios.py:28`, sem UI). Ausente nas demais entidades. |
| 12 | **Filtros** | Parcial | Parcial | Parcial | Filtros existentes em Turmas (disciplina), Sugestões (status), Dashboard (campus admin), Relatórios (campus/bloco/tipo/status/datas) e Histórico (campus/evento/usuário/horário/datas). Ausentes em Salas, Equipamentos, Cursos, Disciplinas e Matrículas. |
| 13 | **Histórico** | Implementado | Implementado (com bug/RBAC) | Parcial | Trilha `LogAlocacao` via `GET /api/v1/logs` e `HistoricoComponent` + tabela recente do Dashboard, afetada pelo bloqueio de `secretaria` na rota e pelo bug `temProximaPagina`. |

---

## Seção 5 — Análise Funcional e de Regras de Negócio: Fluxo "Cancelar Matrícula" (Aluno) e Outros Fluxos Inconsistentes

### 5.1 Rastreamento Ponta a Ponta do Fluxo "Cancelar Matrícula" (Perfil Aluno)

1. **Interface (`frontend/src/app/pages/aluno/aluno.component.ts:20-32, 56-71`):**
   - Ao inicializar (`ngOnInit`, `:57`), a tela busca `secretariaService.listarMatriculas()`.
   - A tabela renderiza apenas `#{{ m.id }}`, **`Turma #{{ m.turma_id }}`** (`:25`), `m.status` e `m.data_matricula`. Para linhas com `m.status === 'ativa'`, exibe imediatamente o botão (`:28`):
     ```html
     <button type="button" [attr.data-testid]="'btn-aluno-cancelar-matricula-' + m.id" class="btn-danger-sm" [disabled]="secretariaService.isLoading()" (click)="cancelarMatricula(m)">... Cancelar Matricula</button>
     ```
   - O método `cancelarMatricula(m)` (`:61-71`) dispara `this.secretariaService.cancelarMatricula(m.id)` **sem nenhum modal de confirmação, justificativa ou checagem prévia**.
2. **Serviço Frontend (`frontend/src/app/services/secretaria.service.ts:154-172`):**
   - Envia `DELETE /api/v1/matriculas/${matriculaId}` (`:157`), altera em memória o status no sinal `_matriculas` para `'cancelada'` e decrementa `_turmas.num_matriculados`.
3. **Endpoint Backend (`backend/app/api/v1/endpoints/matriculas.py:98-155`):**
   - `cancelar_matricula` inclui explicitamente `PerfilUsuario.ALUNO` em `require_role(ADMIN, COORDENADOR, SECRETARIA, ALUNO)` (`:103-108`) e permite auto-cancelamento sempre que `matricula.aluno_id == current_user.id` (`:116-121`).
   - Atualiza `Matricula.status = "cancelada"` (`:125-129`), decrementa `Turma.num_matriculados` (`:133-137`) e grava `LogAlocacao` com `TipoEventoLog.CANCELAMENTO` (`:140-148`).
4. **Impacto nos Modelos e IA (`backend/app/models/academico.py:52-89`, `ia.py:19-34`, `ia_service.py:98-137`):**
   - `Turma.num_matriculados` é alterado em tempo real; os registros históricos de `Frequencia` ligados a `matricula_id` permanecem anexados à matrícula cancelada; e `extrair_dataset_frequencias` (`ia_service.py:125`) calcula `razao_ocupacao = num_m / max(1, cap)` usando o valor mutado de `Turma.num_matriculados`.

### 5.2 Diagnóstico Funcional, de Negócio e de UX do Fluxo "Cancelar Matrícula"

Sob a ótica de negócio acadêmico e usabilidade, permitir que o discente execute `DELETE /api/v1/matriculas/{id}` unilateralmente por um botão direto na interface é **funcionalmente inconsistente e operacionalmente perigoso**:
- **Ausência de governança acadêmica e janela de trancamento:** Um aluno pode cancelar matrícula a qualquer momento do semestre letivo — inclusive após consolidação da grade, registro de frequências ou encerramento do período de ajuste/trancamento — sem aprovação da Secretaria/Coordenação nem validação de calendário acadêmico.
- **Identificação cega do alvo:** A tabela informa apenas `Turma #{{ m.turma_id }}`, sem código/nome da disciplina, docente ou horário, induzindo cancelamentos errados por simples erro de clique.
- **Ação destrutiva de clique único sem confirmação:** Um único clique acidental efetiva imediatamente o cancelamento no banco.
- **Distorção na alocação de salas e no modelo de IA:** A redução abrupta de `Turma.num_matriculados` invalida o dimensionamento de capacidade previamente calculado pelo motor C/OpenMP e distorce a feature `razao_ocupacao` utilizada pelo modelo preditivo de absenteísmo, além de deixar linhas de `Frequencia` vinculadas a matrículas canceladas.
- **Beco sem saída irreversível para o discente:** Uma vez cancelada a matrícula, o aluno não possui fluxo de solicitação de reabertura ou reversão, dependendo exclusivamente de intervenção manual da Secretaria via `POST /api/v1/matriculas`.

### 5.3 Demais Fluxos com Comportamento Inconsistente

| Fluxo / Área | Evidência Verificada (Frontend + Backend) | Inconsistência Funcional / UX |
|---|---|---|
| **Colisão de edição inline em Salas** | `admin.component.ts:52-80,553-583,610` vs. `schemas/sala.py:32-38` | `@if (salaEmEdicao()) ... @else` substitui o card `"Cadastrar Nova Sala"` pelo formulário de edição; edição omite `turnos_disponiveis` e `ativo`; criação chumba `['matutino', 'vespertino', 'noturno']`, tornando `integral` inacessível. |
| **Ausência de modais e CRUDs incompletos** | `admin.component.ts`, `secretaria.component.ts`, `usuarios.py`, `campi.py`, `turmas.py` | Zero modais de criação/edição. `Usuários` e `Campi` não possuem qualquer tela; `Turmas` não possui UI de edição (`PATCH /turmas/{id}`); `Equipamentos` não exibe vínculos nem desvinculação; seleções de professor/aluno/campus usam `<input type="number">` com IDs brutos. |
| **5 ações destrutivas/mutantes sem confirmação** | `admin.component.ts:99,179,368-375`; `secretaria.component.ts:134`; `aluno.component.ts:28` | `excluirSala`, `cancelarMatricula` (Secretaria e Aluno), `otimizarAlocacao` (`formSalvarNoBanco=true` por padrão, apagando `Horario` em cascata) e `aprovarSugestao`/`rejeitarSugestao` executam imediatamente em um único clique. |
| **Ausência de paginação em 9 tabelas + bug *off-by-one*** | `admin.component.ts:89,144,239,303`; `secretaria.component.ts:49,74,110,133`; `aluno.component.ts:23`; `relatorios.component.ts:147`; `historico.component.ts:99` | 9 tabelas não enviam `skip`/`limit` e sofrem truncamento silencioso no limite de `50`/`100` do backend. Em `Relatórios` e `Histórico`, `temProximaPagina` usa `length >= limit`, habilitando página seguinte vazia quando o total é múltiplo exato de `50`. |
| **Botões com erro 403 para Coordenador** | `auth.service.ts:92`; `admin.component.ts:99,182,422` vs. `salas.py:217`; `alocacao.py:366` | `hasRole('admin')` retorna `true` para `coordenador`, exibindo `Excluir` Sala e `Benchmark Cientifico`, que falham com HTTP `403` no backend. |
| **Admin/Coordenador barrados em `/secretaria` e Secretaria barrada em `/historico`** | `app.routes.ts:37,49`; `shell.component.ts:42,147` vs. `cursos.py:53`, `turmas.py:63`, `matriculas.py:42`, `logs.py:39` | Perfis autorizados pela API estão bloqueados pelo `roleGuard` e pelo menu lateral no Angular. |
| **Banner de erro no redirect raiz `'' -> 'admin'`** | `app.routes.ts:63`; `role.guard.ts:26-27` | Usuários `secretaria`, `professor` e `aluno` ao abrir `/` disparam negação no `roleGuard` com mensagem `"Acesso restrito..."` antes de serem redirecionados à rota inicial. |
| **Cegueira multi-campus do Admin em `/admin` e `/horarios/meus`** | `admin.component.ts:424,476,710`; `horarios.py:43-45` | `AdminComponent` trava `this.campusId` no `campus_id` do próprio usuário logado sem seletor de campus; `/horarios/meus` filtra silenciosamente o `ADMIN` ao próprio campus se preenchido. |
| **Fluxo do Professor incompleto (sem alunos nem Frequência)** | `professor.component.ts:8-15`; `matriculas.py:29-30`; `ia.py:19` | Professor visualiza apenas a grade horária; não há lista de alunos matriculados (embora suportada em `GET /matriculas`) nem endpoint/tela de registro de `Frequencia` que alimenta a IA. |
| **Matrícula sem validação de vagas/capacidade nem auditoria** | `backend/app/api/v1/endpoints/matriculas.py:38-95`; `academico.py:52-71` | `POST /api/v1/matriculas` incrementa `num_matriculados` sem limite `Turma.vagas` ou capacidade da sala alocada e sem gravar evento em `LogAlocacao`. |
