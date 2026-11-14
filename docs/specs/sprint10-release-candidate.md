# SPEC-010: Sprint 10 — Release Candidate (Estabilização, OpenAPI/Swagger, Schema Final e README Completo)

- **Status:** Aguardando Aprovação (Gate 1)
- **Sprint:** 10 (Data-Limite: 14/11/2026 às 23:59)
- **Responsáveis:** Wesclei Batista (PO), Ewerton Thyago (SM) e Squad SIGAAS (Osvaldo, Gabriel, Flávio)
- **Referência Normativa:** `docs/projeto-gestao-salas-escalas.md` (Seção 4 — Sprint 10)

---

## 1. Contexto e Objetivo

A Sprint 10 marca o marco de **Release Candidate (`v1.0.0-rc.1`)** do Sistema Integrado de Gestão Acadêmica e Alocação de Salas com IA (SIGAAS). Após a conclusão da homologação de testes na Sprint 09 (270 testes no backend com 90,87% de cobertura e 163 testes no frontend), esta etapa consolida:
1. A estabilização final da aplicação como Release Candidate (`v1.0.0-rc.1`);
2. A verificação e consolidação do schema definitivo do PostgreSQL via Alembic;
3. A documentação interativa completa da API REST via OpenAPI 3.1 / Swagger UI / ReDoc;
4. O polimento final da interface SPA Angular;
5. A atualização integral do `README.md` técnico e a consolidação do relatório cumulativo oficial (`Sprints 01 a 10`).

---

## 2. Histórias de Usuário e Critérios de Aceite (Gherkin)

### História 1: Documentação Interativa de APIs (OpenAPI / Swagger / ReDoc) e Versão RC
> **Como** integrador, avaliador ou desenvolvedor,  
> **Quero** acessar a documentação interativa OpenAPI/Swagger e ReDoc com descrições completas de tags, endpoints, autenticação JWT e códigos de resposta,  
> **Para** explorar e testar todos os contratos da API do SIGAAS sem ambiguidade.

#### Cenário 1.1: Metadados OpenAPI e endpoints de documentação
- **Given** o servidor FastAPI inicializado com versão `1.0.0-rc.1`;
- **When** for realizada uma requisição `GET /api/v1/openapi.json`, `GET /api/v1/docs` e `GET /api/v1/redoc`;
- **Then** todas devem retornar HTTP `200 OK`;
- **And** o JSON OpenAPI deve conter `info.version == "1.0.0-rc.1"`, metadados de tags descritivas para todos os 17 módulos e esquema de segurança `BearerAuth` (JWT).

#### Cenário 1.2: Cobertura descritiva das rotas críticas
- **Given** o schema OpenAPI gerado dinamicamente pelo FastAPI;
- **When** forem inspecionadas as rotas de Autenticação, Alocação OpenMP, IA Preditiva, Sugestões, Motor C, Dashboard e Relatórios;
- **Then** todas devem possuir `summary` e `description` claros em português técnico, além de tipagem Pydantic v2 para entrada e saída.

---

### História 2: Schema Final do PostgreSQL e Paridade com Migrations Alembic
> **Como** DBA / Engenheiro de Dados,  
> **Quero** garantir paridade estrita entre os models SQLAlchemy e o histórico de migrations Alembic, com índices compostos adequados às consultas críticas,  
> **Para** assegurar integridade estrutural e desempenho previsível no Release Candidate.

#### Cenário 2.1: Paridade ORM vs. Alembic Head e Índices de Desempenho
- **Given** o banco migrado via `alembic upgrade head`;
- **When** for executado o teste de paridade estrutural (`Base.metadata` vs. tabelas/índices reais no banco) e o ciclo completo `upgrade` / `downgrade`;
- **Then** todas as 14 tabelas e índices compostos definidos nos models devem existir no schema migrado sem divergências;
- **And** o script `scripts/seed_db.py` deve executar com idempotência total (`make seed`).

---

### História 3: Polimento Final da Interface Angular (Release Candidate)
> **Como** usuário institucional (Admin, Coordenador, Secretaria, Docente ou Aluno),  
> **Quero** utilizar uma interface final polida, responsiva e consistente, identificando claramente a versão Release Candidate do sistema,  
> **Para** operar todos os fluxos acadêmicos com clareza visual e zero falhas de layout.

#### Cenário 3.1: Identificação de versão RC e integridade visual
- **Given** a aplicação Angular compilada em modo produção (`ng build`);
- **When** o usuário autenticado navegar pelo layout principal (`ShellComponent`);
- **Then** o rodapé ou barra lateral deve exibir discretamente a versão `v1.0.0-rc.1` (sem emojis, utilizando ícones SVG vetoriais);
- **And** a suíte Karma/ChromeHeadless e o build de produção devem concluir com 100% de aprovação e zero erros de orçamento de bundle.

---

### História 4: README Técnico Completo e Pacote Acadêmico da Sprint 10
> **Como** avaliador da banca e usuário externo,  
> **Quero** consultar um `README.md` técnico completo e o relatório cumulativo oficial em PDF (Sprints 01 a 10),  
> **Para** compreender a arquitetura, instalar, executar e auditar todo o projeto SIGAAS.

#### Cenário 4.1: README técnico completo e PDF cumulativo oficial
- **Given** a branch `main` consolidada com os PRs 1, 2 e 3 da Sprint 10;
- **When** for revisado o `README.md` e gerado o arquivo `docs/entregas/Grupo31_SIGAAS_Sprints01-10.pdf`;
- **Then** o `README.md` deve documentar arquitetura, stack, comandos `make`, credenciais de homologação, links Swagger/ReDoc, resultados de benchmark C/OpenMP e métricas ML;
- **And** o PDF oficial deve respeitar rigorosamente a Regra 8 do `AGENTS.md` (zero alucinações institucionais).

---

## 3. Fatiamento em Pull Requests (Limite <= 400 linhas de código por PR)

| Ordem | PR / Branch | Task ClickUp | Responsável | Escopo |
| :---: | :--- | :---: | :--- | :--- |
| **PR 1** | `feat/rc-openapi-docs` | `#1dft1faj11r` | Osvaldo (Backend) | Versão `1.0.0-rc.1`, OpenAPI tags, ReDoc, docstrings nos endpoints e `test_openapi_docs.py` |
| **PR 2** | `feat/rc-schema-final` | `#1dft1faj11t` | Osvaldo / Flávio | Paridade ORM vs. Alembic, índices compostos finais (se aplicável via migration `003`) e testes de schema |
| **PR 3** | `feat/rc-frontend-polish` | `#1dft1faj11u` | Gabriel (Frontend) | Versão `v1.0.0-rc.1` no `ShellComponent`, revisão visual final e verificação de build/Karma |
| **PR 4** | `docs/sprint10-readme-relatorio` | `#1dft1faj11w` | Flávio (DBA / Docs) | `README.md` técnico completo, `relatorio-sprint10.md`, `relatorio-consolidado-sprints-01-a-10.md` e PDF `Grupo31_SIGAAS_Sprints01-10.pdf` |
