# AGENTS.md — Sistema de Gestão de Salas e Escalas com IA (SIGAAS)

Este arquivo é a fonte de verdade normativa para qualquer agente autônomo ou assistido (Antigravity, Claude Code, etc.) que trabalhar neste repositório. Leia por completo antes de planejar ou executar qualquer tarefa.

O documento de requisitos e arquitetura oficial está em `docs/projeto-gestao-salas-escalas.md`.
O catálogo e regras do Squad de agentes estão em `.agent/rules/squad-roles.md`.
O fluxo SDD + TDD está documentado em `.agent/workflows/sdd-cycle.md`.
O guia de prompts e handoff entre sessões está em `docs/handoff-guide.md`.

---

## 1. Contexto do Projeto
Projeto acadêmico (Fábrica de Software + Tópicos Avançados). Sistema multi-campus de gestão acadêmica com alocação inteligente de salas/horários.
Equipe com papéis fixos:
- Scrum Master
- Product Owner (PO)
- Dev Backend
- Dev Frontend
- Responsável BD / Documentação

---

## 2. Stack e Diretrizes Arquiteturais (Invioláveis)
- **Frontend**: Angular (SPA). Apresentação limpa baseada em perfis de acesso (Admin/Coordenação, Professor, Aluno, Secretaria). Nenhuma regra de negócio ou cálculo pesado vive no frontend.
- **Backend / API**: FastAPI (Python). Único ponto de entrada HTTP para clientes. Responsável por autenticação (JWT), multi-tenancy por campus, CRUDs, regras de negócio e orquestração.
- **Motor de Alocação**: C + OpenMP, compilado como biblioteca compartilhada (`motor_alocacao.so`) e carregado via `ctypes` no mesmo processo do FastAPI. **Sem dependências externas e sem conexão direta ao banco de dados**.
- **IA Preditiva de Falta**: Python (scikit-learn). Roda em background / job agendado (`APScheduler` embutido no processo do FastAPI). **NUNCA altera salas diretamente** — apenas gera registros em `SugestaoRemanejamento` com status `pendente`.
- **Banco de Dados**: PostgreSQL — única fonte da verdade para FastAPI e job de IA.
- **Ambiente e Deploy**: Docker Compose (`db` e `app`).

---

## 3. Metodologia SDD + TDD

1. **SDD (Spec-Driven Development)**:
   - Nenhuma linha de código deve ser escrita sem uma especificação aprovada em `docs/specs/<tipo>-<nome>.md`.
   - Toda spec deve conter: Contexto, Histórias de Usuário, Critérios de Aceite em formato Gherkin (`Given/When/Then`), Design de Arquitetura e Plano de Testes TDD.
   - Tarefas correspondentes devem ser registradas no ClickUp via script `scripts/clickup_sync.py` ou MCP.
2. **TDD (Test-Driven Development)**:
   - **Red**: Escrever testes automatizados unitários/integração que falham antes de escrever a implementação.
   - **Green**: Escrever o código mínimo necessário para fazer os testes passarem.
   - **Refactor**: Limpar o código garantindo que a suíte continue verde.

---

## 4. Regras Invioláveis de Desenvolvimento
1. **Nunca** implemente lógica de negócio no Angular nem acesso a banco no motor C.
2. **Toda alteração de schema** no banco de dados DEVE ser acompanhada de uma migration (Alembic).
3. O job de IA só gera `SugestaoRemanejamento` — a troca real de sala só ocorre com aprovação humana via endpoint `PATCH /sugestoes/{id}`.
4. No motor de alocação em C, sempre meça e registre o tempo sequencial vs. paralelo (essencial para as entregas e vídeos acadêmicos).
5. Toda funcionalidade deve ter testes automatizados cobrindo os critérios de aceite antes de ser concluída.
6. Commits e PRs devem seguir rigorosamente o padrão Conventional Commits: `<tipo>(<escopo>): <descrição curta no imperativo>` (ex.: `feat(schema): adicionar models postgres e migrations alembic`). Tipos válidos: `feat`, `fix`, `docs`, `test`, `perf`, `refactor`, `chore`, `ci`.
7. Valide integrações de alto risco primeiro: a integração FastAPI ↔ C via `ctypes` deve ser validada com prova de conceito antes do algoritmo de alocação completo.

---

## 5. Portões de Aprovação Humana (Human-in-the-Loop)
- **Gate 1**: Aprovação formal da Spec gerada pelo agente planejador antes de iniciar TDD/Dev.
- **Gate 2 (Review-driven)**: Aprovação humana explícita antes de aplicar:
  - Alterações de schema no PostgreSQL / migrations.
  - Implementação ou alteração do motor de alocação em C / OpenMP.
  - Endpoints que alterem a tabela `Horario` ou aprovem `SugestaoRemanejamento`.
  - Commits e merges finais de Sprint.

---

## 6. Política de Branches, PRs e Limite de Diff (Inviolável)
1. **Zero Push Direto**: Ninguém (humano ou agente) faz `git push` direto para `main`. A branch `main` é protegida e representa o estado contínuo e estável do produto.
2. **Fluxo de Branches (Trunk-Based Development)**:
   - Todo trabalho começa criando uma branch semântica a partir de `main`: `git checkout -b feat/<nome>` (ou `fix/<nome>`, `docs/<nome>`, `chore/<nome>`, `perf/<nome>`, `test/<nome>`).
   - Ao concluir a tarefa, o agente `devops-sync` abre o PR mirando a `main`: `gh pr create --base main`.
   - O PR passa obrigatoriamente por todos os checks de CI (Pytest >=85%, Motor C, Diff <= 400 linhas) e CodeRabbit AI.
   - Após aprovação humana e merge, o GitHub exclui a branch efêmera automaticamente (*auto-delete*).
   - Ao final da Sprint ou marco estável, a Release é publicada via Git Tag na `main` (`v*.*.*-sprint*` ou `v*.*.*`), acionando o workflow de deploy/release.
3. **Squash and Merge Exclusivo e Obrigatório**:
   - Todo merge para a `main` DEVE ser realizado obrigatoriamente via **Squash and Merge** (`gh pr merge <PR> --squash --delete-branch`).
   - O repositório no GitHub está configurado com `allow_merge_commit=false` e `allow_rebase_merge=false`, tornando tecnicamente impossível a criação acidental de commits de merge tradicionais ou rebase via interface web ou CLI.
   - Cada PR condensado resulta em exatamente 1 commit atômico e linear na branch `main`, preservando o histórico limpo, rastreável e aderente aos Conventional Commits (`<tipo>(<escopo>): <descrição curta> (#<PR>)`).
   - O título do commit condensado segue o padrão Conventional Commits do PR (`PR_TITLE`) e o corpo registra a descrição do PR (`PR_BODY`), suprimindo commits intermediários de desenvolvimento.
4. **Limite de Diff por PR**:
   - Cada PR deve conter no **máximo 300 a 400 linhas de código modificado** (excluindo migrações de banco ou lockfiles).
   - Se uma feature exigir mais código, o `planner-sdd` deve fatiá-la em subtarefas com PRs incrementais e testáveis.

---

## 7. Review por IA, Fallback e Debate Adversarial Pré-PR (Inviolável)
1. **Debate Adversarial Multi-Agente Pré-PR (.agent/workflows/adversarial-debate.md):**
   - Antes de submeter qualquer entrega para o Gate 2 humano, é mandatório executar a esteira de debate dialético multi-agente via `invoke_subagent`.
   - O comitê de análise simultânea opera com personas antagônicas: `advocate-mapper` (defesa e rastreabilidade), `adversary-breaker` (casos de borda, concorrência e falhas de lógica), `adversary-security` (OWASP, isolamento multi-campus e autenticação) e `adversary-compliance` (10 regras invioláveis e diff <= 400).
   - O código só avança com **CONSENSO UNÂNIME** formalizado pelo `debate-arbiter` / `sec-reviewer`. Havendo veto, a tarefa retorna imediatamente para correção técnica.
2. **Review por IA no GitHub (CodeRabbit AI):**
   - Todo PR aberto dispara verificação complementar pelo **CodeRabbit AI** configurada em `.coderabbit.yaml`.
   - **Inspeção Ativa de Comentários:** Terminantemente proibido considerar o PR pronto apenas pelo status do GitHub Checks (`gh pr checks`). É obrigatório inspecionar os comentários textuais via `gh pr view <PR> --comments`.
   - **Protocolo de Fallback para Rate Limit:** Se o CodeRabbit atingir o teto de requisições (`Review limit reached` ou `Review rate limited`), o relatório do debate adversarial local supre a auditoria externa, devendo ser comunicado expressamente ao usuário antes do Gate 2.

---

## 8. Padrões de Código, Estilo e Comunicação Profissional (Invioláveis)
1. **Proibição Total de Emojis**:
   - É estritamente proibido o uso de emojis em qualquer artefato do projeto: títulos de PRs, descrições, mensagens de commit, arquivos de documentação, specs, código-fonte e telas da aplicação.
   - No frontend (Angular), utilize exclusivamente bibliotecas profissionais de ícones vetoriais (ex.: Lucide Icons, FontAwesome ou ícones SVG do Material Design). Jamais utilize emojis como ícones de UI.
2. **Comentários Sóbrios e Concisos**:
   - Proibidos comentários prolixos, narrativos ou redundantes. O código deve ser limpo e autoexplicativo por si só.
   - Comente apenas casos não-óbvios ou decisões críticas de algoritmo, com explicação sucinta de no máximo 1 a 2 linhas (ex.: `// X faz isso`).
3. **Organização e Padronização Extrema**:
   - Manter rigor absoluto na estrutura de diretórios, nomenclatura de rotas, classes, tipos e contratos.
   - Documentação, PRs e commits devem ser estritamente profissionais, objetivos e técnicos.
4. **Padronização de Commits e PRs (Conventional Commits)**:
   - Todo commit e título de PR deve seguir a convenção: `<tipo>(<escopo>): <descrição curta no imperativo>` (ex.: `feat(auth): implementar geracao de jwt`).
   - O escopo de sprint/acadêmico é rastreado via ClickUp, Milestones do GitHub e tags de release (`v*.*.*-sprint*`), nunca no prefixo de commits ou branches.
