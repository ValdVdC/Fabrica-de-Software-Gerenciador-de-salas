# [SPEC-DEVOPS] Entrega Final DevOps — Pipeline CI/CD, Observabilidade Docker e Deploy AWS

- **Sprint / Marco:** Entrega Final de DevOps (Data-Limite: 07/12/2026)
- **Autor / Agente:** Grupo 31 — SIGAAS (Especificação SDD — Milestone M5)
- **Status:** Draft - Aguardando Gate 1
- **Data de Criação:** 2026-11-27
- **ID ClickUp (Épico/Task):** `[Pendente sync]`
- **Disciplina:** Fábrica de Software & Tópicos Avançados em Computação
- **Curso e Turma:** Curso de Bacharelado em Ciência da Computação — Turma 8MB - CC (Semestre 2026/2)
- **Equipe:** Grupo 31 — SIGAAS
- **Repositório:** `https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas`

| Integrante | Matrícula | Papel no Squad | Responsabilidade Principal |
| :--- | :---: | :--- | :--- |
| Ewerton Thyago Tavares da Silva | `01573977` | Scrum Master (Líder) | Facilitação ágil, gestão de entregas, governança de branches e submissão no Teams |
| Wesclei Batista Da Cruz Júnior | `01606772` | Product Owner | Levantamento de requisitos, regras de negócio e validação dos critérios de aceite |
| Osvaldo Vasconcelos de Carvalho | `01614171` | Dev Backend / Sistemas | Arquitetura de API, integração FFI C/OpenMP (`ctypes`), endpoints e migrations |
| Gabriel Porfírio dos Santos | `01591399` | Dev Frontend | Interface SPA Angular 20, componentes, estados reativos e interceptors |
| Flávio Vecch de Brito Farias | `01600988` | DBA & Documentação | Modelagem relacional PostgreSQL, scripts de seed, integridade e documentação técnica |

---

## 1. Contexto, Diagnóstico Atual e Matriz de Rastreabilidade (100% Rubrica DevOps 07/12/2026)

### 1.1 Contexto e Objetivos

Esta especificação define, no padrão Spec-Driven Development (SDD) do repositório, o plano técnico completo e fatiado em Pull Requests incrementais para adequar o sistema **SIGAAS** integralmente aos critérios do Projeto Final de DevOps (entrega em **07/12/2026**), preservando todas as diretrizes arquiteturais invioláveis de `AGENTS.md`:

- Operações **GET** e **POST** usando **JSON** integrando front-end Angular 20, back-end FastAPI e persistência real em banco de dados PostgreSQL 16;
- Arquitetura **Docker** completa para front-end, back-end, banco de dados, agendador cron, **Zabbix via Docker** (Server, Web, Banco dedicado e Agent 2 monitorando contêineres via socket Docker) e **Grafana via Docker** para geração de gráficos e dashboards em tempo real;
- Estratégia de controle de versão no **Git/GitHub** com no mínimo **3 branches** mantendo `main` como branch principal protegida, conciliada com `AGENTS.md` §6 (Trunk-Based + Squash & Merge exclusivo + limite de 400 linhas de código por PR + CodeRabbit) e com **atualização automática em servidor de nuvem AWS** para `staging` e `main`;
- Especificação completa da **Coleção Postman** (e ambientes `local`, `staging`, `prod`) para testes automatizados via Collection Runner e **Newman CLI**, além de documentação embutida da API.

> [!NOTE]
> Esta especificação foi elaborada após auditoria estática integral dos diretórios `docker/`, `.github/`, `backend/`, `frontend/` e `scripts/`. Os procedimentos manuais externos que dependem exclusivamente de ação do usuário na AWS, GitHub, Zabbix, Grafana e Postman estão detalhados no guia complementar `docs/manuais/guia-devops-aws-usuario.md`.

### 1.2 Diagnóstico Técnico Atual (Evidências Verificadas no Repositório)

A auditoria direta da base atual identificou lacunas operacionais, de segurança e de governança que impedem o deploy automatizado em nuvem e o cumprimento integral da rubrica de DevOps:

1. **Sombreamento de Volume do Motor C e Build Local (`docker/compose/docker-compose.local.yml:43`, `docker/backend/Dockerfile:19,23`, `backend/Dockerfile`):**
   - `docker/backend/Dockerfile:19` executa `cd /app/motor_alocacao && make clean && make`, acionando o alvo `all` de `backend/motor_alocacao/Makefile:9` e gerando dentro do contêiner Linux um binário ELF nomeado erroneamente como `motor_alocacao.dll` além de `motor_alocacao.so`.
   - Em execução local, `docker/compose/docker-compose.local.yml:43` monta `../../backend:/app` sobre todo `/app`, sobrescrevendo `/app/motor_alocacao/motor_alocacao.so` compilado na imagem por arquivos do host (em Windows/macOS ou checkout limpo, forçando recompilação em runtime via `backend/app/services/motor_service.py:133-149`).
   - Apesar de `docker/README.md:31` afirmar suporte a hot-reload no modo local, `docker/backend/Dockerfile:23` e `docker/compose/docker-compose.local.yml` não passam `--reload` ao `uvicorn`. Adicionalmente, coexistem dois Dockerfiles redundantes (`docker/backend/Dockerfile` e `backend/Dockerfile`) e o `.dockerignore` raiz (`lines 1-17`) não ignora `.env`, `sigaas_local.db`, `*.so` e `*.dll` quando o contexto de build é a raiz (`context: ../..`).

2. **Ausência de Entrypoint com Migrations Automáticas e Readiness Probe (`docker/backend/Dockerfile:23`, `backend/app/main.py:85-98`):**
   - O backend inicia diretamente com `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` sem executar `alembic upgrade head`. Em volumes PostgreSQL novos na AWS (`staging`/`prod`), as 14 tabelas não são criadas no boot.
   - `GET /health` (`backend/app/main.py:85-98`) executa apenas `SELECT 1` e retorna HTTP `200` mesmo quando o banco está desconectado (`"status": "degraded"`, comportamento explicitamente asserido em `backend/tests/test_health.py:37-46`). Não existe um endpoint `/health/ready` que retorne HTTP `503` quando o banco ou o histórico do Alembic estiverem indisponíveis.

3. **Proxy Reverso Nginx Incompleto (`docker/frontend/nginx.conf:2,20-42`):**
   - O bloco `server` usa `server_name localhost;` (`linha 2`) e encaminha apenas `/api/`, `/docs` e `/openapi.json` para `http://backend:8000`. Não há proxy para `/health`, `/health/ready` e `/redoc`. Em `docker/compose/docker-compose.prod.yml` (onde a porta `8000` não é publicada no host), requisições a `http://<host>/health` caem em `try_files $uri $uri/ /index.html` e retornam HTML da SPA Angular em vez de JSON. Faltam ainda cabeçalhos de segurança HTTP (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).

4. **CORS Hardcoded e Credenciais Padrão sem Bloqueio Fail-Closed (`backend/app/main.py:61-67`, `backend/app/config.py:20-24`, `docker/compose/*.yml`):**
   - `backend/app/main.py:63` fixa `allow_origins=["http://localhost:4200", "http://localhost:8000"]`, bloqueando acessos diretos de origem pública AWS quando fora do mesmo domínio Nginx.
   - `backend/app/config.py:20-24` contém valores padrão inseguros (`POSTGRES_PASSWORD = "changeme_local_only"`, `SECRET_KEY = "super-secret-key-change-in-production-min-32-chars"`) sem variável `ENVIRONMENT` nem validação que impeça inicialização em `staging`/`prod` com segredos fracos ou padrão.
   - `docker/compose/docker-compose.homolog.yml:10,40` usa nomenclatura `homolog` (divergente de `staging`), expõe as portas `5432` e `8000` publicamente e `docker/compose/docker-compose.prod.yml` omite `:?` nas substituições de variáveis obrigatórias e omite blocos `healthcheck` nos serviços `backend`, `frontend` e `cron`.

5. **Cron Job Stubado e Ausência de Propagação de Ambiente (`docker/cron/crontab:4`, `docker/cron/entrypoint.sh:1-9`):**
   - `docker/cron/crontab:4` executa apenas um `echo` simulado a cada 6 horas. `docker/cron/entrypoint.sh` não exporta variáveis de ambiente do contêiner (`DATABASE_URL`, `POSTGRES_*`, `PYTHONPATH`) para o daemon `vixie-cron` e não existe script CLI em `backend/scripts/` para invocar `gerar_sugestoes_remanejamento` (`backend/app/services/ia_service.py:266`).

6. **Lacunas de Governança Git, CI/CD, Monitoramento e Postman:**
   - O repositório possui apenas a branch permanente `main` (sem `develop` e `staging`). `docs/git-governance.md:57-60` cita nomes de checks que divergem dos nomes reais dos jobs em `.github/workflows/ci.yml`. `.coderabbit.yaml:15-16` observa apenas `["main"]`.
   - Em `.github/workflows/ci.yml`: a linha `52` valida `1200` linhas em `check_pr_size.py` (violando o limite normativo de `400` em `AGENTS.md:89`); as linhas `61` e `66` usam `|| true` em `ruff` e `bandit`, anulando os portões de qualidade e segurança; os gatilhos (`linhas 3-17`) restringem-se a `main` com `paths-ignore` incompatível com checks obrigatórios; e o job `docker-smoke-test` (`linhas 158-208`) não executa `alembic upgrade head`, `seed_db.py` nem testes automatizados de API via Newman.
   - Não existem no repositório arquivos de **Zabbix**, **Grafana**, **Postman/Newman** nem workflows de deploy automático na AWS (`.github/workflows/deploy-staging.yml` e `deploy-prod.yml`).

---

### 1.3 Matriz de Rastreabilidade (100% Rubrica DevOps 07/12/2026)

| Requisito da Rubrica DevOps (07/12/2026) | Sub-requisito Técnico | Evidência / Artefato no SIGAAS (Atual ou Alvo) | PR Alvo | Critério de Verificação Objetivo |
| :--- | :--- | :--- | :---: | :--- |
| **1. Aplicação Web com Operações GET e POST em JSON, Front-end, Back-end e Banco de Dados** | Front-end SPA consumindo JSON | Angular 20.2.0 (`frontend/src/app/**`), requisições HTTP relativas `/api/v1/...` via `auth.interceptor.ts` e Nginx `proxy_pass` | Existente + PR 4 | Build `npm run build -- --configuration production` verde; interface carrega em `http://<host>/` |
| | API REST JSON GET/POST/PATCH/DELETE | FastAPI (`backend/app/main.py` + 17 prefixos em `backend/app/api/v1/api.py`: `/auth/login`, `/campi`, `/usuarios`, `/equipamentos`, `/salas`, `/cursos`, `/disciplinas`, `/turmas`, `/matriculas`, `/horarios`, `/motor`, `/alocacao/otimizar`, `/ia/analisar`, `/sugestoes`, `/dashboard/*`, `/relatorios/*`, `/logs`, `/health`, `/health/ready`) | Existente + PR 3 | Testes Pytest >= 85% cobertura e suíte Postman/Newman 100% verde |
| | Persistência e alteração real em BD | PostgreSQL 16 (14 tabelas, migrations `backend/alembic/versions/001..003`), `alembic upgrade head` automático no boot com `pg_advisory_lock` + seed `scripts/seed_db.py` | PR 3, PR 4 | `POST` cria registro, `GET` subsequente retorna registro persistido; `PATCH`/`DELETE` alteram e gravam `LogAlocacao` |
| **2. Arquitetura Docker Completa (App + Serviços + Zabbix + Grafana)** | Contêineres da aplicação | `db` (`postgres:16-alpine`), `backend` (FastAPI + `motor_alocacao.so` OpenMP sem shadowing de volume), `frontend` (`nginx:1.27-alpine` com `/health`, `/health/ready`, `/redoc`), `cron` (`run_ia_job.py` + `flock`) | PR 3, PR 4 | `docker compose config --quiet` sem erros; `docker compose ps` com todos os serviços `(healthy)` |
| | Zabbix instalado via Docker | `docker/compose/docker-compose.monitoring.yml`: `zabbix-db` (`postgres:16-alpine`), `zabbix-server` (`zabbix-server-pgsql:alpine-7.0-latest`), `zabbix-web` (`zabbix-web-nginx-pgsql:alpine-7.0-latest`), `zabbix-agent2` (`zabbix-agent2:alpine-7.0-latest` com `/var/run/docker.sock:ro` e template *Docker by Zabbix agent 2*) | PR 5 | Host `sigaas-ec2-host` ativo no Zabbix Web (`:8081`) coletando CPU, RAM, estado e health de todos os contêineres |
| | Grafana instalado via Docker com gráficos ao vivo | `grafana/grafana-oss:11.3.0` + provisioning declarativo em `docker/grafana/provisioning/` (`alexanderzobnin-zabbix-app` + datasource PostgreSQL read-only `sigaas_ro`) + dashboards JSON de contêineres e métricas SIGAAS/IA | PR 5 | Dashboards carregados automaticamente em `:3000` exibindo séries temporais de contêineres e métricas reais do PostgreSQL |
| | Isolamento de redes e dimensionamento AWS | Redes `frontend_net`, `backend_net` (`internal: true`) e `monitoring_net`; dimensionamento `t3.large` (8 GB RAM / 40 GB `gp3`) em Ubuntu 24.04 LTS | PR 4, PR 5 | Portas `5432`, `8000` e `10051` não expostas ao host em `staging`/`prod` |
| **3. Estratégia Git/GitHub (>= 3 Branches com `main` Principal) + Auto-Deploy AWS** | Mínimo 3 branches permanentes com `main` principal | `develop` (Integração/QA) -> `staging` (Pré-produção AWS) -> `main` (Principal/Produção AWS) + branches efêmeras (`feat/*`, `fix/*`, `docs/*`, `ci/*`, `chore/*`, `perf/*`, `test/*`) | PR 1 | Branches `develop`, `staging` e `main` protegidas no GitHub; Squash & Merge exclusivo; `.coderabbit.yaml` nas 3 bases |
| | Correção de portões de CI | `ci.yml`: limite `400` LOC (`check_pr_size.py`), remoção de `|| true` em `ruff` e `bandit`, triggers em `[main, staging, develop]`, resolução de `paths-ignore`, migrations + seed + Newman no smoke test | PR 2, PR 6 | Pipeline `Continuous Integration (CI)` verde em PRs para `develop`, `staging` e `main` |
| | Atualização automática na AWS (`staging` e `main`) | `.github/workflows/deploy-staging.yml` (`workflow_run` após CI verde em `staging` -> Environment `staging`) e `.github/workflows/deploy-prod.yml` (`workflow_run` após CI verde em `main` -> Environment `production` com Required Reviewers) | PR 7 | Merge em `staging` ou `main` atualiza automaticamente os contêineres na EC2 AWS e valida `/health/ready` |
| **4. Coleção Postman + Documentação + Guia do Usuário** | Coleção Postman para testes e docs | `docs/postman/sigaas-devops.postman_collection.json` (16 pastas, scripts `pm.test`, `run_suffix` idempotente, `salvar_no_banco: false`) + 3 environments (`local`, `staging`, `prod`) + job `test-newman-api` | PR 6 | `newman run ... --reporters cli,junit` executa todas as requisições com zero falhas e gera relatório JUnit |
| | Guia passo a passo para ações externas | `docs/manuais/guia-devops-aws-usuario.md` cobrindo EC2, SG, SSH, GitHub Branches/Environments/Secrets, `.env`, Zabbix/Grafana e Postman | Entregue em M5 + sync PR 7 | Operador humano consegue provisionar do zero e validar todos os requisitos até 07/12/2026 |

---

## 2. Histórias de Usuário e Critérios de Aceite (Gherkin)

### História 1: Operações JSON (GET/POST/PATCH/DELETE) e Persistência Real no PostgreSQL
> **Como** avaliador de DevOps e usuário da aplicação SIGAAS,  
> **Quero** executar operações HTTP GET e POST em JSON pelo front-end Angular e pela API FastAPI com persistência real no PostgreSQL 16 e exposição de probes `/health` e `/health/ready` via Nginx,  
> **Para que** toda alteração cadastral ou operacional seja validada ponta a ponta em banco de dados relacional em ambiente conteinerizado.

#### Critérios de Aceite (Gherkin)
```gherkin
Cenário: Persistência ponta a ponta de sala via JSON (POST seguido de GET)
  Dado que o usuário está autenticado como Admin ou Coordenador com token JWT válido
  Quando envia uma requisição POST para "/api/v1/salas" com payload JSON válido no campus do usuário
  Então a API retorna HTTP 201 com o objeto JSON da sala criada e seu "id" gerado pelo PostgreSQL
  E registra um evento "criacao" na tabela "log_alocacao"
  E uma requisição GET subsequente para "/api/v1/salas/{id}" retorna HTTP 200 com os mesmos atributos persistidos

Cenário: Verificação de prontidão do banco e migrations via proxy reverso Nginx
  Dado que os contêineres "frontend", "backend" e "db" estão em execução
  Quando um cliente ou monitor consulta "GET http://<host>/health/ready" através do Nginx
  Então o Nginx encaminha a chamada para "http://backend:8000/health/ready" sem servir HTML da SPA
  E o backend retorna HTTP 200 com JSON contendo database "connected" e alembic_head aplicado
  Mas se o PostgreSQL estiver inacessível ou pendente de migration, o endpoint "/health/ready" retorna HTTP 503

Cenário: Compatibilidade preservada do endpoint de liveness "/health"
  Dado que o backend está em execução e a suíte "backend/tests/test_health.py" é executada
  Quando o banco de dados estiver temporariamente desconectado durante consulta a "GET /health"
  Então a API continua retornando HTTP 200 com "status": "degraded" e "database": "disconnected"
```

### História 2: Arquitetura Docker Endurecida, Entrypoint Automático e Cron IA Real
> **Como** engenheiro de plataforma e operador do SIGAAS,  
> **Quero** que os stacks Docker (`local`, `staging`, `prod`) inicializem migrations Alembic automaticamente com lock concorrente, não sombreiem o binário C/OpenMP `motor_alocacao.so`, rejeitem segredos padrão em `staging`/`prod` e executem o job real de IA via cron,  
> **Para que** o ambiente suba de forma reproduzível, segura e livre de falhas manuais na nuvem AWS.

#### Critérios de Aceite (Gherkin)
```gherkin
Cenário: Bloqueio fail-closed de segredos inseguros em staging e produção
  Dado que a variável de ambiente "ENVIRONMENT" está definida como "staging" ou "prod"
  Quando a aplicação FastAPI inicia com "SECRET_KEY" padrão ou menor que 32 caracteres ou "POSTGRES_PASSWORD" padrão
  Então o validador de "Settings" em "backend/app/config.py" levanta "ValueError" e aborta o boot imediatamente
  E o Docker Compose falha na validação se variáveis obrigatórias com ":?" não estiverem preenchidas

Cenário: Inicialização automática de schema e proteção do motor C no contêiner backend
  Dado um volume PostgreSQL vazio em "staging" ou "prod"
  Quando o contêiner "backend" é iniciado via "docker/backend/entrypoint.sh"
  Então o entrypoint adquire "pg_advisory_lock", executa "alembic upgrade head" e só então inicia o Uvicorn
  E a biblioteca "/opt/sigaas/motor_alocacao.so" permanece acessível mesmo com bind mounts locais de código Python

Cenário: Execução agendada do job preditivo de IA sem mutação direta de horários
  Dado o contêiner "cron" em execução com acesso às variáveis de conexão do PostgreSQL
  Quando o agendamento em "docker/cron/crontab" dispara "backend/scripts/run_ia_job.py" protegido por "flock"
  Então o script executa "gerar_sugestoes_remanejamento" por campus ativo
  E grava previsões em "previsao_falta" e sugestões "pendente" em "sugestao_remanejamento"
  E nenhuma linha da tabela "horario" tem seu "sala_id" alterado automaticamente
```

### História 3: Observabilidade com Zabbix via Docker e Grafana Provisionado
> **Como** administrador de infraestrutura do SIGAAS,  
> **Quero** monitorar todos os contêineres Docker e métricas de aplicação/IA por meio do Zabbix Server + Zabbix Agent 2 (Docker) e visualizar gráficos em tempo real no Grafana pré-provisionado,  
> **Para que** gargalos de CPU/RAM, quedas de contêineres e evolução de sugestões de IA sejam acompanhados continuamente.

#### Critérios de Aceite (Gherkin)
```gherkin
Cenário: Descoberta automática de contêineres pelo Zabbix Agent 2 via socket Docker
  Dado que o stack de monitoramento está ativo com "zabbix-db", "zabbix-server", "zabbix-web" e "zabbix-agent2"
  Quando o "zabbix-agent2" acessa "/var/run/docker.sock" em modo somente leitura com grupo "DOCKER_GID"
  Então o template "Docker by Zabbix agent 2" descobre os contêineres "db", "backend", "frontend", "cron", "zabbix-*" e "grafana"
  E coleta métricas de CPU, memória RSS, estado de execução, reinicializações e healthcheck

Cenário: Provisionamento declarativo do Grafana com datasources Zabbix e PostgreSQL read-only
  Dado que o contêiner "grafana" sobe com as pastas montadas de "docker/grafana/provisioning/"
  Quando o Grafana conclui a inicialização com o plugin "alexanderzobnin-zabbix-app" habilitado
  Então os datasources "Zabbix" e "SIGAAS PostgreSQL" (usuário read-only "sigaas_ro") ficam disponíveis sem configuração manual de JSON
  E os dashboards "sigaas-containers-infra" e "sigaas-app-ia-metrics" exibem gráficos ao vivo de infraestrutura e de aplicação
```

### História 4: Estratégia Git com 3 Branches Permanentes e Auto-Deploy na AWS
> **Como** Scrum Master e equipe do Grupo 31,  
> **Quero** operar um fluxo Git com 3 branches permanentes (`develop`, `staging`, `main`), checks rigorosos de CI (400 LOC, Ruff, Bandit, Pytest >= 85%, Motor C, Angular, Newman) e pipelines de deploy automático para AWS Staging e Produção,  
> **Para que** toda entrega respeite a governança do `AGENTS.md` e atualize o servidor na nuvem de forma controlada e auditável.

#### Critérios de Aceite (Gherkin)
```gherkin
Cenário: Bloqueio de push direto e promoção por fatias respeitando o limite de 400 LOC
  Dado que as branches "develop", "staging" e "main" estão protegidas no GitHub
  Quando um desenvolvedor conclui uma funcionalidade em "feat/<nome>" com no máximo 400 linhas de código de produção
  Então o PR para "develop" passa pelo Debate Adversarial, checks obrigatórios do CI e CodeRabbit e entra por Squash & Merge
  E cada fatia validada em "develop" é promovida por PR individual para "staging" e depois para "main", mantendo o diff <= 400 LOC em todos os portões

Cenário: Deploy automático em AWS Staging e AWS Produção após CI verde
  Dado que um PR foi integrado em "staging" ou "main" e o workflow "Continuous Integration (CI)" concluiu com sucesso
  Quando o evento "workflow_run" dispara "deploy-staging.yml" ou "deploy-prod.yml"
  Então o workflow conecta via SSH na instância EC2 usando as credenciais do GitHub Environment correspondente ("staging" ou "production")
  E atualiza o código, grava o arquivo ".env" com permissão 600, reconstrói os contêineres e valida HTTP 200 em "/health/ready"
  E em "production" o deploy aguarda aprovação humana configurada em Required Reviewers do Environment
```

### História 5: Coleção Postman e Execução Headless via Newman no CI
> **Como** engenheiro de QA e desenvolvedor back-end,  
> **Quero** manter uma coleção Postman versionada cobrindo todos os domínios da API SIGAAS com scripts de asserção `pm.test`, documentação e execução via Newman CLI,  
> **Para que** contratos JSON, persistência no banco e regras RBAC sejam verificados automaticamente a cada pipeline e manualmente no Postman Desktop.

#### Critérios de Aceite (Gherkin)
```gherkin
Cenário: Execução completa e idempotente da coleção Postman via Newman CLI
  Dado um ambiente SIGAAS em execução com migrations aplicadas e seed inicial carregado
  Quando o comando "newman run docs/postman/sigaas-devops.postman_collection.json -e docs/postman/sigaas-local.postman_environment.json" é executado
  Então o script de pré-requisição gera "run_suffix" único evitando colisões 409 Conflict em execuções repetidas
  E o login captura "access_token" e "campus_id" automaticamente para as pastas subsequentes
  E a cadeia de matrículas valida incremento e decremento atômico de "num_matriculados" no PostgreSQL
  E a chamada "POST /api/v1/alocacao/otimizar" utiliza "salvar_no_banco: false" preservando os dados de frequência e sugestões
  E todos os "pm.test" passam com zero falhas e geram relatório JUnit XML
```

---

## 3. Arquitetura e Contratos Técnicos

### 3.1 Arquitetura Docker, Redes Isoladas e Dimensionamento AWS

#### A. Redes Docker (`driver: bridge`)

| Rede | Flag `internal` | Serviços Conectados | Justificativa de Isolamento |
| :--- | :---: | :--- | :--- |
| `frontend_net` | `false` | `frontend`, `backend` | Único ponto de entrada HTTP/HTTPS público via Nginx; impede acesso direto de `frontend` ao PostgreSQL ou ao cron. |
| `backend_net` | `true` | `db`, `backend`, `cron`, `grafana` (apenas usuário `sigaas_ro`) | Isola o banco principal SIGAAS e o job batch de IA contra acesso externo; somente `backend` roteia entre `frontend_net` e `backend_net`. |
| `monitoring_net` | `false` | `zabbix-db`, `zabbix-server`, `zabbix-web`, `zabbix-agent2`, `grafana`, `frontend`, `backend` | Separa o banco do Zabbix (`zabbix-db`) do banco da aplicação (`db`) e permite sondagens HTTP internas a `frontend:80` e `backend:8000`. |

#### B. Matriz Completa de Serviços Docker

| Serviço | Imagem / Dockerfile | Ambientes | Redes | Portas no Host | Healthcheck | Política de Restart | Volumes / Montagens |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `db` | `postgres:16-alpine` | `local`, `staging`, `prod` | `backend_net` | `local`: `127.0.0.1:5432:5432`; `staging`/`prod`: **nenhuma** | `pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}` (`10s/5s/5`) | `unless-stopped` (`prod`: `always`) | `db_data_<env>:/var/lib/postgresql/data` + `docker/postgres/init-readonly.sql:/docker-entrypoint-initdb.d/01-readonly.sql:ro` |
| `backend` | `docker/backend/Dockerfile` (`appuser` não-root em `staging`/`prod`) | `local`, `staging`, `prod` | `frontend_net`, `backend_net`, `monitoring_net` | `local`: `8000:8000`; `staging`/`prod`: **nenhuma** | `curl -fsS http://127.0.0.1:8000/health/ready \|\| exit 1` (`15s/5s/5`, `start_period: 30s`) | `unless-stopped` (`prod`: `always`) | `local` apenas: `./backend/app:/app/app`, `./backend/alembic:/app/alembic`, `./backend/tests:/app/tests`, `./scripts:/scripts:ro` |
| `frontend` | `docker/frontend/Dockerfile` (`node:22-alpine` -> `nginx:1.27-alpine`) | `local`, `staging`, `prod` | `frontend_net`, `monitoring_net` | `local`: `4200:80`; `staging`: `8080:80` (se co-hospedado) ou `80:80`; `prod`: `80:80`, `443:443` | `wget -qO- http://127.0.0.1:80/health >/dev/null \|\| exit 1` (`15s/5s/3`) | `unless-stopped` (`prod`: `always`) | Opcional TLS `/etc/letsencrypt:ro` em `prod` |
| `cron` | `docker/cron/Dockerfile` | `local`, `staging`, `prod` | `backend_net` | **nenhuma** | `pgrep -x cron >/dev/null \|\| exit 1` (`30s/5s/3`) | `unless-stopped` (`prod`: `always`) | `cron_logs_<env>:/var/log` |
| `zabbix-db` | `postgres:16-alpine` | `monitoring` | `monitoring_net` | **nenhuma** | `pg_isready -U ${ZABBIX_DB_USER} -d ${ZABBIX_DB_NAME}` (`10s/5s/5`) | `unless-stopped` / `always` | `zabbix_db_data:/var/lib/postgresql/data` |
| `zabbix-server` | `zabbix/zabbix-server-pgsql:alpine-7.0-latest` | `monitoring` | `monitoring_net` | **nenhuma** (`10051/TCP` interno) | `zabbix_server -R config_cache_reload >/dev/null 2>&1 \|\| exit 1` (`30s/10s/5`, `start_period: 45s`) | `unless-stopped` / `always` | `zabbix_server_data:/var/lib/zabbix` |
| `zabbix-web` | `zabbix/zabbix-web-nginx-pgsql:alpine-7.0-latest` | `monitoring` | `monitoring_net` | `8081:8080` (restrito por Security Group) | `wget -qO- http://127.0.0.1:8080/ >/dev/null \|\| exit 1` (`30s/5s/5`, `start_period: 30s`) | `unless-stopped` / `always` | Stateless (PHP/Nginx) |
| `zabbix-agent2` | `zabbix/zabbix-agent2:alpine-7.0-latest` | `monitoring` | `monitoring_net` | **nenhuma** (`10050/TCP` interno) | `zabbix_agent2 -t agent.ping \|\| exit 1` (`30s/5s/3`) | `unless-stopped` / `always` | `/var/run/docker.sock:/var/run/docker.sock:ro`, `/:/hostfs:ro`, `/proc:/host/proc:ro`, `/sys:/host/sys:ro`; `group_add: ["${DOCKER_GID}"]` |
| `grafana` | `grafana/grafana-oss:11.3.0` | `monitoring` | `monitoring_net`, `backend_net` | `3000:3000` (restrito por Security Group) | `wget -qO- http://127.0.0.1:3000/api/health >/dev/null \|\| exit 1` (`15s/5s/5`) | `unless-stopped` / `always` | `grafana_data:/var/lib/grafana`; `./docker/grafana/provisioning:/etc/grafana/provisioning:ro`; `./docker/grafana/dashboards:/var/lib/grafana/dashboards:ro` |

#### C. Correções Estruturais nos Dockerfiles, Entrypoints e Nginx

1. **Consolidação do Backend (`docker/backend/Dockerfile` + `docker/backend/entrypoint.sh`):**
   - Remover ou tornar obsoleto `backend/Dockerfile` mantendo `docker/backend/Dockerfile` como única fonte oficial (`context: ../..`).
   - Compilar explicitamente `make motor_alocacao.so benchmark` (evitando gerar `motor_alocacao.dll` ELF no Linux) e instalar a biblioteca compilada em `/opt/sigaas/motor_alocacao.so`, garantindo runtime com `libgomp1` e `curl`.
   - Em `MotorAlocacaoService._carregar_biblioteca()` (`backend/app/services/motor_service.py:151`), suportar a variável `MOTOR_ALOCACAO_LIB_PATH` (ex.: `/opt/sigaas/motor_alocacao.so`) antes de recorrer ao fallback local em `backend/motor_alocacao/`.
   - Criar `docker/backend/entrypoint.sh`:
     - Aguardar PostgreSQL responder;
     - Se `RUN_MIGRATIONS_ON_STARTUP=true`, executar `alembic upgrade head` protegido por `SELECT pg_advisory_lock(734201)` em `backend/alembic/env.py` (evitando condição de corrida em subidas concorrentes);
     - Iniciar `exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-1}"` (no Compose local, sobrescrever `command:` com `--reload`).
2. **Proxy Reverso (`docker/frontend/nginx.conf`):**
   - Alterar `server_name localhost;` para `server_name _;`.
   - Adicionar `location = /health` -> `proxy_pass http://backend:8000/health;`, `location = /health/ready` -> `proxy_pass http://backend:8000/health/ready;` e `location /redoc` -> `proxy_pass http://backend:8000/redoc;`.
   - Adicionar cabeçalhos de segurança (`X-Content-Type-Options "nosniff"`, `X-Frame-Options "SAMEORIGIN"`, `Referrer-Policy "strict-origin-when-cross-origin"`).
3. **Cron IA (`backend/scripts/run_ia_job.py`, `docker/cron/entrypoint.sh`, `docker/cron/crontab`):**
   - `docker/cron/entrypoint.sh` grava apenas as variáveis necessárias (`POSTGRES_*`, `DATABASE_URL`, `PYTHONPATH`, `TZ`) em `/app/.cron.env` (`chmod 600`) e inicia `exec cron -f`.
   - `docker/cron/crontab` executa a cada 6 horas: `. /app/.cron.env && flock -n /tmp/sigaas_ia.lock /usr/local/bin/python /app/scripts/run_ia_job.py >> /proc/1/fd/1 2>&1`.
   - `backend/scripts/run_ia_job.py` percorre os campi ativos e chama `gerar_sugestoes_remanejamento(db, campus_id=c.id)` (`backend/app/services/ia_service.py:266`), respeitando estritamente a regra *Human-in-the-Loop* (nunca modifica `horario.sala_id`).
4. **Provisionamento Zabbix & Grafana (`docker/postgres/init-readonly.sql`, `docker/grafana/`):**
   - `init-readonly.sql` cria a role `sigaas_ro` com `GRANT SELECT` apenas nas tabelas operacionais não sensíveis (`campus`, `sala`, `turma`, `horario`, `previsao_falta`, `sugestao_remanejamento`, `log_alocacao`), excluindo explicitamente `usuario.senha_hash`.
   - `docker/grafana/provisioning/plugins/zabbix.yaml` habilita `alexanderzobnin-zabbix-app`.
   - `docker/grafana/provisioning/datasources/datasources.yaml` registra `Zabbix` (`http://zabbix-web:8080/api_jsonrpc.php`) e `SIGAAS PostgreSQL` (`db:5432`, usuário `sigaas_ro`).
   - `docker/grafana/dashboards/` contém `sigaas-containers-infra.json` (CPU, RAM, uptime e health dos contêineres via Zabbix) e `sigaas-app-ia-metrics.json` (ocupação por campus, distribuição de `SugestaoRemanejamento` e probabilidades de `PrevisaoFalta` via PostgreSQL).

#### D. Dimensionamento de EC2 na AWS (Ubuntu 24.04 LTS `x86_64`)

A pilha completa com os 9 contêineres consome aproximadamente **4,2 GB a 5,6 GB de RAM** em regime contínuo (SO + Docker ~0,6 GB; App SIGAAS ~1,7–2,6 GB; Zabbix + Grafana ~1,9–2,4 GB).

| Topologia de Implantação | Instância Recomendada | Recursos | Disco EBS | Observações Operacionais |
| :--- | :--- | :--- | :--- | :--- |
| **EC2 Única Completa (App + Zabbix + Grafana)** | `t3.large` (ou `t3a.large`) | 2 vCPU, 8 GB RAM | 40 GB `gp3` (mín. 30 GB) | Folga segura para todos os 9 contêineres + build Docker + 2 GB de swap preventivo. |
| **EC2 Única para Benchmark OpenMP (4 Threads)** | `t3.xlarge` (ou `c6a.xlarge`) | 4 vCPU, 16 GB (ou 8 GB) RAM | 40–50 GB `gp3` | Necessária para demonstrar speedup paralelo real com `OMP_NUM_THREADS=4` na nuvem. |
| **EC2 Separada apenas para Staging (sem Zabbix/Grafana)** | `t3.small` ou `t3.medium` | 2 vCPU, 2 GB ou 4 GB RAM | 30 GB `gp3` | `t3.medium` suporta `docker compose build` local na instância; `t3.small` exige swap 2 GB. |

> [!CAUTION]
> Instâncias `t2.micro` ou `t3.micro` (1 GB de RAM) sofrem encerramento por falta de memória (`OOMKill`) ao executar simultaneamente PostgreSQL, FastAPI/scikit-learn, Zabbix Server e Grafana. Recomenda-se `t3.large` para a entrega completa.

---

### 3.2 Contratos de Configuração e Novos Endpoints (`backend/app/config.py` e `main.py`)

#### A. Variáveis de Ambiente (`backend/app/config.py` e `.env.example`)

| Variável | Tipo / Padrão Local | Validação em `staging` / `prod` | Finalidade |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `Literal["local", "staging", "prod"] = "local"` | Obrigatória explícita | Controla validação estrita de segredos no boot. |
| `CORS_ORIGINS` | `str = "http://localhost:4200,http://localhost:8000"` | Parseada para `list[str]` (proibido `"*"` com `allow_credentials=True`) | Origens permitidas no `CORSMiddleware` (`main.py:63`). |
| `SECRET_KEY` | String >= 32 chars | Rejeita valores padrão e strings `< 32` chars (`ValueError`) | Assinatura JWT HS256 (`core/security.py`). |
| `POSTGRES_PASSWORD` | String >= 16 chars | Rejeita `changeme_local_only`, `changeme_homolog_only` e `< 16` chars | Autenticação no PostgreSQL principal. |
| `POSTGRES_RO_PASSWORD` | String >= 16 chars | Obrigatória quando perfil `monitoring` ativo | Senha da role read-only `sigaas_ro` usada pelo Grafana. |
| `MOTOR_ALOCACAO_LIB_PATH` | `Optional[str] = "/opt/sigaas/motor_alocacao.so"` | Fallback para `backend/motor_alocacao/motor_alocacao.{so,dll}` | Evita sombreamento por bind mount no container. |
| `RUN_MIGRATIONS_ON_STARTUP` | `bool = True` | Executado com `pg_advisory_lock(734201)` | Garante schema atualizado antes de aceitar tráfego. |
| `ZABBIX_DB_PASSWORD` | String forte | Obrigatória (`:?`) no compose de monitoramento | Senha do banco exclusivo `zabbix-db`. |
| `ZABBIX_API_USER` / `ZABBIX_API_PASSWORD` | Usuário/senha API Zabbix | Obrigatória (`:?`) no compose de monitoramento | Leitura de métricas pelo datasource Grafana. |
| `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` | Admin Grafana | Obrigatória (`:?`) no compose de monitoramento | Acesso administrativo e bloqueio de `GF_USERS_ALLOW_SIGN_UP=false`. |

#### B. Endpoints de Saúde (`backend/app/main.py`)
- `GET /health` (mantido sem quebra de contrato): executa `SELECT 1` e retorna HTTP `200` com `{"status": "ok"|"degraded", "service": ..., "version": ..., "database": "connected"|"disconnected"}`.
- `GET /health/ready` (novo): verifica `SELECT 1` e consulta `alembic_version` comparando com o `head` esperado via `ScriptDirectory`; retorna HTTP `200` (`{"status": "ready", "database": "connected", "alembic_head": "<rev>"}`) quando pronto, ou HTTP `503 Service Unavailable` caso o banco esteja fora ou haja migrations pendentes.

#### C. Exige Migration Alembic?
- `[Não]` — As 14 tabelas e 3 migrations (`001` a `003`) existentes permanecem inalteradas. Apenas a role read-only `sigaas_ro` é criada via script de inicialização SQL (`docker/postgres/init-readonly.sql`) com `GRANT SELECT` explícito, sem alteração de schema de domínio.

---

### 3.3 Estratégia Git/GitHub (3 Branches Permanentes) e Pipelines CI/CD

#### A. Modelo de Branches Conciliado com `AGENTS.md` §6

```text
feat/*, fix/*, docs/*, ci/*, chore/*, perf/*, test/*
   |  (PR: Squash & Merge, <= 400 LOC, TDD + Debate Adversarial + CI + CodeRabbit)
   v
develop  (Permanente, Protegida -- Integracao Continua e QA)
   |  (PR: Squash & Merge por fatia <= 400 LOC, CI + Newman + CodeRabbit)
   v
staging  (Permanente, Protegida -- Pre-Producao; CI verde dispara deploy-staging.yml -> AWS Staging)
   |  (PR: Squash & Merge por fatia <= 400 LOC + Gate 2 Humano, CI + Newman + CodeRabbit)
   v
main     (Permanente, Principal, Protegida -- Producao; CI verde dispara deploy-prod.yml -> AWS Prod; Tags v* -> release.yml)
```

Regras operacionais de conciliação com `AGENTS.md`:
1. **Manutenção de `main` como branch principal:** `main` continua sendo a branch padrão/principal do repositório, única fonte das tags de release (`v*.*.*` em `.github/workflows/release.yml`) e destino exclusivo da produção AWS.
2. **Três branches permanentes protegidas:** `develop`, `staging` (convenção minúscula exata) e `main`. Nenhuma aceita push direto ou force push; todas aceitam exclusivamente **Squash and Merge** (`allow_merge_commit=false`, `allow_rebase_merge=false`) com exclusão automática de branches efêmeras.
3. **Promoção Linear por Fatia (`<= 400` LOC):** Como `scripts/check_pr_size.py:57` compara `git diff --numstat origin/${{ github.base_ref }}...HEAD`, cada funcionalidade aprovada em `develop` é promovida em seu respectivo PR fatiado (`<= 400` LOC de produção) para `staging` e, após validação em AWS Staging, para `main`. Assim, o teto de 400 LOC é cumprido em **todos** os portões sem exceções ou enfraquecimento do validador.
4. **Exceção de Hotfix:** Correções críticas em produção (`fix/hotfix-*`) partem de `main`, entram via PR em `main` (`<= 400` LOC + Gate 2) e são retroportadas imediatamente via PR (`main -> staging -> develop`).
5. **Sincronização de Governança:** Atualizar `AGENTS.md` §6 (incluindo `develop`, `staging` e `ci/<nome>`), `docs/git-governance.md` (alinhando nomes de checks aos nomes reais de `.github/workflows/ci.yml`), `.coderabbit.yaml` (`base_branches: ["main", "staging", "develop"]`), `.github/pull_request_template.md`, `.agent/rules/squad-roles.md` e `.agent/workflows/sdd-cycle.md`.

#### B. Correções em `.github/workflows/ci.yml`

| Trecho Atual em `ci.yml` | Problema Identificado | Correção Especificada |
| :--- | :--- | :--- |
| Linhas `3-17` (`branches: [main]`, `paths-ignore`) | Ignora `staging` e `develop`; `paths-ignore` trava PRs apenas de `docs/` quando há Required Status Checks | Expandir `branches: [main, staging, develop]`; substituir `paths-ignore` global por filtro de caminhos (`dorny/paths-filter`) dentro dos jobs pesados para que o job de governança sempre conclua e sinalize status verde |
| Linha `52` (`... 1200`) | Permite PRs de até 1200 LOC, violando `AGENTS.md:89` | Alterar para `python scripts/check_pr_size.py origin/${{ github.base_ref }} 400` |
| Linha `61` (`ruff check ... \|\| true`) | Mascara falhas de lint | Remover `\|\| true` (`ruff check backend/ scripts/`) |
| Linha `66` (`bandit ... \|\| true`) | Mascara vulnerabilidades médias/altas | Remover `\|\| true` (`bandit -r backend/app -ll -ii`) |
| Linhas `158-208` (`docker-smoke-test`) | Não aplica migrations/seed nem testa API autenticada | Garantir boot com `entrypoint.sh` (`alembic upgrade head`), validar `/health/ready`, executar `docker compose exec -T backend python /scripts/seed_db.py` e rodar o job `test-newman-api` |
| Ausência de Newman | Nenhum teste automatizado de coleção Postman no CI | Novo job `test-newman-api` (`needs: [test-backend, test-motor-c, test-frontend]`) executando `npx --yes newman run ... --reporters cli,junit`, publicando `reports/newman-junit.xml` como artefato |

#### C. Novos Workflows de Deploy Automático AWS (`.github/workflows/deploy-staging.yml` e `deploy-prod.yml`)

| Aspecto | `deploy-staging.yml` | `deploy-prod.yml` |
| :--- | :--- | :--- |
| **Gatilho Primário** | `workflow_run` de `"Continuous Integration (CI)"` (`types: [completed]`, `branches: [staging]`, `conclusion == 'success'`) + `workflow_dispatch` | `workflow_run` de `"Continuous Integration (CI)"` (`types: [completed]`, `branches: [main]`, `conclusion == 'success'`) + `workflow_dispatch` |
| **GitHub Environment** | `staging` | `production` (com **Required Reviewers** habilitado para Gate 2 humano) |
| **Secrets do Environment** | `AWS_HOST`, `AWS_USER`, `AWS_SSH_KEY`, `AWS_PORT`, `DEPLOY_PATH` (ex.: `/opt/sigaas/staging`), `ENV_FILE_STAGING` | `AWS_HOST`, `AWS_USER`, `AWS_SSH_KEY`, `AWS_PORT`, `DEPLOY_PATH` (ex.: `/opt/sigaas/prod`), `ENV_FILE_PROD` |
| **Execução Remota via SSH** | `git fetch origin staging && git reset --hard origin/staging`; grava `.env` (`chmod 600`); `docker compose -p sigaas-staging -f docker/compose/docker-compose.staging.yml up -d --build --remove-orphans`; `seed_db.py` idempotente; valida `curl -fsS http://127.0.0.1:${STAGING_PORT}/health/ready` | `git fetch origin main && git reset --hard origin/main`; grava `.env` (`chmod 600`); `docker compose -p sigaas-prod -f docker/compose/docker-compose.prod.yml -f docker/compose/docker-compose.monitoring.yml up -d --build --remove-orphans`; valida `curl -fsS http://127.0.0.1/health/ready` |

---

### 3.4 Especificação da Coleção Postman e Ambientes

- **Coleção (Schema v2.1.0):** `docs/postman/sigaas-devops.postman_collection.json`
- **Environments:**
  - `docs/postman/sigaas-local.postman_environment.json` (`base_url = http://localhost:8000`)
  - `docs/postman/sigaas-staging.postman_environment.json` (`base_url = http://<EC2_STAGING_HOST>:8080` ou domínio staging)
  - `docs/postman/sigaas-prod.postman_environment.json` (`base_url = https://<DOMINIO_PROD>` ou `http://<EC2_PROD_HOST>`)
- **Variáveis Comuns:** `base_url`, `api_prefix` (`/api/v1`), `admin_email` (`admin@sigaas.edu`), `admin_password`, `coord_email` (`coord.cc@sigaas.edu`), `coord_password`, `aluno_email` (`aluno@sigaas.edu`), `aluno_password`, além das variáveis dinâmicas de execução (`run_suffix`, `access_token`, `aluno_token`, `campus_id`, `created_campus_id`, `created_user_id`, `created_equip_id`, `created_sala_id`, `created_curso_id`, `created_disciplina_id`, `created_turma_id`, `created_matricula_id`, `created_sugestao_id`).
- **Mecanismo de Idempotência:** Script *Pre-request* no nível da coleção inicializa `run_suffix` (ex.: últimos 6 dígitos de `Date.now()`) caso vazio, evitando erros `409 Conflict` em execuções consecutivas.

| Pasta da Coleção | Requisições Principais (Método e Rota) | Asserções `pm.test` e Encadeamento |
| :--- | :--- | :--- |
| `01 - Health & Root` | `GET /health`, `GET /health/ready`, `GET {{api_prefix}}` | Status `200`, `json.database === "connected"`, `responseTime < 2000`, chaves `docs` e `redoc` |
| `02 - Auth & RBAC` | `POST /auth/login` (Admin), `POST /auth/login` (Aluno), `POST /auth/login` (senha inválida), `GET /auth/me` (válido e sem token) | Captura `access_token`, `campus_id` e `aluno_token`; valida `200`, `401` (negativos) e `Content-Type: application/json` |
| `03 - Campi` | `GET /campi`, `POST /campi`, `GET /campi/{{created_campus_id}}` | `200`/`201`; confirma persistência no PostgreSQL via `GET` pelo `id` criado |
| `04 - Usuários` | `POST /usuarios`, `GET /usuarios/{{created_user_id}}`, `PATCH /usuarios/{{created_user_id}}`, `GET /usuarios` (com `aluno_token`) | `201`/`200`; valida atualização persistida e teste negativo RBAC `403 Forbidden` para `aluno` |
| `05 - Equipamentos` | `POST /equipamentos`, `GET /equipamentos` | `201`/`200`; confirma presença de `created_equip_id` na listagem |
| `06 - Salas (CRUD Completo)` | `POST /salas`, `GET /salas/{{created_sala_id}}`, `POST /salas/{{created_sala_id}}/equipamentos`, `PATCH /salas/{{created_sala_id}}`, `DELETE /salas/{{created_sala_id}}`, `GET /salas/{{created_sala_id}}` | `201` -> `200` -> `201` -> `200` (`capacidade === 55`) -> `204` -> `404` (comprovando exclusão persistida) |
| `07 - Cursos` | `POST /cursos`, `GET /cursos/{{created_curso_id}}` | `201`/`200`; normalização `codigo` maiúsculo (`QA{{run_suffix}}`) |
| `08 - Disciplinas` | `POST /disciplinas`, `GET /disciplinas/{{created_disciplina_id}}` | `201`/`200`; vínculo com `created_curso_id` |
| `09 - Turmas` | `POST /turmas`, `GET /turmas/{{created_turma_id}}`, `PATCH /turmas/{{created_turma_id}}` | `201`/`200`; `num_matriculados === 0` e alteração persistida de `turno_preferido` |
| `10 - Matrículas (Contador Atômico)` | `POST /matriculas`, `GET /turmas/{{created_turma_id}}`, `DELETE /matriculas/{{created_matricula_id}}`, `GET /turmas/{{created_turma_id}}` | Comprova incremento atômico (`num_matriculados === 1`) após `POST` e decremento atômico (`num_matriculados === 0`) após `DELETE` |
| `11 - Horários` | `GET /horarios?campus_id={{campus_id}}`, `GET /horarios/meus` | `200`; estrutura de lista JSON válida |
| `12 - Motor C & Alocação` | `GET /motor/status`, `POST /motor/teste-integracao`, `POST /alocacao/otimizar` (`salvar_no_banco: false`), `POST /alocacao/benchmark` (`cenario: "pequeno"`) | `200`; `openmp_ativo === true`, `resultado === 42`, `sucesso === true` sem apagar frequências/sugestões via CASCADE |
| `13 - Sugestões & IA Preditiva` | `POST /ia/analisar`, `GET /sugestoes?status=pendente` | `200`; valida estrutura de análise e listagem por status |
| `14 - Dashboard` | `GET /dashboard/resumo`, `GET /dashboard/ocupacao` | `200`; `por_dia_semana.length === 7` e `por_turno.length === 4` |
| `15 - Relatórios` | `GET /relatorios/ocupacao-salas?formato=json`, `GET /relatorios/remanejamentos?formato=json` | `200`; arrays JSON válidos |
| `16 - Logs` | `GET /logs?limit=10` | `200`; presença dos eventos de auditoria gerados na execução |

Comando oficial headless via Newman CLI:
```bash
newman run docs/postman/sigaas-devops.postman_collection.json \
  -e docs/postman/sigaas-local.postman_environment.json \
  --reporters cli,junit \
  --reporter-junit-export reports/newman-junit.xml \
  --timeout-request 10000 \
  --bail
```

---

## 4. Fatiamento em PRs Incrementais (<= 300-400 LOC)

Respeitando estritamente a regra de diff de `AGENTS.md` §6 (`<= 300 a 400` linhas de código de produção modificado por PR) e o playbook de inversão de dependências (`.agent/skills/diff-slicer/SKILL.md`), a entrega é particionada em **7 Pull Requests incrementais**, compiláveis e testáveis isoladamente:

| Ordem | Branch | Escopo | Arquivos Alvo | LOC Prod. Est. | Commit Conventional Commits | Dependência | Gate 2 / Debate |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| **PR 1** | `docs/devops-git-governance` | Alinhar governança para 3 branches (`develop`, `staging`, `main`), `.coderabbit.yaml`, template de PR, `docs/git-governance.md`, `AGENTS.md`, `squad-roles.md` e `sdd-cycle.md` | `AGENTS.md`, `docs/git-governance.md`, `.coderabbit.yaml`, `.github/pull_request_template.md`, `.agent/rules/squad-roles.md`, `.agent/workflows/sdd-cycle.md` | `0` (`docs/`, `.agent/`, `.github/` isentos) | `docs(governance): definir fluxo com tres branches e protecoes` | Gate 1 | Debate Adversarial |
| **PR 2** | `fix/ci-ruff-bandit-baseline` | Sanear preventivamente apontamentos de `ruff` e `bandit` no código Python existente antes de tornar os gates bloqueantes no CI | `backend/app/**/*.py`, `scripts/*.py` | `<= 250` | `fix(ci): sanear apontamentos de ruff e bandit` | PR 1 | Debate Adversarial |
| **PR 3** | `feat/devops-backend-config-health` | Endurecer `config.py` (`ENVIRONMENT`, `CORS_ORIGINS`, validação fail-closed de segredos), CORS dinâmico e `/health/ready` em `main.py`, `MOTOR_ALOCACAO_LIB_PATH` em `motor_service.py`, `pg_advisory_lock` em `alembic/env.py`, criar `backend/scripts/run_ia_job.py` e testes unitários | `backend/app/config.py`, `backend/app/main.py`, `backend/app/services/motor_service.py`, `backend/alembic/env.py`, `backend/scripts/run_ia_job.py`, `backend/tests/test_config_health.py` | `<= 280` | `feat(backend): adicionar health ready cors dinamico e job ia` | PR 2 | Debate Adversarial |
| **PR 4** | `feat/devops-docker-stacks` | Consolidar `docker/backend/Dockerfile` (`appuser`, `make motor_alocacao.so benchmark`, `/opt/sigaas/motor_alocacao.so`), `docker/backend/entrypoint.sh`, `nginx.conf` (`/health`, `/health/ready`, `/redoc`, segurança), `docker/cron/{entrypoint.sh,crontab}`, corrigir `docker-compose.local.yml`, criar `docker-compose.staging.yml`, endurecer `docker-compose.prod.yml`, `.dockerignore` e `.env.example` | `docker/backend/*`, `docker/frontend/nginx.conf`, `docker/cron/*`, `docker/compose/*.yml`, `.dockerignore`, `.env.example` (obsoletar `backend/Dockerfile`) | `0` (`.yml`, `Dockerfile`, `.sh`, `.conf` fora de `CODE_EXTENSIONS`) | `feat(docker): endurecer stacks local staging prod e entrypoints` | PR 3 | Debate Adversarial + **Gate 2** |
| **PR 5** | `feat/devops-zabbix-grafana` | Adicionar `docker/compose/docker-compose.monitoring.yml` (`zabbix-db`, `zabbix-server`, `zabbix-web`, `zabbix-agent2`, `grafana`), `docker/postgres/init-readonly.sql` (`sigaas_ro`), provisioning Grafana e dashboards JSON | `docker/compose/docker-compose.monitoring.yml`, `docker/postgres/init-readonly.sql`, `docker/grafana/provisioning/**`, `docker/grafana/dashboards/*.json` | `<= 30` (`.sql`; YAML/JSON isentos) | `feat(observability): integrar zabbix e grafana via docker` | PR 4 | Debate Adversarial + **Gate 2** |
| **PR 6** | `test/devops-postman-ci-gates` | Criar coleção Postman (16 pastas) + 3 environments (`local`, `staging`, `prod`) e endurecer `.github/workflows/ci.yml` (`1200 -> 400`, remover `\|\| true`, triggers `[main, staging, develop]`, filtro de caminhos, migrations + seed no smoke test e job `test-newman-api`) | `docs/postman/*.json`, `.github/workflows/ci.yml` | `0` (`*.json` e `.github/` isentos) | `ci(tests): ativar gates 400 loc ruff bandit e suite newman` | PR 3, PR 4 | Debate Adversarial |
| **PR 7** | `ci/aws-auto-deploy-pipelines` | Criar `.github/workflows/deploy-staging.yml` e `.github/workflows/deploy-prod.yml` com GitHub Environments (`staging`, `production`), SSH deploy, validação `/health/ready` e sincronização de `docs/handoff-guide.md` | `.github/workflows/deploy-staging.yml`, `.github/workflows/deploy-prod.yml`, `docs/handoff-guide.md`, `docs/manuais/guia-devops-aws-usuario.md` | `0` (`.github/` e `docs/` isentos) | `ci(deploy): configurar auto-deploy aws para staging e main` | PR 5, PR 6 | Debate Adversarial + **Gate 2** |

> [!NOTE]
> Cada PR será integrado primeiro em `develop`, depois promovido individualmente via PR (`develop -> staging` e `staging -> main`) com Squash & Merge exclusivo, mantendo o diff de produção `<= 400` LOC em todas as etapas.

---

## 5. Plano de Testes e Verificação (TDD, Docker Smoke, Newman, Zabbix/Grafana e Dry-Run)

### 5.1 Suíte Unitária e de Integração TDD (Fase RED -> GREEN -> REFACTOR)
1. **`backend/tests/test_config_health.py` (criar antes do PR 3):**
   - `test_settings_rejeita_secret_padrao_em_prod`: valida `ValidationError`/`ValueError` quando `ENVIRONMENT="prod"` e `SECRET_KEY` tem valor padrão ou `< 32` caracteres.
   - `test_settings_rejeita_postgres_password_padrao_em_staging`: valida rejeição de `"changeme_local_only"` quando `ENVIRONMENT="staging"`.
   - `test_settings_parseia_cors_origins_csv`: valida parsing de `CORS_ORIGINS="http://localhost:4200,https://sigaas.example.com"`.
   - `test_health_ready_retorna_200_quando_alembic_no_head`: valida HTTP `200` com DB conectado e revisão atualizada.
   - `test_health_ready_retorna_503_quando_db_indisponivel`: valida HTTP `503` (enquanto `backend/tests/test_health.py` continua garantindo `GET /health` -> `200` `"degraded"`).
   - `test_run_ia_job_executa_por_campus_sem_alterar_horario`: garante que `backend/scripts/run_ia_job.py` gera sugestões pendentes sem alterar `horario.sala_id`.
2. **Critérios de Qualidade Estática e Cobertura:**
   - `ruff check backend/ scripts/` (exit code `0`, sem `|| true`).
   - `bandit -r backend/app -ll -ii` (exit code `0`, sem `|| true`).
   - `pytest tests -v --cov=app --cov-config=.coveragerc --cov-fail-under=85`.
   - `python scripts/check_pr_size.py origin/<base> 400` em todos os PRs.

### 5.2 Validação Docker Compose, Runtime, Cron e Motor C
1. **Validação sintática dos manifests:**
   ```bash
   docker compose -f docker/compose/docker-compose.local.yml config --quiet
   docker compose --env-file .env.staging -f docker/compose/docker-compose.staging.yml config --quiet
   docker compose --env-file .env.prod -f docker/compose/docker-compose.prod.yml -f docker/compose/docker-compose.monitoring.yml config --quiet
   ```
2. **Verificação em volume limpo (`staging`/`prod`):**
   - Subir com `docker compose ... up -d --build` e confirmar ausência de portas `5432`, `8000` e `10051` publicadas no host.
   - Confirmar que `docker compose exec -T backend alembic current` já exibe o `(head)` sem comando manual.
   - Confirmar `curl -fsS http://127.0.0.1/health` e `curl -fsS http://127.0.0.1/health/ready` retornando JSON via Nginx.
   - Confirmar presença de `/opt/sigaas/motor_alocacao.so` e execução de `GET /api/v1/motor/status` (`openmp_ativo: true`).
   - Executar manualmente `docker compose exec -T cron python /app/scripts/run_ia_job.py` e validar exit code `0` e geração de `SugestaoRemanejamento` `pendente`.

### 5.3 Validação Newman (Headless API E2E), Zabbix/Grafana e Dry-Run de Workflows
1. **Newman CLI:** executar `newman run docs/postman/sigaas-devops.postman_collection.json -e docs/postman/sigaas-local.postman_environment.json --reporters cli,junit --reporter-junit-export reports/newman-junit.xml --bail` esperando `0` falhas nas 16 pastas.
2. **Zabbix + Grafana:**
   - No Zabbix Web (`http://<IP>:8081`), verificar host `sigaas-ec2-host` com disponibilidade verde e itens populados em *Monitoring -> Latest data* pelo template *Docker by Zabbix agent 2*.
   - No Grafana (`http://<IP>:3000`), testar ambos os datasources (`Zabbix` e `SIGAAS PostgreSQL`) com status *Data source is working* e abrir os dois dashboards sem painéis em erro.
3. **Dry-Run dos Workflows GitHub Actions:** validar sintaxe YAML com `actionlint` (ou revisão estrita no PR), confirmar disparo de `deploy-staging.yml` via `workflow_dispatch` / merge em `staging`, e validar pausa de aprovação humana do Environment `production` antes de executar `deploy-prod.yml`.

---

## 6. Decomposição de Tarefas para o ClickUp e Portões (Gate 1 / Debate Adversarial / Gate 2)

### 6.1 Portões Obrigatórios do Fluxo SDD (`AGENTS.md` §5 e §7)
1. **Gate 1 (Pré-Execução):** Aprovação formal desta especificação (`docs/specs/spec-devops-entrega-final.md`) e do guia do usuário (`docs/manuais/guia-devops-aws-usuario.md`) antes de criar código de infraestrutura ou workflows. Após aprovação, sincronizar subtarefas no ClickUp via:
   ```bash
   python scripts/clickup_sync.py sync-spec docs/specs/spec-devops-entrega-final.md
   ```
2. **Debate Adversarial Multi-Agente Pré-PR:** Obrigatório antes de abrir cada um dos PRs 1 a 7, com zero vetos e ciclo de re-review em caso de apontamento crítico, seguido de inspeção de comentários do CodeRabbit (`gh pr view <PR> --comments`).
3. **Gate 2 (Pré-Merge / Pós-Debate):** Aprovação humana explícita requerida especialmente nos **PRs 4, 5 e 7** (alteração de Dockerfiles/Compose de produção, inclusão de serviços de monitoramento com socket Docker e pipelines de auto-deploy AWS) e na promoção `staging -> main`.

### 6.2 Checklist de Tarefas para Sincronização ClickUp

- [ ] [Gate 1] Revisar e aprovar `spec-devops-entrega-final.md` e `guia-devops-aws-usuario.md`
- [ ] [Infra/Usuário] Provisionar instância EC2 AWS, Security Groups, chaves SSH, branches `develop`/`staging` e GitHub Environments/Secrets conforme guia do usuário
- [ ] [PR 1 - Governança] Atualizar `AGENTS.md`, `docs/git-governance.md`, `.coderabbit.yaml`, template de PR e regras de squad para 3 branches permanentes (`develop`, `staging`, `main`)
- [ ] [PR 2 - Qualidade] Sanear apontamentos baseline de `ruff` e `bandit` em `backend/app/` e `scripts/`
- [ ] [PR 3 - TDD/Backend] Criar testes unitários e implementar `ENVIRONMENT`, `CORS_ORIGINS`, fail-closed secrets, `/health/ready`, `MOTOR_ALOCACAO_LIB_PATH`, `pg_advisory_lock` e `run_ia_job.py`
- [ ] [PR 4 - Docker] Consolidar `docker/backend/Dockerfile`, `entrypoint.sh`, `nginx.conf` (`/health`, `/health/ready`), `cron`, corrigir `docker-compose.local.yml`, criar `docker-compose.staging.yml` e endurecer `docker-compose.prod.yml`
- [ ] [PR 5 - Observabilidade] Implementar `docker-compose.monitoring.yml` (Zabbix Server/Web/DB/Agent2 + Grafana), role `sigaas_ro`, provisioning e dashboards JSON
- [ ] [PR 6 - Postman & CI] Criar `sigaas-devops.postman_collection.json` + environments, corrigir `ci.yml` (`400` LOC, remover `|| true`, triggers 3 branches) e adicionar job `test-newman-api`
- [ ] [PR 7 - AWS Deploy] Criar `.github/workflows/deploy-staging.yml` e `deploy-prod.yml`, validar auto-deploy na AWS para `staging` e `main` e atualizar `docs/handoff-guide.md`
- [ ] [Evidências] Coletar provas finais da rubrica de 07/12/2026 (Postman/Newman, Docker `ps`, Zabbix Latest Data, Grafana dashboards, deploy AWS)
