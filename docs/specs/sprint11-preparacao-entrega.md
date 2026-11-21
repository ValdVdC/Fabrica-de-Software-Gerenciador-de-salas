# SPEC-011: Sprint 11 — Preparação para Entrega (Manuais, Revisão de Código e Saneamento)

- **Status:** Aprovada (Gate 1)
- **Sprint:** 11 (Data-Limite: 21/11/2026 às 23:59)
- **Responsáveis:** Wesclei Batista (PO), Ewerton Thyago (SM) e Squad SIGAAS (Osvaldo, Gabriel, Flávio)
- **Referência Normativa:** `docs/projeto-gestao-salas-escalas.md` (Seção 4 — Sprint 11)

---

## 1. Contexto e Atendimento às Devolutivas Anteriores

A Sprint 11 tem como objetivo organizar e finalizar a documentação técnica e de usuário, revisar integralmente o código-fonte e sanear o repositório GitHub para a entrega e apresentação final.

Além dos 5 entregáveis obrigatórios da disciplina, esta especificação incorpora diretamente os cuidados apontados nas devolutivas das Sprints 07, 08 e 09:
1. **Rastreabilidade de Versão e Tag Formal:** O PDF final só deve ser gerado após o merge dos PRs técnicos/documentais na `main`, seguido da publicação da **Git Tag oficial da Sprint (`v0.11.0-sprint11`)** via `.github/workflows/release.yml`;
2. **Fluxo Ponta a Ponta Unificado:** Evidenciar claramente nos manuais e no relatório como cadastro, alocação C/OpenMP, IA preditiva, remanejamento *Human-in-the-Loop*, dashboard, relatórios CSV e auditoria funcionam como um único sistema integrado;
3. **Registro Factual de Datas e Dificuldades:** Data oficial da Sprint 11 (`21/11/2026`) e registro objetivo das dificuldades reais encontradas e soluções aplicadas.

---

## 2. Histórias de Usuário e Critérios de Aceite (Gherkin)

### História 1: Revisão Geral de Código e Saneamento do Repositório
> **Como** equipe de engenharia,  
> **Quero** revisar os módulos backend/frontend e sanear arquivos legados ou temporários do repositório,  
> **Para** entregar um código-fonte limpo, seguro, legível e 100% aderente às boas práticas.

#### Cenário 1.1: Limpeza, segurança e integridade da suíte
- **Given** o código atual da branch `main`;
- **When** forem revisados backend (`backend/app/`) e frontend (`frontend/src/app/`), removidos eventuais códigos mortos, imports não utilizados ou logs de debug, e verificados `.gitignore` / `.env.example` / diretórios legados (`ia_previsao/`);
- **Then** nenhuma credencial ou dado sensível deve existir versionado no repositório;
- **And** todas as suítes automatizadas (Pytest backend, Motor C e Karma/ng build frontend) devem permanecer 100% aprovadas.

---

### História 2: Manual Técnico e Revisão da Documentação Final
> **Como** avaliador técnico ou mantenedor futuro,  
> **Quero** consultar o Manual Técnico completo e a documentação arquitetural alinhada ao sistema real,  
> **Para** compreender, configurar, executar e manter todos os componentes do SIGAAS.

#### Cenário 2.1: Manual Técnico completo (`docs/manuais/manual-tecnico.md`)
- **Given** a arquitetura consolidada na versão `v1.0.0-rc.1`;
- **When** o Manual Técnico for publicado;
- **Then** deve cobrir arquitetura, stack/bibliotecas, organização de módulos, schema PostgreSQL (14 tabelas, índices e Alembic), requisitos, instalação/execução, variáveis de ambiente (sem credenciais sensíveis), APIs OpenAPI/Swagger, motor C/OpenMP (`ctypes`), IA `scikit-learn` (limiar 40%) e orientações de manutenção.

---

### História 3: Manual do Usuário por Perfil
> **Como** usuário final (Admin, Coordenador, Secretaria, Professor ou Aluno),  
> **Quero** um Manual do Usuário claro, acessível e ilustrado com telas do sistema,  
> **Para** executar todos os fluxos acadêmicos sem conhecimento prévio do código.

#### Cenário 3.1: Manual do Usuário acessível (`docs/manuais/manual-usuario.md`)
- **Given** as interfaces e fluxos implementados no Angular SPA;
- **When** o Manual do Usuário for publicado;
- **Then** deve conter apresentação, público-alvo, acesso/autenticação, descrição das telas, passo a passo dos fluxos ponta a ponta (cadastros, alocação, remanejamento, grade, dashboard, relatórios, auditoria), referências às capturas de tela em `docs/entregas/images/` e orientações sobre mensagens/validações.

---

### História 4: Relatório Consolidado, PDF Oficial e Publicação de Tag
> **Como** Scrum Master e banca examinadora,  
> **Quero** um PDF único cumulativo (Sprints 01 a 11) coerente com o estado final da `main` e marcado por tag oficial de release,  
> **Para** formalizar a entrega da Sprint 11 no Microsoft Teams com rastreabilidade total.

#### Cenário 4.1: Pacote acadêmico alinhado à `main` e tag publicada
- **Given** os PRs 1, 2 e 3 devidamente mesclados na `main`;
- **When** forem gerados `docs/entregas/relatorio-sprint11.md`, `docs/entregas/relatorio-consolidado-sprints-01-a-11.md` e `docs/entregas/Grupo31_SIGAAS_Sprints01-11.pdf`;
- **Then** o PDF deve consolidar os manuais, a revisão de código, o saneamento, links do GitHub, dificuldades e próximos passos, respeitando a Regra 8 do `AGENTS.md`;
- **And** após o merge do PR 4, deve ser publicada a tag `v0.11.0-sprint11` na `main`.

---

## 3. Fatiamento em Pull Requests (Limite <= 400 linhas de código por PR)

| Ordem | PR / Branch | Task ClickUp | Responsável | Escopo |
| :---: | :--- | :---: | :--- | :--- |
| **PR 1** | `chore/sprint11-code-sanitation` | `#1dft1fajvph` | Osvaldo / Gabriel | Revisão geral de código, limpeza de imports/debug/legado (`ia_previsao/`), verificação de `.env.example`/`.gitignore` e inclusão da `SPEC-011` |
| **PR 2** | `docs/sprint11-manual-tecnico` | `#1dft1fajvpj` | Osvaldo / Flávio | `docs/manuais/manual-tecnico.md` e revisão final da documentação arquitetural |
| **PR 3** | `docs/sprint11-manual-usuario` | `#1dft1fajvpk` | Gabriel / Wesclei | `docs/manuais/manual-usuario.md` por perfil com passo a passo e imagens de `docs/entregas/images/` |
| **PR 4** | `docs/sprint11-relatorio-pdf` | `#1dft1fajvpm` | Flávio / SM | `relatorio-sprint11.md`, `relatorio-consolidado-sprints-01-a-11.md`, `Grupo31_SIGAAS_Sprints01-11.pdf` (após PRs 1–3) + tag `v0.11.0-sprint11` |
