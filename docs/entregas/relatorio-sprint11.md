# Relatório Técnico: Sprint 11

## Sistema Integrado de Gestão Acadêmica e Alocação de Salas com IA (SIGAAS)

**Disciplina:** Fábrica de Software & Tópicos Avançados em Computação  
**Curso:** Curso de Bacharelado em Ciência da Computação  
**Turma:** 8MB - CC  
**Equipe:** Grupo 31 — SIGAAS  
**Entrega:** Sprint 11 - Preparação para Entrega (Manuais Técnico e do Usuário, Revisão de Código e Saneamento do Repositório)  
**Data-Limite de Entrega:** 21 de Novembro de 2026 às 23:59  
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

# PARTE 11 - SPRINT 11: PREPARAÇÃO PARA ENTREGA (MANUAIS, REVISÃO DE CÓDIGO E SANEAMENTO)

## 11.1 Contexto, Objetivos e Atendimento às Devolutivas Anteriores

A Sprint 11 (data oficial de entrega: **21/11/2026**) tem como objetivo preparar integralmente o **SIGAAS (`v1.0.0-rc.1`)** para a entrega final e a banca examinadora, consolidando a documentação técnica e de usuário, revisando todo o código-fonte de produção e saneando o repositório GitHub.

A especificação normativa desta entrega é a `SPEC-011`, registrada em `docs/specs/sprint11-preparacao-entrega.md`, que além dos entregáveis previstos no cronograma da disciplina, atende diretamente às devolutivas docentes das Sprints 07, 08 e 09:

1. **Rastreabilidade de Versão e Tag Formal:** compilação do PDF cumulativo exclusivamente a partir da branch `main` consolidada (commit `067b84f`), seguida da publicação da tag oficial `v0.11.0-sprint11` após o merge deste PR;
2. **Fluxo Ponta a Ponta Unificado:** demonstração explícita nos manuais e neste relatório de como cadastros, motor C/OpenMP, IA preditiva, remanejamento *Human-in-the-Loop*, dashboard, relatórios CSV e auditoria operam como um único sistema integrado;
3. **Registro Factual de Dificuldades e Soluções:** documentação transparente das dificuldades técnicas e documentais reais enfrentadas na Sprint 11 e das remediações aplicadas.

Todos os Pull Requests técnicos e de manuais da Sprint 11 encontram-se mesclados na branch `main` (commit `067b84f`):

1. **PR 1 (Revisão de Código e Saneamento — PR #108, commit `fd1461a`):** hardening de erros em `alocacao.py` e `motor.py`, observabilidade em `ia_service.py` e `motor_service.py`, remoção de imports não utilizados no frontend, remoção do diretório legado `ia_previsao/`, alinhamento de `.env.example` e `.gitignore` e inclusão da `SPEC-011`.
2. **PR 2 (Manual Técnico — PR #109, commit `067b84f`):** publicação de `docs/manuais/manual-tecnico.md` (378 linhas) e revisão final da documentação arquitetural (`docs/projeto-gestao-salas-escalas.md`).
3. **PR 3 (Manual do Usuário — PR #110, commit `c5d76ce`):** publicação de `docs/manuais/manual-usuario.md` (244 linhas) orientado aos 5 perfis RBAC, 7 fluxos ponta a ponta e 16 capturas de tela validadas.
4. **PR 4 (Relatório Consolidado e PDF Oficial — branch `docs/sprint11-relatorio-pdf`):** elaboração deste relatório (`docs/entregas/relatorio-sprint11.md`), consolidação cumulativa das Sprints 01 a 11 (`docs/entregas/relatorio-consolidado-sprints-01-a-11.md`) e geração do PDF oficial ABNT (`docs/entregas/Grupo31_SIGAAS_Sprints01-11.pdf`).

---

## 11.2 Visão Ponta a Ponta Unificada do Sistema Integrado

O SIGAAS opera como um ecossistema coeso em 3 camadas — **Angular 20 SPA**, **FastAPI (Python 3.12)** e **PostgreSQL 16 + Motor C11/OpenMP + IA `scikit-learn`** — ancorado no isolamento multi-tenant por `campus_id` e no controle de acesso baseado em papéis (RBAC). O ciclo operacional completo conecta todos os módulos sem etapas isoladas:

```text
[1. Cadastros Estruturais]  -->  [2. Motor C11/OpenMP (ctypes)]  -->  [3. IA Preditiva (scikit-learn)]
 Admin/Secretaria: campi,        POST /api/v1/alocacao/otimizar       POST /api/v1/ia/analisar ou cron:
 salas, equipamentos, cursos,    serializa structs 64-bit, resolve    HistGradientBoosting calibrado
 disciplinas, turmas e           grade sem choques em O(T*S),         estima absenteismo; ociosidade
 matriculas (contagem atomica).  persiste em horario + log_alocacao.  >= 40% gera sugestao pendente.
                                                                                     |
                                                                                     v
[6. Auditoria & Relatorios] <--  [5. Grade & Dashboard]          <--  [4. Human-in-the-Loop]
 GET /api/v1/logs e              Grade docente/discente (/horarios)   PATCH /api/v1/sugestoes/{id}:
 /api/v1/relatorios (CSV em      e Dashboard (/dashboard) refletem    Admin/Coordenador aprova ou
 streaming) consolidam trilha    salas atualizadas, ocupacao por      rejeita com parecer. Somente a
 imutavel em log_alocacao.       dia/turno e vagas recuperadas.       aprovacao altera horario.sala_id.
```

Cada transição preserva as fronteiras arquiteturais invioláveis do projeto: o frontend Angular não executa regras combinatórias nem cálculos de IA; o motor em C/OpenMP não possui acesso ao banco de dados nem dependências externas; e a IA preditiva jamais modifica diretamente a tabela `horario`, atuando estritamente sob governança *Human-in-the-Loop*.

---

## 11.3 Revisão Geral de Código e Saneamento do Repositório (PR #108)

O **PR #108** (commit `fd1461a`, Task ClickUp `#1dft1fajvph`, diff líquido de `+34 / -15` linhas de código de produção) executou uma auditoria transversal de qualidade, segurança e higiene no repositório:

- **Hardening de Tratamento de Erros no Backend (OWASP API8:2023 / CWE-209):**
  - Em `backend/app/api/v1/endpoints/alocacao.py`, a interpolação direta de exceções internas (`{exc}`) nas respostas HTTP `503` (`otimizar_alocacao_endpoint` e `benchmark_alocacao_endpoint`) e HTTP `500` (persistência transacional) foi substituída por mensagens genéricas seguras, mantendo o rastreamento completo no servidor via `logger.error` / `logger.exception` e encadeamento `from exc`.
  - Em `backend/app/api/v1/endpoints/motor.py`, substituiu-se `detail=str(e)` nos retornos HTTP `503` e `400` de `POST /api/v1/motor/teste-integracao` por mensagens controladas com registro interno via `logger.error` / `logger.warning` e encadeamento `from e`.
- **Observabilidade (Eliminação de `try/except/pass` — Ruff S110):**
  - Em `backend/app/services/ia_service.py`, dois blocos silenciosos `except Exception: pass` foram substituídos por `logger.warning(...)` (falha ao carregar artefato `joblib`) e `logger.debug(...)` (parse de probabilidade no motivo).
  - Em `backend/app/services/motor_service.py`, o bloco silencioso em `os.add_dll_directory` passou a registrar telemetria em `logger.debug(...)`.
- **Higiene do Frontend (`frontend/src/app/`):**
  - Remoção de imports não utilizados em `grade-horaria.component.ts`, `grade-horaria.component.spec.ts`, `admin.component.spec.ts` e `admin.service.spec.ts`, atingindo **0 erros** em `tsc --noUnusedLocals --noUnusedParameters`.
- **Saneamento de Diretórios Legados e Configurações:**
  - Remoção definitiva do diretório legado `ia_previsao/` (3 arquivos placeholder da Sprint 01: `README.md`, `dados/.gitkeep` e `requirements.txt`), pois o módulo oficial de IA reside integralmente em `backend/app/services/ia_service.py` e `backend/app/services/ml_evaluator.py`.
  - Atualização de `.gitignore` (adição de `.ruff_cache/` e remoção de regras obsoletas de `ia_previsao/`), atualização da árvore de diretórios no `README.md` e alinhamento de `ACCESS_TOKEN_EXPIRE_MINUTES=60` em `.env.example` com `backend/app/config.py`.
  - Auditoria com `git ls-files` confirmando zero arquivos `.env`, chaves privadas, bancos `.db` ou artefatos `.joblib`/`.pkl` versionados indevidamente, bem como zero ocorrências de `print(`, `breakpoint(`, `pdb.set_trace` ou emojis no código de produção.

---

## 11.4 Manual Técnico da Solução e Revisão Documental (PR #109)

O **PR #109** (commit `067b84f`, Task ClickUp `#1dft1fajvpj`) publicou o Manual Técnico oficial e sincronizou o documento arquitetural mestre (`docs/projeto-gestao-salas-escalas.md`) com o estado real da versão `v1.0.0-rc.1`:

- **Link Direto no GitHub:** [docs/manuais/manual-tecnico.md](https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas/blob/main/docs/manuais/manual-tecnico.md) (378 linhas)
- **Documento Arquitetural Revisado:** [docs/projeto-gestao-salas-escalas.md](https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas/blob/main/docs/projeto-gestao-salas-escalas.md)

### Conteúdo Essencial Consolidado no Manual Técnico

| Seção do Manual Técnico | Síntese do Conteúdo Documentado |
| :--- | :--- |
| **1. Visão Geral da Arquitetura** | Arquitetura em 3 camadas (Angular 20 SPA, FastAPI/Python 3.12, PostgreSQL 16 + Motor C11/OpenMP + IA `scikit-learn`), diagrama Mermaid e fluxo ponta a ponta unificado. |
| **2. Stack e Bibliotecas** | Versões exatas extraídas de `backend/requirements.txt` (FastAPI `>=0.110.0`, SQLAlchemy `>=2.0.28`, Alembic `>=1.13.1`, scikit-learn `>=1.4.0`, APScheduler `>=3.10.4`) e `frontend/package.json` (Angular `^20.2.0`, TypeScript `~5.9.2`, RxJS `~7.8.0`, Karma/Jasmine). |
| **3. Organização de Módulos** | Mapeamento completo de diretórios: `backend/app/` (17 roteadores, 14 models, schemas, services), `backend/motor_alocacao/`, `frontend/src/app/`, `docker/` e `scripts/`. |
| **4. Banco de Dados PostgreSQL** | Catálogo das **14 tabelas** com chaves primárias, FKs, constraints (`UNIQUE`, `CHECK`) e histórico das **3 migrations Alembic** (`001_initial_schema`, `002_add_campus_id_to_log_alocacao`, `003_release_candidate_indexes` com 6 índices compostos). |
| **5 e 6. Requisitos e Execução** | Pré-requisitos e passo a passo para modo conteinerizado (`make setup`, `make sigaas`, `make migrate`, `make seed`, `make ps`, `make reset` e composes `local`, `homolog`, `prod`) e modo híbrido local. |
| **7. Variáveis de Ambiente** | Catálogo completo baseado em `.env.example` (`POSTGRES_*`, `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES=60`), sem credenciais sensíveis e com recomendações de hardening em produção. |
| **8. APIs REST e OpenAPI** | Documentação interativa Swagger (`/api/v1/docs`), ReDoc (`/api/v1/redoc`), schema OpenAPI 3.1 (`/api/v1/openapi.json`), autenticação JWT HS256 com `DUMMY_HASH` contra *timing attacks*, isolamento BOLA/IDOR por `campus_id` e mapa dos 17 grupos de endpoints. |
| **9. Motor C/OpenMP e IA** | Heurística *Best-Fit Decreasing* em `O(T * S)`, contrato FFI `ctypes` com structs alinhadas em 64-bit, benchmarks estatísticos `N=10` (speedup de `1,29x` até `3,74x`, `CV < 15%`), anomalias blindadas (`BUG-HPC-01` a `BUG-HPC-04`) e pipeline `HistGradientBoostingClassifier` + `CalibratedClassifierCV` com limiar de **40%** e governança *Human-in-the-Loop*. |
| **10. Manutenção, Testes e CI** | Comandos de verificação local (`pytest --cov-fail-under=85`, `ruff`, `bandit`, `make`, `ng test`, `ng build`, `prettier`), detalhamento dos 3 estágios do `.github/workflows/ci.yml` e boas práticas de evolução segura. |

---

## 11.5 Manual do Usuário por Perfil (PR #110)

O **PR #110** (commit `c5d76ce`, Task ClickUp `#1dft1fajvpk`) publicou o Manual do Usuário em linguagem acessível e orientada a tarefas, permitindo que qualquer usuário final opere o SIGAAS sem conhecimento prévio de código-fonte:

- **Link Direto no GitHub:** [docs/manuais/manual-usuario.md](https://github.com/ValdVdC/Fabrica-de-Software-Gerenciador-de-salas/blob/main/docs/manuais/manual-usuario.md) (244 linhas)

### Conteúdo Essencial Consolidado no Manual do Usuário

1. **Público-Alvo e Matriz dos 5 Perfis RBAC:** detalhamento claro das telas e limites operacionais de **Administrador (`admin`)**, **Coordenador (`coordenador`)**, **Secretaria (`secretaria`)**, **Professor (`professor`)** e **Aluno (`aluno`)**, evidenciando o isolamento por campus e as operações exclusivas de Administrador (visão multi-campus, exclusão de sala via `DELETE /salas/{id}` e execução do benchmark científico via `POST /alocacao/benchmark`).
2. **Acesso, Autenticação e Credenciais de Demonstração:** instruções de login (`/login`), encerramento seguro de sessão e tabela oficial das 9 contas geradas por `scripts/seed_db.py` (com senha padrão `sigaas123` para ambiente de avaliação).
3. **Visão Geral das 6 Telas Principais:** `Administracao` (5 abas), `Secretaria Academica` (5 abas), `Grade Horaria` (Docente e Discente com `Minhas Matriculas`), `Dashboard` (4 KPIs, gráficos de ocupação e tabela `Ultimos Eventos de Auditoria`), `Relatorios` (abas `Ocupacao de Salas` e `Remanejamentos` com CSV) e `Historico` (auditoria `LogAlocacao`).
4. **7 Fluxos Ponta a Ponta Ilustrados com 16 Capturas de Tela:**
   - **Fluxo 1:** Cadastros de salas e catálogo/vínculo de equipamentos (`print_18`, `print_03`, `print_04`);
   - **Fluxo 2:** Cadastros de cursos, disciplinas, turmas e matrículas (`print_19`);
   - **Fluxo 3:** Execução da Alocação Inteligente OpenMP e leitura de métricas de speedup (`print_09`);
   - **Fluxo 4:** Análise preditiva de IA e aprovação/rejeição humana de remanejamentos (`print_12`, `print_13`);
   - **Fluxo 5:** Consulta à grade horária semanal por docente e discente (`print_20`, `print_21`);
   - **Fluxo 6:** Acompanhamento no Dashboard consolidado e exportação CSV em Relatórios (`print_15`, `print_16`);
   - **Fluxo 7:** Rastreamento de eventos na Trilha de Auditoria e Histórico (`print_17`), complementados pelas telas de login (`print_11`), cabeçalho (`print_14`), erro `409` (`print_04_admin_erro_409`) e banner `403` (`print_22`).
5. **Guia de Validações, Erros Comuns e Perguntas Rápidas:** orientações objetivas para campos obrigatórios, limites numéricos, datas invertidas, justificativa obrigatória na rejeição de sugestões e tratamento dos códigos HTTP `401`, `403`, `404/422` e `409`.

---

## 11.6 Registro Factual de Dificuldades Encontradas e Soluções Aplicadas

Atendendo à devolutiva da Sprint 07, registram-se abaixo as dificuldades reais encontradas durante a Sprint 11 e as respectivas soluções aplicadas:

| Dificuldade Encontrada na Sprint 11 | Causa Raiz Identificada | Solução Aplicada e Evidência |
| :--- | :--- | :--- |
| **1. Exposição de exceções internas em endpoints HPC e blocos `except: pass` silenciosos** | Em revisões anteriores, `alocacao.py` e `motor.py` retornavam `str(e)` no `detail` HTTP e `ia_service.py` / `motor_service.py` continham fallbacks sem log (Ruff S110). | Aplicado hardening OWASP API8:2023 (mensagens genéricas seguras + `logger.error`/`exception` com `from exc`) e logs estruturados `warning`/`debug` no PR #108 (`fd1461a`). |
| **2. Imprecisões pontuais no rascunho inicial do Manual do Usuário frente às regras reais da API** | Na Rodada 1 do debate adversarial do PR #110, `adversary-breaker` emitiu veto ao constatar divergências sobre permissão exclusiva de Admin (`DELETE /salas/{id}` e benchmark), obtenção de IDs de usuários na Secretaria e vínculo do `Periodo Letivo` na aba IA. | Corrigidas todas as discrepâncias diretamente contra os roteadores FastAPI e componentes Angular no commit de remediação do PR #110 (`c5d76ce`), alcançando consenso unânime 4/4 na Rodada 2 (Re-Review). |
| **3. Resíduos legados da Sprint 01 e desalinhamento de expiração JWT em `.env.example`** | O diretório placeholder `ia_previsao/` permanecia no repositório desde a Sprint 01 e `.env.example` divergia do padrão `ACCESS_TOKEN_EXPIRE_MINUTES=60` definido em `config.py`. | Removido `ia_previsao/`, limpo `.gitignore`, sincronizado `.env.example` e validado via `git ls-files` que nenhum segredo ou binário sensível está versionado (PR #108). |
| **4. Garantia de coerência entre capturas de sprints intermediárias e interface `v1.0.0-rc.1`** | Algumas capturas históricas (`print_03`, `print_04`, `print_09`, `print_12`, `print_13`) exibiam rótulos anteriores do menu superior (`Infraestrutura & IA`). | Incluída nota explícita de rastreabilidade no Manual do Usuário explicando a correspondência exata com o layout atual (`v1.0.0-rc.1`) sem comprometer a veracidade das evidências. |

---

## 11.7 Evidências de Testes Automatizados, CI na Branch `main` e Governança Ágil

No estado consolidado da branch `main` (commit `067b84f`), os commits `c5d76ce` (PR #110) e `067b84f` (PR #109) alteraram exclusivamente documentação em `docs/`. A última execução completa do pipeline de Integração Contínua sobre o código-fonte consolidado ocorreu no commit `fd1461a` (PR #108, **GitHub Actions Run `#44915266637`**, duração total `4m53s`), com **5/5 checks aprovados**:

| Check de CI (GitHub Actions — Run `#44915266637`) | Status | Duração | Evidência Consolidada |
| :--- | :---: | :---: | :--- |
| **1. Code Quality & Policy Enforcement** | `SUCCESS` | `30s` | Sintaxe Python (`py_compile`), `ruff`, `bandit` (segurança estática) e `prettier --check` 100% aprovados. |
| **2. Allocation Engine (C & OpenMP)** | `SUCCESS` | `12s` | Compilação `gcc -O3 -fopenmp -shared` sem warnings impeditivos e biblioteca compartilhada validada. |
| **3. Backend Tests & Coverage (Pytest)** | `SUCCESS` | `2m09s` | **276 testes aprovados**, cobertura global de **90,76%** no CI Linux (`90,73%` em ambiente local Windows; acima do piso mínimo `>= 85%`). |
| **4. Frontend Tests & Build (Angular)** | `SUCCESS` | `37s` | **165/165 specs Karma/ChromeHeadless SUCCESS** e build de produção Angular limpo (**479,25 kB**). |
| **5. Docker Environment Smoke Test** | `SUCCESS` | `2m03s` | Build das imagens, inicialização full-stack (`db`, `backend`, `frontend`, `cron`), migrations Alembic e smoke test HTTP (`/health`, `/docs`, `/api/v1/motor/status`, `:4200` e proxy Nginx). |

### Governança Ágil e Estado dos Pull Requests da Sprint 11

| PR | Branch | Commit na `main` | Escopo | ID ClickUp | Situação |
| :---: | :--- | :---: | :--- | :---: | :--- |
| **#108** | `chore/sprint11-code-sanitation` | `fd1461a` | Revisão geral de código (hardening, observabilidade, limpeza TS), remoção de `ia_previsao/`, `.env.example`, `.gitignore` e `SPEC-011` | `#1dft1fajvph` | **Mesclado na `main`** |
| **#110** | `docs/sprint11-manual-usuario` | `c5d76ce` | Manual do Usuário completo (`docs/manuais/manual-usuario.md`, 244 linhas, 5 perfis, 7 fluxos, 16 capturas) | `#1dft1fajvpk` | **Mesclado na `main`** |
| **#109** | `docs/sprint11-manual-tecnico` | `067b84f` | Manual Técnico completo (`docs/manuais/manual-tecnico.md`, 378 linhas) e revisão de `docs/projeto-gestao-salas-escalas.md` | `#1dft1fajvpj` | **Mesclado na `main`** |
| **PR 4** | `docs/sprint11-relatorio-pdf` | Em revisão | `relatorio-sprint11.md`, `relatorio-consolidado-sprints-01-a-11.md` e `Grupo31_SIGAAS_Sprints01-11.pdf` | `#1dft1fajvpm` | **Aberto para Gate 2** |

---

## 11.8 Conclusão, Publicação de Tag e Próximos Passos (Sprint 12)

A Sprint 11 conclui a preparação documental, de qualidade de código e de saneamento do repositório do **SIGAAS (`v1.0.0-rc.1`)** na branch `main` (`067b84f`), entregando:

- Código-fonte revisado, endurecido contra vazamento de detalhes internos de erro, livre de diretórios legados e validado por **276 testes backend (90,76% de cobertura no CI)**, **165 testes frontend** e **5/5 checks de CI**;
- **Manual Técnico** e **Manual do Usuário** completos e publicados em `docs/manuais/`, conectados à visão ponta a ponta do sistema;
- Relatório cumulativo das Sprints 01 a 11 e PDF oficial ABNT (`docs/entregas/Grupo31_SIGAAS_Sprints01-11.pdf`) íntegros e sem desvios institucionais.

### Encerramento da Sprint 11 e Próximos Passos (Sprint 12 — 28/11/2026)

1. Submeter o PR 4 (`docs/sprint11-relatorio-pdf`) à aprovação humana no **Gate 2** e efetivar o *Squash and Merge* na `main`.
2. Publicar a tag oficial **`v0.11.0-sprint11`** na branch `main` consolidada (acionando `.github/workflows/release.yml`) e realizar a entrega formal do PDF no Microsoft Teams.
3. **Sprint 12 (28/11/2026 — Encerramento e Apresentação Final):** executar o **Code Freeze** (congelamento de código para estabilidade total), gravar os **vídeos acadêmicos de demonstração** (fluxo ponta a ponta integrado, benchmark sequencial vs. paralelo OpenMP e remanejamento preditivo *Human-in-the-Loop*), revisar a apresentação final e realizar a defesa perante a banca examinadora.
