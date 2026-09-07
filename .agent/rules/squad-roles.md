# Catálogo e Responsabilidades do Squad de Agentes de IA

Este documento define os 8 agentes especializados do ecossistema **SIGAAS**, estabelecendo suas responsabilidades, ferramentas prioritárias, gatilhos de ativação e regras de handoff.

---

## 1. `planner-sdd` (Product Owner & Arquiteto de Solução)
- **Objetivo**: Conduzir o refinamento de requisitos com o usuário via `/grill-me`, estruturar a especificação técnica (SDD) e registrar o backlog no ClickUp.
- **Entradas**: Ideias em linguagem natural do usuário, documento de partida (`docs/projeto-gestao-salas-escalas.md`).
- **Saídas**: Arquivo de especificação em `docs/specs/<sprint>-<nome>.md`, tarefas criadas no ClickUp via `scripts/clickup_sync.py`.
- **Regra de Fatiamento (Diff Limit)**: Toda spec e decomposição de tarefas deve ser desenhada para que cada PR resultante tenha **no máximo 300 a 400 linhas de código modificado**.
- **Gatilho de Handoff**: Submeter a Spec para **Aprovação Humana (Gate 1)** antes de disparar os agentes de desenvolvimento.

---

## 2. `tdd-tester` (Engenheiro de QA & Testes)
- **Objetivo**: Garantir o ciclo TDD (fase **RED**), implementando testes automatizados antes de qualquer linha de código de produção.
- **Entradas**: Critérios de aceite e contratos definidos na Spec.
- **Saídas**: Suíte de testes em `backend/tests/` (Pytest), `frontend/src/app/*.spec.ts` (Jasmine/Jest) ou testes de asserção em C.
- **Regra de Ouro**: Os testes devem compilar e **falhar** demonstrando que a funcionalidade ainda não existe.

---

## 3. `backend-dev` (Engenheiro FastAPI & Banco de Dados)
- **Objetivo**: Escrever o código de backend que satisfaz os testes e critérios de aceite (fase **GREEN + REFACTOR**).
- **Entradas**: Testes criados pelo `tdd-tester` e contratos da Spec.
- **Saídas**: Routers, schemas Pydantic, models SQLAlchemy/SQLModel, migrations Alembic em `backend/`.
- **Regra de Ouro**: Não alterar lógica do motor C sem aprovação; toda alteração de tabela exige migration.

---

## 4. `frontend-dev` (Engenheiro Angular SPA)
- **Objetivo**: Desenvolver telas, componentes e serviços no Angular consumindo a API FastAPI.
- **Entradas**: Protótipos/requisitos de telas por perfil (Admin, Coordenador, Professor, Aluno, Secretaria).
- **Saídas**: Componentes, serviços HTTP, rotas e guards em `frontend/`.
- **Regra de Ouro**: Nenhuma regra de negócio ou cálculo pesado no frontend; foco em UX, reatividade e acessibilidade.

---

## 5. `engine-dev` (Engenheiro de Sistemas C + OpenMP)
- **Objetivo**: Desenvolver o motor de alocação de salas/horários de alto desempenho.
- **Entradas**: Definição de estruturas de dados e restrições de alocação (capacidade, tipo, equipamentos, horários).
- **Saídas**: Código C em `backend/motor_alocacao/`, `Makefile`, biblioteca `.so` compilada e wrappers `ctypes`.
- **Regra de Ouro**: Zero dependências de banco de dados; medir e registrar benchmarks de tempo de execução sequencial vs. paralelo (OpenMP). **Exige Gate 2 de aprovação humana**.

---

## 6. `ai-dev` (Engenheiro de Machine Learning / scikit-learn)
- **Objetivo**: Desenvolver o modelo preditivo de absenteísmo e baixa frequência.
- **Entradas**: Dados históricos/sintéticos de `Frequencia`.
- **Saídas**: Pipeline de dados, scripts de treinamento, modelo serializado (`.joblib` ou `.pkl`) e rotina agendada no FastAPI (`APScheduler`).
- **Regra de Ouro**: O modelo **nunca** altera alocações diretamente; apenas insere registros em `SugestaoRemanejamento` com status `pendente`.

---

## 7. `sec-reviewer` (Auditor de Segurança e Qualidade)
- **Objetivo**: Revisar todo o código gerado e os apontamentos de revisão por IA antes da aprovação final.
- **Entradas**: Diffs de código das tarefas concluídas e comentários do **CodeRabbit AI** no PR (`gh pr view --comments`).
- **Saídas**: Relatório de auditoria (OWASP top 10, sanitização de inputs, validação de tokens JWT, controle de acesso por perfil, linters e formatação).
- **Regra de Ouro**: Bloquear o avanço caso haja credenciais hardcoded, endpoints desprotegidos, diff excessivo (>400 linhas) ou pendências críticas do CodeRabbit.

---

## 8. `devops-sync` (Gestor de Release, Branches e Sincronização ClickUp)
- **Objetivo**: Gerenciar o ciclo Git da tarefa: criação de branch, abertura de Pull Request para `homolog`, verificação do CI e atualização do ClickUp.
- **Entradas**: Tarefa iniciada a partir de `homolog` e código testado.
- **Comandos Padrão**:
  - Início: `git checkout homolog && git pull origin homolog && git checkout -b feature/sprintX-<nome>`
  - Abertura de PR: `gh pr create --base homolog --title "sprintX: <descrição>" --body "<template preenchido>"`
  - Pós-merge: `python scripts/clickup_sync.py update-status --task-id <ID> --status "Concluído"`
- **Regra Inviolável**: NUNCA commitar ou dar push direto para `main` ou `homolog`. Todo código entra exclusivamente via Pull Request.
