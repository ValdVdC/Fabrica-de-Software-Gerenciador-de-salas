# Relatório Técnico: Sprint 10

## Sistema Integrado de Gestão Acadêmica e Alocação de Salas com IA (SIGAAS)

**Disciplina:** Fábrica de Software & Tópicos Avançados em Computação  
**Curso:** Curso de Bacharelado em Ciência da Computação  
**Turma:** 8MB - CC  
**Equipe:** Grupo 31 — SIGAAS  
**Entrega:** Sprint 10 - Release Candidate (`v1.0.0-rc.1`), Documentação OpenAPI, Schema Final e README Técnico  
**Data-Limite de Entrega:** 14 de Novembro de 2026 às 23:59  
**Repositório Oficial no GitHub:** [https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas](https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas)

---

### 1. Identificação da Equipe e Distribuição de Papéis

| Integrante | Matrícula | Papel no Squad | Responsabilidade Técnica Principal |
| :--- | :---: | :--- | :--- |
| **Ewerton Thyago Tavares da Silva** | 01573977 | Scrum Master (Líder) | Facilitação ágil, gestão de entregas, governança de branches e submissão no Teams |
| **Wesclei Batista Da Cruz Júnior** | 01606772 | Product Owner | Levantamento de requisitos, regras de negócio e validação dos critérios de aceite |
| **Osvaldo Vasconcelos de Carvalho** | 01614171 | Dev Backend / Sistemas | Arquitetura de API, integração FFI C/OpenMP (`ctypes`), endpoints e migrations |
| **Gabriel Porfírio dos Santos** | 01591399 | Dev Frontend | Interface SPA Angular 20, componentes, estados reativos e interceptors |
| **Flávio Vecch de Brito Farias** | 01600988 | DBA & Documentação | Modelagem relacional PostgreSQL, scripts de seed, integridade e documentação técnica |

---

# PARTE 10 - SPRINT 10: RELEASE CANDIDATE (`v1.0.0-rc.1`)

## 10.1 Contexto e Objetivos

A Sprint 10 consolida o marco de **Release Candidate (`v1.0.0-rc.1`)** do Sistema Integrado de Gestão Acadêmica e Alocação de Salas com IA (SIGAAS). Após a homologação funcional, estatística e de testes ponta a ponta realizada na Sprint 09, esta etapa teve como foco a estabilização final da plataforma para entrega e avaliação externa, abrangendo:

1. Publicação da documentação interativa completa da API REST (OpenAPI 3.1, Swagger UI e ReDoc) e versionamento oficial `1.0.0-rc.1`;
2. Validação do schema definitivo do PostgreSQL com 14 tabelas, paridade estrutural 100% entre models SQLAlchemy e histórico Alembic, e criação dos índices compostos de desempenho;
3. Polimento visual final da interface SPA Angular 20 com identificação discreta da versão `v1.0.0-rc.1` e conformidade de contraste WCAG AA;
4. Atualização integral do `README.md` técnico na raiz do repositório e consolidação cumulativa dos relatórios técnicos das Sprints 01 a 10 (`docs/entregas/Grupo31_SIGAAS_Sprints01-10.pdf`).

A especificação normativa desta entrega é a `SPEC-010`, registrada em `docs/specs/sprint10-release-candidate.md`. Todos os Pull Requests de código da Sprint 10 encontram-se concluídos e integrados na branch `main` (commit `0a03b07`):

1. **PR 1 (OpenAPI / Swagger — PR #104, commit `62b9bfb`):** versionamento `1.0.0-rc.1`, metadados de 17 tags de domínio + `Health` e `Root`, ReDoc (`/api/v1/redoc`), Swagger UI (`/api/v1/docs`), docstrings nos endpoints críticos e suíte `backend/tests/test_openapi_docs.py`.
2. **PR 2 (Schema Final PostgreSQL — PR #105, commit `95338f8`):** migration reversível `003_release_candidate_indexes.py` com 6 índices compostos, paridade 100% ORM vs. Alembic e validação de idempotência de `scripts/seed_db.py`.
3. **PR 3 (Polimento Final Angular — PR #106, commit `0a03b07`):** exibição da tag `v1.0.0-rc.1` no rodapé do `ShellComponent`, ajustes de contraste WCAG AA, foco/hover e responsividade em `styles.scss`, além da suíte `shell.component.spec.ts`.
4. **PR 4 (README e Pacote Acadêmico — branch `docs/sprint10-readme-relatorio`):** atualização integral do `README.md`, elaboração deste relatório (`relatorio-sprint10.md`), consolidação cumulativa (`relatorio-consolidado-sprints-01-a-10.md`) e compilação do PDF oficial ABNT (`docs/entregas/Grupo31_SIGAAS_Sprints01-10.pdf`).

---

## 10.2 API REST, Documentação Interativa OpenAPI/Swagger e Versão RC

O PR #104 (commit `62b9bfb`, Task ClickUp `#1dft1faj11r`) estruturou a camada de documentação interativa e contratos da API para o Release Candidate:

- **Versionamento Oficial (`backend/app/config.py`):** atualização de `Settings.VERSION` para `"1.0.0-rc.1"`, refletida automaticamente no endpoint `/health` e no documento OpenAPI (`/api/v1/openapi.json`).
- **Metadados OpenAPI e ReDoc (`backend/app/main.py`):** configuração de `API_DESCRIPTION`, `OPENAPI_TAGS` cobrindo integralmente os 17 módulos de domínio (`Autenticacao`, `Campi`, `Usuarios`, `Cursos`, `Disciplinas`, `Salas`, `Equipamentos`, `Turmas`, `Matriculas`, `Horarios`, `Motor`, `Alocacao`, `Sugestoes`, `IA Preditiva`, `Logs`, `Dashboard` e `Relatorios`), além de `Health` e `Root`. Foram expostos `docs_url="/api/v1/docs"` (Swagger UI), `redoc_url="/api/v1/redoc"` (ReDoc) e redirecionamentos de conveniência em `/docs` e `/redoc`.
- **Documentação de Endpoints Críticos:** enriquecimento de `summary`, `description` e mapa de `responses` HTTP (`400`, `401`, `403`, `404`, `409`, `500`, `503`) nos roteadores `auth.py`, `alocacao.py`, `sugestoes.py`, `motor.py` e `dashboard.py`.
- **Testes TDD (`backend/tests/test_openapi_docs.py`):** 5 testes automatizados validando versão `1.0.0-rc.1`, presença das 19 tags esperadas sem *drift*, HTTP `200 OK` para `/api/v1/openapi.json`, `/api/v1/docs` e `/api/v1/redoc`, esquema `BearerAuth` / OAuth2 e cobertura descritiva das rotas protegidas.

---

## 10.3 Banco de Dados PostgreSQL, Schema Final e Índices Compostos

O PR #105 (commit `95338f8`, Task ClickUp `#1dft1faj11t`) consolidou o schema definitivo do PostgreSQL (14 tabelas) e garantiu paridade estrita entre os modelos ORM SQLAlchemy 2.0 e o histórico de migrations Alembic:

- **Índices Compostos de Desempenho (`backend/app/models/alocacao.py` e `backend/app/models/ia.py`):**
  - Tabela `horario`: `ix_horario_turma_dia_hora` (`turma_id`, `dia_semana`, `hora_inicio`), `ix_horario_sala_dia_hora` (`sala_id`, `dia_semana`, `hora_inicio`, `hora_fim`) e `ix_horario_campus_dia_hora` (`campus_id`, `dia_semana`, `hora_inicio`);
  - Tabela `frequencia`: `ix_frequencia_horario_data` (`horario_id`, `data`);
  - Tabela `previsao_falta`: `ix_previsao_falta_horario_data` (`horario_id`, `data_prevista`);
  - Tabela `sugestao_remanejamento`: `ix_sugestao_remanejamento_status_criado_em` (`status`, `criado_em`).
- **Migration Reversível (`backend/alembic/versions/003_release_candidate_indexes.py`):** implementa `upgrade()` e `downgrade()` completos sobre a revisão `002_add_campus_id_to_log_alocacao`.
- **Testes TDD de Paridade e Idempotência (`backend/tests/test_migrations.py`):**
  - `test_schema_parity_alembic_models`: valida paridade 100% entre `Base.metadata` e `alembic upgrade head` (14 tabelas, colunas, nullability e índices), além de testar o ciclo reversível `downgrade -1` / `upgrade head`;
  - `test_seed_database_idempotency`: valida que execuções sucessivas de `scripts/seed_db.py` não duplicam campi, usuários, salas, disciplinas, turmas, matrículas ou horários.

---

## 10.4 Interface Final Angular e Polimento Release Candidate

O PR #106 (commit `0a03b07`, Task ClickUp `#1dft1faj11u`) realizou o polimento visual final da SPA Angular 20 sem alteração de regras de negócio:

- **Identificação de Versão (`frontend/src/app/layout/shell/shell.component.ts`):** inclusão da barra de rodapé discreta exibindo `SIGAAS v1.0.0-rc.1` no layout principal autenticado (`ShellComponent`), sem uso de emojis.
- **Contraste WCAG AA, Foco e Responsividade (`frontend/src/styles.scss`, `login.component.ts`, `grade-horaria.component.ts`):** refinamento de tokens visuais, contraste de texto/fundo, estados de `:focus-visible` e `:hover`, e ajustes responsivos para visualização da grade horária.
- **Testes e Build de Produção (`frontend/src/app/layout/shell/shell.component.spec.ts`):** adição de testes unitários para o `ShellComponent` (incluindo verificação da exibição de `v1.0.0-rc.1`), totalizando **165/165 testes aprovados** no Karma/ChromeHeadless e build de produção limpo em `479.25 kB` sem avisos de orçamento de bundle.

---

## 10.5 README Técnico Completo e Pacote Acadêmico Cumulativo

O PR 4 (branch `docs/sprint10-readme-relatorio`, Task ClickUp `#1dft1faj11w`) consolida a documentação final do projeto para avaliadores e usuários externos:

- **`README.md`:** reestruturado integralmente para o marco `v1.0.0-rc.1`, documentando arquitetura em camadas, links diretos para `/api/v1/docs`, `/api/v1/redoc` e `/api/v1/openapi.json`, guia completo via `Makefile` (`make setup`, `make sigaas`, `make ps`, `make reset`) e desenvolvimento híbrido, tabela oficial de credenciais extraída de `scripts/seed_db.py`, resumo científico do motor C/OpenMP (speedup até `3,74x` em `N=10`), métricas ML com limiar de `40%`, resultados de testes/CI e identificação oficial do Grupo 31.
- **`docs/entregas/relatorio-sprint10.md` e `docs/entregas/relatorio-consolidado-sprints-01-a-10.md`:** registro técnico completo da Sprint 10 preservando integralmente o histórico das Sprints 01 a 09.
- **`docs/entregas/Grupo31_SIGAAS_Sprints01-10.pdf`:** compilação oficial em formato ABNT via ReportLab, em estrita conformidade com a Regra 8 do `AGENTS.md` e `.agent/rules/academic-deliverables.md`.

---

## 10.6 Evidências de Testes Automatizados e CI na Branch `main`

No estado consolidado da branch `main` (commit `0a03b07`, GitHub Actions Run `#43639008716`, duração total `4m30s`), todos os **5 checks obrigatórios de Integração Contínua** foram aprovados com 100% de sucesso:

| Check de CI (GitHub Actions — Run `#43639008716`) | Status | Duração | Evidência Consolidada |
| :--- | :---: | :---: | :--- |
| **1. Code Quality & Policy Enforcement** | `SUCCESS` | `17s` | Linter `ruff` limpo e auditoria `check_pr_size.py` dentro do limite (`<= 400` linhas). |
| **2. Backend Tests & Coverage (Pytest)** | `SUCCESS` | `2m10s` | **276 testes aprovados**, cobertura global de **93,65%** (meta mínima `>= 85%`), incluindo `test_openapi_docs.py` e `test_migrations.py`. |
| **3. Frontend Tests & Build (Angular)** | `SUCCESS` | `43s` | **165/165 specs Karma/ChromeHeadless SUCCESS** e `ng build` de produção limpo (`479.25 kB`). |
| **4. Allocation Engine (C & OpenMP)** | `SUCCESS` | `12s` | Compilação `gcc -O3 -fopenmp -shared` sem warnings e validação FFI `ctypes` aprovada. |
| **5. Docker Environment Smoke Test** | `SUCCESS` | `1m55s` | Subida dos containers `db` e `app`, migrations Alembic aplicadas (`003_release_candidate_indexes`) e healthcheck HTTP 200 validado. |

Resumo consolidado das suítes na `main` (`v1.0.0-rc.1`):

```text
Backend (Pytest + Alembic):
276 passed | Total coverage: 93.65% | Schema parity: 14 tabelas + 6 indices compostos RC

Frontend (Angular 20 + Karma):
Chrome Headless: Executed 165 of 165 SUCCESS | Production build: 479.25 kB (0 warnings)
```

---

## 10.7 Governança Ágil e Estado dos Pull Requests

| PR | Branch | Commit na `main` | Escopo | ID ClickUp | Situação |
| :---: | :--- | :---: | :--- | :---: | :--- |
| **#104** | `feat/rc-openapi-docs` | `62b9bfb` | Versão `1.0.0-rc.1`, OpenAPI 17 tags, Swagger/ReDoc e `test_openapi_docs.py` | `#1dft1faj11r` | **Mesclado na `main`** |
| **#105** | `feat/rc-schema-final` | `95338f8` | Migration `003_release_candidate_indexes.py`, 6 índices e paridade ORM/Alembic | `#1dft1faj11t` | **Mesclado na `main`** |
| **#106** | `feat/rc-frontend-polish` | `0a03b07` | Tag `v1.0.0-rc.1` no `ShellComponent`, contraste WCAG AA e `shell.component.spec.ts` | `#1dft1faj11u` | **Mesclado na `main`** |
| **PR 4** | `docs/sprint10-readme-relatorio` | Em revisão | `README.md` completo, `relatorio-sprint10.md`, consolidado Sprints 01-10 e PDF oficial | `#1dft1faj11w` | **Aberto para Gate 2** |

---

## 10.8 Conclusão e Próximos Passos

A Sprint 10 conclui a preparação do **Release Candidate (`v1.0.0-rc.1`)** do SIGAAS com estabilidade técnica e rastreabilidade documental completas na branch `main` (commit `0a03b07`):

- A API REST dispõe de documentação interativa OpenAPI 3.1 / Swagger UI / ReDoc cobrindo os 17 módulos de domínio, autenticação JWT e códigos de erro padronizados.
- O banco de dados PostgreSQL encontra-se consolidado com 14 tabelas, migration reversível `003_release_candidate_indexes.py` e paridade 100% validada por testes automatizados.
- A interface Angular 20 exibe a versão `v1.0.0-rc.1` com 165/165 testes aprovados, acompanhada de 276 testes no backend (93,65% de cobertura) e 5/5 checks de CI aprovados.

Próximos passos para o encerramento formal da Sprint 10:

1. Submeter o PR 4 (`docs/sprint10-readme-relatorio`) à aprovação humana no Gate 2.
2. Realizar o *Squash and Merge* do PR 4 na branch `main`.
3. Publicar a tag de release `v1.0.0-rc.1` a partir da `main` consolidada.
