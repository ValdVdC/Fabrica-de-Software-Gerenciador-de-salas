# [SPEC-013] Redesign Completo de UX/UI, Design System e Biblioteca de Componentes do SIGAAS

- **Sprint / Fase:** Fase de Auditoria e Especificação SDD — Entrega Final Acadêmica (Frente R3: UX/UI)
- **Disciplina:** Fábrica de Software & Tópicos Avançados em Computação
- **Curso e Turma:** Curso de Bacharelado em Ciência da Computação — Turma 8MB - CC
- **Equipe:** Grupo 31 — SIGAAS
- **Integrantes:** Ewerton Thyago Tavares da Silva (01573977), Wesclei Batista Da Cruz Júnior (01606772), Osvaldo Vasconcelos de Carvalho (01614171), Gabriel Porfírio dos Santos (01591399), Flávio Vecch de Brito Farias (01600988)
- **Autor / Agente:** Squad SIGAAS (Especificação SDD M4)
- **Status:** Draft - Aguardando Gate 1
- **Data de Criação:** 2026-11-27
- **ID ClickUp (Épico/Task):** `[Pendente sync]`
- **Referências Normativas:** `AGENTS.md`, `docs/projeto-gestao-salas-escalas.md`, `docs/specs/template-spec.md`, `.agent/skills/impeccable/SKILL.md`, `.agent/skills/frontend-design/SKILL.md`, `.agent/skills/sigaas-academic-ui/SKILL.md`, `.agent/skills/web-design-guidelines/SKILL.md`, `.agent/skills/diff-slicer/SKILL.md`, `.agent/skills/contract-testing/SKILL.md`

---

## 1. Contexto, Diagnóstico Atual e Decisões de Design

O frontend do SIGAAS (`frontend/src/`) é uma SPA Angular 20.2.0 (`standalone components` + Signals) com 55 arquivos (~3.053 linhas de código de produção em `.ts`/`.html`, 1.220 linhas em `styles.scss` e 1.941 linhas em 19 arquivos `*.spec.ts`). Apesar de atender aos fluxos básicos de sprints anteriores, a auditoria linha a linha evidenciou dívidas severas de UX/UI, divergências de Design System, colisões de estado em formulários inline, ausência de confirmações destrutivas, listas sem paginação, bug *off-by-one* em listagens paginadas, lacunas de CRUDs e desalinhamento de controle de acesso (RBAC) com o backend FastAPI.

### 1.1 Diagnóstico Baseado em Evidências Verificadas

| Categoria | Evidência Verificada (`arquivo:linha`) | Defeito / Impacto Atual |
|---|---|---|
| **Tokens e Variáveis CSS** | `frontend/src/styles.scss:1-25`, `:31-37`; `frontend/src/index.html:2,5` | Define 24 tokens planos (`--color-primary: #0f172a`) incompatíveis com a arquitetura em 3 camadas (`sigaas-academic-ui`), sem `color-scheme: light`, sem fonte `Inter`, sem tokens de *focus-ring*, escala de espaçamento ou `z-index`. `index.html:5` sem acentuação (`Gestao`). |
| **Conflitos e Regras Mortas em `styles.scss`** | `frontend/src/styles.scss:652-680` vs `:1037-1053`; `:398-406` vs `:1165-1173`; `:962-995`; `dashboard.component.ts:131` | `.kpi-card`, `.kpi-label` e `.kpi-value` declarados em duplicidade com conflito de fundo/padding/fonte; `.shell-header` duplicado; `.roles-list`/`.btn-role` mortos; `.table-card-header` usado no Dashboard sem regra CSS correspondente. |
| **Estilos Locais Divergentes e Inline** | `login.component.ts:57-65`; `secretaria.component.ts:151-165`; `aluno.component.ts:37-47`; `grade-horaria.component.ts:51-77`; 20 atributos `style="..."` (`shell.component.ts:201,208`, `admin.component.ts:134,159,162,166,214,267`, `relatorios.component.ts:41,43,45,48,77,79,83`, `historico.component.ts:35,37,41,45,46`) | Quatro componentes redefinem localmente `.panel-card`, `.btn-primary`, `.tabs-nav`, `.badge` e `#0284c7`/`#e0f2fe` fora do tema global, além de 20 atributos `style="..."` espalhados nos templates. |
| **Violações de Contraste WCAG AA, Foco e Movimento** | `styles.scss:11,79,133,139,151,174,199,223-226,317,341,440,500,576,696-714`; `secretaria.component.ts:162-163`; `aluno.component.ts:46`; `grade-horaria.component.ts:70-71` | `#94a3b8` sobre `#ffffff` (2,56:1), `#64748b` sobre `#f1f5f9` (4,34:1) e `#0284c7` sobre `#f8fafc` (3,94:1) falham em WCAG AA (mín. 4,5:1). `.form-input:focus` e `.form-control:focus` aplicam `outline: none` sem `:focus-visible`. Há 8 usos de `transition: all`, zero `@media (prefers-reduced-motion: reduce)`, *ghost cards* (`border` + `box-shadow`), *side-stripes* (`border-left: 3px/4px`), zero `<th scope="col">` e reticências `...` em vez de `…`. |
| **SVGs Brutos e Ausência de `lucide-angular`** | `frontend/package.json:27-37`; 16 `<svg>` de ícone (`shell.component.ts:22-190`, `admin.component.ts:354,369,373,387`, `secretaria.component.ts:134`, `aluno.component.ts:28`, `relatorios.component.ts:24`, `historico.component.ts:24`) + 2 `<svg>` de barra (`dashboard.component.ts:103,119`) | Nenhuma biblioteca de ícones instalada; 16 ícones vetoriais codificados manualmente em HTML e 2 gráficos `<svg>` sem contexto de capacidade. |
| **AISlop e Dívidas Textuais / Código Morto** | `package.json:2`, `angular.json:6,64,67`, `package-lock.json:2,8`, `app.ts:11` (`frontend-init`); `auth.service.ts:121-128` (`setRole` + 24 chamadas em 7 `.spec.ts`); 7 ocorrências `@ufma.br` (`admin.component.spec.ts:26,71,517`, `secretaria.component.spec.ts:29,36,194`, `admin.service.spec.ts:209`); `admin.component.ts:26,157,264` (`"Sprint 05"`, `"(Human-in-the-Loop)"`); `historico.component.ts:20` (`"(LogAlocacao)"`); rótulos `#id` brutos em 7 telas; ausência sistêmica de acentuação pt-BR; opções fixas (`dashboard.component.ts:49-51` `#1/#2/#3`, `admin.component.ts:444` & `secretaria.component.ts:191` `'2026.1'`); símbolos mortos (`AdminService.listarUsuarios`, `SecretariaService.obterTurma`, `HorarioService.listarHorarios`, `GradeHorariaComponent.formatarHorario`) | Violação de `AGENTS.md` §4.8 (`@ufma.br`), exposição de *stub* de autenticação em produção (`setRole()`), cópia interna de sprint/classe no UI, ausência de acentuação profissional e exposição de chaves primárias brutas (`Usuario #1`, `Turma #3`) ao usuário final. |
| **Colisão de Edição Inline e CRUDs Ausentes** | `admin.component.ts:52-80,112-138,424-441,610`; `secretaria.component.ts:36-129`; `turmas.py:107-157`; `usuarios.py:22-211`; `campi.py:16-40` | Em Salas, `@if (salaEmEdicao())` destrói o formulário de criação inline; edição omite `turnos_disponiveis` e `ativo`, e criação fixa `['matutino','vespertino','noturno']` (impedindo `'integral'`). Não existem modais dedicados, nem edição de Turmas no frontend (embora `PATCH /turmas/{id}` exista), nem UI para `Usuários` e `Campi`, e campos FK (`professor_id`, `aluno_id`, `campus_id`) usam `<input type="number">` sem `<label>` em vários trechos. |
| **Ações Destrutivas sem Confirmação** | `admin.component.ts:99,179,368-375,521-545,627-638,705-722`; `secretaria.component.ts:134,285-292`; `aluno.component.ts:28,61-71` | `excluirSala`, `cancelarMatricula` (Secretaria e Aluno), `otimizarAlocacao` com `salvar_no_banco=true` (que sobrescreve `Horario` em `alocacao.py:295`) e `aprovar`/`rejeitarSugestao` executam mutações irreversíveis com um único clique sem diálogo de confirmação. |
| **Listas sem Paginação e Bug *Off-by-One*** | `admin.component.ts:89-108,144-150,239-253,303-391`; `secretaria.component.ts:49-52,74-77,110-113,133-136`; `aluno.component.ts:23-31`; `relatorios.component.ts:145-148`; `historico.component.ts:99` | Nove listagens ignoram `skip`/`limit` (truncando silenciosamente em 50/100 registros no backend ou renderizando centenas de linhas no DOM). `Relatórios` e `Histórico` usam `length >= limit`, mantendo `"Próxima"` habilitado em múltiplos exatos (50/100) e carregando página vazia. |
| **Defeitos do Dashboard** | `dashboard.component.ts:39-235` | Filtro de campus estático (`#1/#2/#3`); ausência de atualização manual e skeletons; barras normalizadas pelo máximo local (`1 aula = 100%`) sem capacidade real nem estado vazio; tabela de auditoria com `#{{ ev.id }}`, `Usuario #{{ ev.usuario_responsavel }}`, `Campus #{{ ev.campus_id }}` e sem link para `/historico`. |
| **Desalinhamentos de RBAC, Rotas e Contratos** | `app.routes.ts:37,43,49,63`; `auth.service.ts:86-93`; `shell.component.ts:42,147`; `admin.component.ts:99,182,422,476`; `horario.service.ts:26` | `AuthService.hasRole('admin')` retorna `true` para `coordenador`, exibindo `Excluir Sala` e `Benchmark` (ambos `ADMIN`-only no backend -> erro 403); `admin`/`coordenador` são bloqueados de `/secretaria`; `secretaria` é bloqueada de `/historico`; rota raiz `''` redireciona para `'admin'` causando banner de acesso negado para outros perfis; `isAuthenticated()` não valida `exp` do JWT; `HorarioRead` declara campo inexistente `status`. |

### 1.2 Decisão Arquitetural: Unificação do Design System

1. **Paleta Canônica Única (Slate + Academic Navy + Semânticos):** Fica formalmente adotada a arquitetura de 3 camadas definida em `.agent/skills/sigaas-academic-ui/references/token-architecture.md` (neutros `Slate #f8fafc..#020617`, identidade institucional `Academic Navy #1e3a8a / #172554 / #0f172a` e semânticos `Emerald`, `Amber`, `Rose`).
2. **Aposentadoria Formal de Tokens Divergentes:** São formalmente aposentadas as cores `#252CEB`, `#4F46E5` e `#7C3AED` especificadas anteriormente em `docs/specs/sprint6-ui-remanejamento-ia.md:22-27`, bem como os tokens planos `--color-*` de `frontend/src/styles.scss:1-25` e o azul avulso `#0284c7`/`#e0f2fe` de `grade-horaria.component.ts:51-77`. Sugestões pendentes da IA passam a usar exclusivamente `Amber` (`--amber-50` / `--amber-800` / `--amber-200`) com ícones `Sparkles`/`Clock3` do `lucide-angular`.
3. **Estratégia de Estilização (`frontend/src/styles.scss`):** Mantém-se SCSS puro estruturado por CSS Custom Properties em 3 camadas no arquivo `frontend/src/styles.scss` (removendo os blocos `styles: [...]` locais dos 4 componentes e os 20 atributos `style="..."`). Essa escolha evita adicionar dependências e `tailwind.config.js` (`.js` contabilizado no limite de diff) e aproveita a isenção explícita de `^frontend/src/styles\.scss$` em `scripts/check_pr_size.py:34`, mantendo cada PR enxuto e focado.

### 1.3 Matriz de Aderência às Skills UX/UI e Política Anti-AISlop

| Diretriz / Skill | Aplicação Normativa Obrigatória no Redesign | Prática Banida / Removida |
|---|---|---|
| **`impeccable`** (`SKILL.md`, `craft-floor.md`, `typeset.md`, `layout.md`, `colorize.md`, `clarify.md`, `harden.md`) | Contraste WCAG AA (`>= 4,5:1` texto/placeholder, `>= 3:1` ícones/foco); elevação declarada **uma única vez** (borda `1px` em cards operacionais **ou** sombra `var(--shadow-overlay)` em overlays); escala de espaçamento base `4px` com mais espaço acima dos títulos que abaixo; medida `65–75ch`; superfície de navegador tematizada (`::selection`, `caret-color`, scrollbars, `:focus-visible`); matriz completa de **8 estados**; resiliência contra textos >100 caracteres, múltiplos cliques e erros `400/401/403/404/409/422/429/500`. | *Ghost cards* (borda 1px + box-shadow juntos), *side-stripe borders* (`border-left > 1px`), cartões aninhados, grade uniforme de cartões idênticos como estrutura principal, *hero-metrics* clichês, *eyebrows* em caixa alta acima de títulos, numeração decorativa `01/02/03`, textos em gradiente, *glassmorphism* decorativo, sombras duras `4px 4px 0`, modais por reflexo. |
| **`frontend-design`** (`SKILL.md`) | Estética sóbria ancorada em gestão acadêmica; família tipográfica única (`Inter` + fallback compatível); linha `< 80ch`; planejamento em 2 passes (tokens + *wireframe* estrutural antes de codar); copy em voz ativa orientada à tarefa do usuário (`"Salvar alterações"`, `"Excluir sala"`). | Rótulos `ALL-CAPS`, strings com ponto mediano decorativo (`A · B · C`), setas textuais em botões, animações *fade-and-slide-up* genéricas em toda seção. |
| **`sigaas-academic-ui`** (`SKILL.md`, `token-architecture.md`, `timetable-matrix-patterns.md`, `conflict-remanejamento-badges.md`) | Angular estritamente como camada de apresentação (zero regra de negócio); `lucide-angular` (`16px`/`20px`, `strokeWidth=2`) e **zero emojis**; grade matricial `M1-M5`, `T1-T5`, `N1-N4` (`Seg–Sáb`) com cabeçalhos fixos (`sticky`) em `>= 1280px` e lista cronológica em `< 1024px`; **clique simples em célula da grade abre `<sigaas-drawer>` lateral read-only**; badges com **3 pistas** (cor WCAG AA + ícone Lucide + texto/ARIA); `truncate` com tooltip em nomes longos e `tabular-nums` em números. | Lógica de alocação ou cálculo de conflito no Angular, emojis em qualquer artefato, indicadores apenas por cor, modal intrusivo para inspeção de célula na grade horária. |
| **`web-design-guidelines`** (`SKILL.md`) | HTML semântico (`<main>`, `<nav>`, `<header>`, `<table>`, `<th scope="col">`, `<button>` vs `<a>`, sem `<div (click)>`); `aria-label` em botões só-ícone; `aria-hidden="true"` em ícones decorativos; `aria-live="polite"` em alertas/toasts; `<label for>` clicáveis com `autocomplete`, `inputmode`, `spellcheck="false"`; `:focus-visible`; `prefers-reduced-motion`; apenas `transform`/`opacity` animados; `text-wrap: balance`; `color-scheme: light`; paginação em listas (`> 50` itens); `…` em vez de `...`; prevenção de CLS e `min-width: 0`. | `outline: none` sem substituto `:focus-visible`, bloqueio de *paste*, `transition: all`, listas sem paginação com centenas de itens, títulos quebrando hierarquia `h1–h6`. |

#### Conciliação Normativa: Modal Dedicado vs. Drawer Lateral (`impeccable` + `sigaas-academic-ui` + R3)

- **`<sigaas-modal>` (Criação e Edição de Entidades):** Aplicado exclusivamente aos fluxos multi-campo de criação e edição (`Salas`, `Equipamentos`, `Vinculação de Equipamento`, `Cursos`, `Disciplinas`, `Turmas`, `Matrículas`, `Usuários`, `Campi`), nos quais o usuário precisa de **foco protegido** e isolamento da listagem de fundo (eliminando a colisão inline existente em `Salas` e removendo formulários permanentes acima das tabelas).
- **`<sigaas-confirm-dialog>` (Confirmação Destrutiva / Crítica):** Aplicado exclusivamente quando há **interrupção obrigatória** por impacto irreversível ou de alto risco (`excluirSala`, `cancelarMatricula`, `otimizarAlocacao` com `salvar_no_banco=true`, aprovação/rejeição de `SugestaoRemanejamento` e desativação de `Usuario`). Conforme `impeccable/reference/clarify.md`, deve nomear explicitamente o objeto alvo, a consequência e o verbo específico no botão primário (ex.: `"Excluir Sala B-204"`, nunca `"OK"` ou `"Sim"` genéricos).
- **`<sigaas-drawer>` (Inspeção Read-Only na Grade Horária):** Mantido exclusivamente para visualização de detalhes de célula, conflito ou alocação nas telas `GradeHoraria` (`Professor` / `Aluno` / consulta de campus), preservando a comparação visual da grade adjacente sem interrupção modal.

---

## 2. Histórias de Usuário e Critérios de Aceite (Gherkin)

### História 1: Identidade Visual Unificada, Tokens 3 Camadas, Ícones Vetoriais e Remoção de AISlop

> **Como** usuário do SIGAAS (Admin, Coordenador, Secretaria, Professor ou Aluno)  
> **Quero** navegar por uma interface coesa com tipografia legível, alto contraste WCAG AA, português corretamente acentuado, ícones vetoriais uniformes e sem textos internos de desenvolvimento  
> **Para que** o sistema transmita confiabilidade institucional e seja acessível em dispositivos desktop e móveis.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Carregamento do Design System unificado sem emojis nem estilos divergentes
  Dado que o usuário autenticado acessa qualquer rota protegida pelo ShellComponent
  Quando a página for renderizada
  Então o documento deve declarar color-scheme light, fonte Inter com fallback compatível e tokens das camadas Primitiva, Semântica e Componente em styles.scss
  E nenhum caractere emoji ou glifo Unicode decorativo deve existir no DOM ou no código-fonte
  E todos os ícones da barra lateral, botões de ação, badges e estados vazios devem usar lucide-angular (16px ou 20px, strokeWidth 2)
  E todos os rótulos, títulos e mensagens devem usar português técnico com acentuação correta e reticências "…"
  E nenhum texto interno de desenvolvimento ("frontend-init", "Sprint 05", "Human-in-the-Loop", "(LogAlocacao)") ou domínio "@ufma.br" deve existir

Cenário: Conformidade de contraste, foco por teclado e preferência de movimento reduzido
  Dado que o usuário navega exclusivamente com a tecla Tab em um formulário ou tabela
  Quando o foco atingir qualquer botão, link, campo ou controle customizado
  Então um anel de foco :focus-visible de alto contraste deve ficar visível sem ser encoberto por cabeçalhos fixos
  E nenhum texto informativo ou placeholder sobre fundo claro deve ter contraste inferior a 4,5:1 (proibido #94a3b8 sobre branco)
  E se o sistema operacional estiver com prefers-reduced-motion: reduce, as transições e animações devem ser suprimidas
```

### História 2: Biblioteca Própria de Componentes Acessíveis (`shared/ui/`)

> **Como** pessoa desenvolvedora e operadora do SIGAAS  
> **Quero** utilizar componentes padronizados de modal, drawer, confirmação, selects pesquisáveis, textareas, campos de data, toggles, paginação, badges e estados vazios  
> **Para que** todos os formulários e listagens mantenham comportamento previsível, acessível por teclado e livre de controles nativos inconsistentes.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Navegação por teclado, focus trap e proteção contra clique duplo em modais
  Dado que o usuário aciona um botão de criação ou edição que abre o <sigaas-modal>
  Quando o modal for exibido
  Então o elemento raiz deve possuir role="dialog", aria-modal="true" e aria-labelledby apontando para o título
  E o foco deve mover-se para o primeiro controle interativo e permanecer restrito ao modal via Tab/Shift+Tab
  E pressionar Escape deve fechar o modal (solicitando descarte se houver alterações não salvas) e restaurar o foco ao botão de origem
  E durante o envio da requisição HTTP o botão de confirmação deve ficar desabilitado com indicador de carregamento, impedindo submissões duplicadas

Cenário: Seleção de entidades via <sigaas-select> pesquisável em vez de ID numérico bruto
  Dado que o formulário modal exige vincular um Campus, Curso, Disciplina, Professor, Aluno, Sala ou Equipamento
  Quando o usuário abrir o componente <sigaas-select>
  Então os itens devem exibir rótulos legíveis (ex.: "CC101 - Algoritmos I" ou "Ana Silva (ana.silva@sigaas.edu)") em vez de input type="number"
  E deve ser possível filtrar opções por digitação e navegar pelas opções com ArrowDown, ArrowUp, Enter e Escape
```

### História 3: Fluxos em Modal Dedicado (Criação e Edição) e Drawer Read-Only

> **Como** Administrador, Coordenador ou Secretário Acadêmico  
> **Quero** criar e editar Salas, Equipamentos, Cursos, Disciplinas, Turmas, Matrículas, Usuários e Campi em modais dedicados acionados por botão explícito  
> **Para que** o formulário de edição nunca sobrescreva o de criação e todas as entidades gerenciáveis tenham fluxo consistente.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Criação e edição de Sala em modal dedicado sem colisão de estado
  Dado que o Administrador ou Coordenador está na aba "Salas"
  Quando clicar no botão "Nova Sala"
  Então um <sigaas-modal> deve abrir com campos rotulados (<label for>) para Campus (se Admin), Bloco, Número, Tipo (incluindo "regular", "laboratorio", "auditorio", "reuniao"), Capacidade e seleção múltipla de turnos disponíveis (incluindo "integral")
  E ao fechar ou salvar o modal e clicar em "Editar" em uma sala existente, um modal distinto de edição deve abrir preenchido com os dados atuais da sala, incluindo "turnos_disponiveis" e alternador "Ativo"
  E a listagem de salas de fundo não deve sofrer colisão ou desaparecimento de controles inline

Cenário: Edição de Turma e gestão de Usuários/Campi com regras hierárquicas de perfil
  Dado que o usuário autorizado acessa a aba "Turmas" na Secretaria ou o módulo de "Usuários"
  Quando acionar "Editar" em uma turma existente
  Então o modal deve permitir alterar "professor_id" (via <sigaas-select> de docentes) e "turno_preferido", enviando PATCH /api/v1/turmas/{id}
  E ao abrir o modal "Novo Usuário", o seletor de perfil deve exibir apenas os perfis permitidos ao perfil autenticado (Secretaria: professor/aluno; Coordenador: secretaria/professor/aluno; Admin: todos)

Cenário: Inspeção não intrusiva de aula na Grade Horária via Drawer lateral
  Dado que o Professor ou Aluno visualiza a Grade Horária
  Quando clicar sobre um card/célula de horário alocado
  Então um <sigaas-drawer> lateral read-only deve abrir exibindo disciplina, docente, localização física completa, horário e capacidade sem bloquear a leitura da grade
```

### História 4: Confirmação Explícita Obrigatória em Ações Destrutivas e Críticas

> **Como** Administrador, Coordenador, Secretário ou Aluno  
> **Quero** confirmar explicitamente toda exclusão, cancelamento ou operação de alto impacto em um diálogo claro antes da execução  
> **Para que** ações irreversíveis nunca ocorram por clique acidental.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Exclusão de Sala com diálogo de confirmação explícito (Admin)
  Dado que o Administrador visualiza uma sala na listagem
  Quando clicar em "Excluir" na linha da sala "Bloco B - 204"
  Então o sistema deve abrir o <sigaas-confirm-dialog> com variante "danger"
  E a mensagem deve identificar "Sala Bloco B - 204" e alertar sobre a remoção irreversível de vínculos de equipamentos
  E o botão destrutivo deve conter o verbo específico "Excluir sala"
  E somente após a confirmação deve disparar DELETE /api/v1/salas/{id}

Cenário: Confirmação antes de sobrescrever horários na Otimização de Alocação
  Dado que o Administrador ou Coordenador configurou o motor de alocação com "Salvar resultado no banco de dados" marcado
  Quando acionar "Executar Alocação"
  Então um <sigaas-confirm-dialog> com variante "warning" deve alertar que os horários existentes do período e campus selecionados serão substituídos
  E se "Salvar resultado no banco de dados" estiver desmarcado (simulação), a execução deve ocorrer sem interrupção modal

Cenário: Confirmação em Cancelar Matrícula, Aprovar/Rejeitar Sugestão IA e Desativar Usuário
  Dado que o usuário aciona "Cancelar Matrícula", "Aprovar Troca", "Rejeitar" (com justificativa em <sigaas-textarea>) ou "Desativar Usuário"
  Quando clicar na ação correspondente
  Então o <sigaas-confirm-dialog> deve exibir os dados do registro afetado e a consequência da operação antes de enviar DELETE /matriculas/{id}, PATCH /sugestoes/{id} ou PATCH /usuarios/{id}
  E no perfil Aluno o fluxo de cancelamento deve respeitar adicionalmente as restrições e justificativas definidas pela especificação de fluxos acadêmicos (M3)
```

### História 5: Paginação, Busca com Debounce e Filtros em Todas as Listas

> **Como** operador acadêmico do SIGAAS  
> **Quero** navegar por listas paginadas com busca reativa e filtros combináveis sem rolagem infinita e sem páginas vazias  
> **Para que** grandes volumes de salas, turmas, matrículas, usuários, sugestões, relatórios e logs permaneçam ágeis e íntegros.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Paginação determinística com técnica limit + 1 corrigindo o bug de última página
  Dado que uma listagem paginada (Salas, Equipamentos, Sugestões, Cursos, Disciplinas, Turmas, Matrículas, Usuários, Campi, Relatórios ou Histórico) consulta a API com pageSize=20 ou 50
  Quando o backend retornar exatamente pageSize registros na última página (sem registros subsequentes)
  Então a requisição deve ter enviado limit = pageSize + 1
  E o frontend deve renderizar os pageSize itens e definir hasNext = false (desabilitando o botão "Próxima")
  E não deve permitir avanço para uma página vazia

Cenário: Busca textual com debounce e paginação local no resultado do motor de alocação
  Dado que o usuário digita um termo de busca em Salas, Turmas ou Usuários
  Quando cessar a digitação por 300ms
  Então uma nova consulta com q e skip=0 deve ser disparada com cancelamento/controle de concorrência
  E na tabela de resultados da Otimização de Alocação, quando houver mais de 25 itens, o <sigaas-pagination> em modo client-side e o filtro "Somente conflitos / sem sala" devem evitar o despejo simultâneo no DOM
```

### História 6: Redesign do Painel Executivo (Dashboard)

> **Como** Administrador, Coordenador ou Secretário  
> **Quero** visualizar no Dashboard indicadores consolidados do campus selecionado dinamicamente, ocupação proporcional à capacidade real e eventos recentes legíveis  
> **Para que** eu identifique gargalos de espaço e acesse diretamente as telas operacionais de resolução.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Seleção dinâmica de campus, carregamento com skeleton e métricas com drill-down
  Dado que um Administrador acessa /dashboard
  Quando a tela inicializar
  Então o filtro de campus deve ser populado dinamicamente via GET /api/v1/campi (nunca com opções estáticas "#1/#2/#3")
  E durante o carregamento os painéis devem exibir placeholders skeleton de dimensões fixas (zero CLS)
  E um botão "Atualizar" deve permitir recarregar os indicadores manualmente com feedback de carregamento
  E os indicadores resumidos e o bloco de sugestões pendentes devem oferecer links de acesso direto para /admin e /secretaria

Cenário: Gráficos de ocupação com escala real e tabela de auditoria sem IDs brutos
  Dado que o Dashboard recebe os dados de ocupação e ocupação por sala (GET /api/v1/relatorios/ocupacao-salas)
  Quando não houver horários alocados no campus selecionado
  Então os gráficos devem exibir um <sigaas-empty-state> claro com ação recomendada em vez de trilhas cinzas zeradas
  E quando houver dados, cada barra deve informar o percentual real em relação à capacidade/horários ofertados com tooltip descritivo
  E a tabela "Últimos Eventos de Auditoria" deve resolver os nomes de usuário e campus via mapas de lookup (com fallback seguro), usar cabeçalhos <th scope="col"> e oferecer link "Ver histórico completo" para /historico
```

### História 7: Alinhamento de RBAC, Rotas e Perfil Docente/Discente

> **Como** usuário autenticado em qualquer perfil do SIGAAS  
> **Quero** acessar apenas e exatamente as rotas e ações autorizadas pelo backend, sendo redirecionado corretamente após o login  
> **Para que** não ocorram erros 403 inesperados nem bloqueios indevidos em módulos permitidos.

#### Critérios de Aceite (Gherkin):
```gherkin
Cenário: Redirecionamento inicial dinâmico e separação entre Admin e Coordenador
  Dado que um usuário com perfil "secretaria", "coordenador", "professor" ou "aluno" acessa a rota raiz "/"
  Quando o roteador avaliar a sessão válida (token JWT não expirado)
  Então deve redirecionar para authService.getHomeRoute() sem exibir banner falso de acesso negado em "/admin"
  E quando um "coordenador" acessar "/admin", os botões exclusivos de "admin" ("Excluir Sala", "Benchmark Científico" e seletor multi-campus) devem permanecer ocultos
  E perfis "admin" e "coordenador" devem acessar "/secretaria" e perfil "secretaria" deve acessar "/historico", espelhando exatamente as permissões do FastAPI
```

---

## 3. Arquitetura, Design System e Contratos Técnicos

### 3.1 Sistema de Tokens em 3 Camadas (`frontend/src/styles.scss`)

Todo o sistema visual é centralizado em `frontend/src/styles.scss` (isento da contagem de linhas por `scripts/check_pr_size.py:34`).

```css
/* Camada 1 — Tokens Primitivos (:root) */
:root {
  color-scheme: light;

  /* Neutros (Slate) */
  --slate-50: #f8fafc;
  --slate-100: #f1f5f9;
  --slate-200: #e2e8f0;
  --slate-300: #cbd5e1;
  --slate-400: #94a3b8;
  --slate-500: #64748b;
  --slate-600: #475569;
  --slate-700: #334155;
  --slate-800: #1e293b;
  --slate-900: #0f172a;
  --slate-950: #020617;

  /* Identidade Institucional (Academic Navy) */
  --navy-50: #eff6ff;
  --navy-200: #bfdbfe;
  --navy-500: #1e3a8a;
  --navy-600: #172554;
  --navy-700: #0f172a;

  /* Semânticos de Estado */
  --emerald-50: #ecfdf5;
  --emerald-200: #a7f3d0;
  --emerald-500: #10b981;
  --emerald-700: #047857;
  --emerald-800: #065f46;

  --amber-50: #fffbeb;
  --amber-200: #fde68a;
  --amber-500: #f59e0b;
  --amber-700: #b45309;
  --amber-800: #92400e;

  --rose-50: #fff1f2;
  --rose-200: #fecdd3;
  --rose-500: #f43f5e;
  --rose-700: #be123c;
  --rose-800: #9f1239;

  /* Tipografia */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;

  /* Escala de Espaçamento (base 4px) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;

  /* Raios e Elevação */
  --radius-sm: 0.375rem;   /* 6px: badges e controles compactos */
  --radius-md: 0.5rem;     /* 8px: inputs, selects e botões */
  --radius-card: 0.75rem;  /* 12px: painéis operacionais e modais */
  --radius-pill: 9999px;   /* somente chips/pills pequenos */
  --shadow-overlay: 0 10px 25px -5px rgba(15, 23, 42, 0.14), 0 4px 10px -4px rgba(15, 23, 42, 0.08);
  --z-sticky: 20;
  --z-dropdown: 40;
  --z-drawer: 60;
  --z-modal: 80;
  --z-toast: 100;

  /* Camada 2 — Tokens Semânticos */
  --bg-app: var(--slate-50);
  --surface-card: #ffffff;
  --surface-subtle: var(--slate-100);
  --surface-overlay: #ffffff;
  --surface-sidebar: var(--slate-900);
  --text-primary: var(--slate-900);
  --text-secondary: var(--slate-600);
  --text-placeholder: var(--slate-500);
  --text-on-dark: var(--slate-300);
  --border-subtle: var(--slate-200);
  --border-control: var(--slate-300);
  --action-primary-bg: var(--navy-500);
  --action-primary-hover: var(--navy-600);
  --action-primary-active: var(--navy-700);
  --focus-ring: 2px solid var(--navy-500);
  --modal-backdrop: rgba(15, 23, 42, 0.55);

  --status-free-bg: var(--emerald-50);
  --status-free-text: var(--emerald-800);
  --status-free-border: var(--emerald-200);
  --status-pending-bg: var(--amber-50);
  --status-pending-text: var(--amber-800);
  --status-pending-border: var(--amber-200);
  --status-conflict-bg: var(--rose-50);
  --status-conflict-text: var(--rose-800);
  --status-conflict-border: var(--rose-200);
  --status-info-bg: var(--navy-50);
  --status-info-text: var(--navy-500);
  --status-info-border: var(--navy-200);

  /* Camada 3 — Tokens de Componente */
  --timetable-header-bg: var(--slate-100);
  --timetable-cell-bg: var(--surface-card);
  --timetable-cell-border: var(--border-subtle);
  --timetable-cell-selected-ring: var(--navy-600);
  --sidebar-nav-item-active-bg: var(--slate-800);
}
```

#### Tabela de Contraste Verificado (WCAG 2.1 AA)

| Uso Semântico | Primeiro Plano | Fundo | Razão Calculada | Critério AA |
|---|---|---|---|---|
| Texto primário em card | `#0f172a` (`--slate-900`) | `#ffffff` | **17,85:1** | Aprovado (>= 4,5:1) |
| Texto primário no app | `#0f172a` (`--slate-900`) | `#f8fafc` (`--slate-50`) | **17,06:1** | Aprovado (>= 4,5:1) |
| Texto secundário em card | `#475569` (`--slate-600`) | `#ffffff` | **7,58:1** | Aprovado (>= 4,5:1) |
| Texto secundário em `--slate-50` | `#475569` (`--slate-600`) | `#f8fafc` (`--slate-50`) | **7,24:1** | Aprovado (>= 4,5:1) |
| Placeholder em input branco | `#64748b` (`--slate-500`) | `#ffffff` | **4,76:1** | Aprovado (>= 4,5:1) |
| Placeholder/texto proibido | `#94a3b8` (`--slate-400`) | `#ffffff` | **2,56:1** | **Banido** (< 4,5:1) |
| Secundário sobre `--slate-100` | `#64748b` (`--slate-500`) | `#f1f5f9` (`--slate-100`) | **4,34:1** | **Banido** (usar `--slate-600`) |
| Botão primário | `#ffffff` | `#1e3a8a` (`--navy-500`) | **10,36:1** | Aprovado (>= 4,5:1) |
| Botão primário hover | `#ffffff` | `#172554` (`--navy-600`) | **14,69:1** | Aprovado (>= 4,5:1) |
| Navegação lateral | `#cbd5e1` (`--slate-300`) | `#0f172a` (`--slate-900`) | **12,02:1** | Aprovado (>= 4,5:1) |
| Badge livre / aprovado | `#065f46` (`--emerald-800`) | `#ecfdf5` (`--emerald-50`) | **7,29:1** | Aprovado (>= 4,5:1) |
| Badge pendente IA | `#92400e` (`--amber-800`) | `#fffbeb` (`--amber-50`) | **6,84:1** | Aprovado (>= 4,5:1) |
| Badge conflito / rejeitado | `#9f1239` (`--rose-800`) | `#fff1f2` (`--rose-50`) | **7,30:1** | Aprovado (>= 4,5:1) |
| Badge alocação padrão | `#1e3a8a` (`--navy-500`) | `#eff6ff` (`--navy-50`) | **9,52:1** | Aprovado (>= 4,5:1) |

#### Regras Mecânicas de Tipografia, Elevação e Superfícies de Navegador
1. **Tipografia:** Fonte `Inter` (pesos `400, 500, 600, 700` com `font-display: swap`); medida de leitura entre `65–75ch`; `text-wrap: balance` em títulos `h1–h3`; `tracking` entre `-0,02em` e `-0,03em` (piso `-0,04em`); piso mínimo de `1rem` (`16px`) em inputs no mobile (`< 768px`) para impedir zoom forçado no iOS Safari; `font-variant-numeric: tabular-nums` obrigatório em horários, capacidades, datas, KPIs e contadores de página.
2. **Elevação e Bordas:** Cards operacionais (`.panel-card`, `.table-card`, `.sugestao-card`) usam exclusivamente `background: var(--surface-card)` + `border: 1px solid var(--border-subtle)` (sem `box-shadow` simultâneo). Overlays flutuantes (`.sigaas-modal-panel`, `.sigaas-drawer-panel`, menus suspensos de `<sigaas-select>`) usam `var(--shadow-overlay)` sem borda competidora. Proibidas bordas laterais `> 1px`.
3. **Superfícies de Navegador e Movimento:** Estilizar `::selection` (`background: var(--navy-500); color: #ffffff`), `caret-color: var(--navy-500)`, `text-underline-offset: 0.2em`, `scrollbar-color: var(--slate-300) var(--slate-100)` e `:focus-visible { outline: var(--focus-ring); outline-offset: 2px; }`. Substituir todo `transition: all` por propriedades explícitas (`background-color`, `border-color`, `transform`, `opacity`) acompanhadas de `@media (prefers-reduced-motion: reduce)`.

### 3.2 Mapeamento Completo de Ícones (`lucide-angular`)

Instalar `lucide-angular` em `frontend/package.json` (`dependencies`) e substituir integralmente os 16 `<svg>` manuais atuais e novos indicadores:

| Local / Contexto | Uso Atual | Ícone `lucide-angular` (`strokeWidth=2`) | Tamanho / ARIA |
|---|---|---|---|
| `ShellComponent` — Administração | `<svg>` manual (`shell.component.ts:22-39`) | `Building2` | `16px`, `aria-hidden="true"` |
| `ShellComponent` — Secretaria Acadêmica | `<svg>` manual (`shell.component.ts:44-59`) | `ClipboardList` | `16px`, `aria-hidden="true"` |
| `ShellComponent` — Grade Horária (Prof./Aluno) | `<svg>` manual (`shell.component.ts:64-99`) | `Calendar` | `16px`, `aria-hidden="true"` |
| `ShellComponent` — Dashboard | `<svg>` manual (`shell.component.ts:109-123`) | `BarChart3` | `16px`, `aria-hidden="true"` |
| `ShellComponent` — Relatórios | `<svg>` manual (`shell.component.ts:127-142`) | `FileText` | `16px`, `aria-hidden="true"` |
| `ShellComponent` — Histórico | `<svg>` manual (`shell.component.ts:150-163`) | `Clock` | `16px`, `aria-hidden="true"` |
| `ShellComponent` — Botão Sair | `<svg>` manual (`shell.component.ts:176-190`) | `LogOut` | `16px`, `aria-hidden="true"` |
| `AdminComponent` — Ganho de Espaço IA | `<svg>` manual (`admin.component.ts:354`) | `ArrowUp` | `16px`, `aria-hidden="true"` |
| `AdminComponent` — Aprovar Troca | `<svg>` manual (`admin.component.ts:369`) | `Check` | `16px`, `aria-hidden="true"` |
| `AdminComponent` — Rejeitar Sugestão | `<svg>` manual (`admin.component.ts:373`) | `X` | `16px`, `aria-hidden="true"` |
| `AdminComponent` — Empty State IA | `<svg>` manual (`admin.component.ts:387`) | `FileText` | `36px`, `aria-hidden="true"` |
| `Secretaria` / `Aluno` — Cancelar Matrícula | `<svg>` manual (`secretaria:134`, `aluno:28`) | `X` | `16px`, `aria-hidden="true"` |
| `Relatórios` / `Histórico` — Exportar CSV | `<svg>` manual (`relatorios:24`, `historico:24`) | `Download` | `16px`, `aria-hidden="true"` |
| Novos Controles & Badges (`shared/ui/`) | Ausentes no repositório atual | `Plus`, `Pencil`, `Trash2`, `Search`, `ChevronLeft`, `ChevronRight`, `ChevronDown`, `AlertTriangle`, `CheckCircle2`, `Clock3`, `Sparkles`, `RefreshCw`, `Users`, `MapPin` | `16px`/`20px` (`32px` em empty states); botões só-ícone com `aria-label` |

### 3.3 Arquitetura da Biblioteca de Componentes (`frontend/src/app/shared/ui/`)

Todos os 11 componentes abaixo são *standalone* (Angular 20 `input()`, `output()`, `model()` e `ControlValueAccessor` onde aplicável), **sem lógica de negócio**, cobrindo a matriz de 8 estados (`default`, `hover`, `active`, `focus-visible`, `disabled`, `loading`, `error`, `empty`):

| Componente / Seletor | Inputs (`input` / `model`) | Outputs (`output`) | Acessibilidade, Teclado e Comportamento |
|---|---|---|---|
| `ModalComponent` (`<sigaas-modal>`) | `aberto: boolean`, `titulo: string`, `largura: 'sm' \| 'md' \| 'lg' = 'md'`, `ocupado: boolean = false`, `temAlteracoes: boolean = false` | `fechado: void` | `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, *focus trap* (`Tab`/`Shift+Tab`), fecha com `Esc` ou clique no *backdrop* (bloqueado quando `ocupado=true`; pede confirmação de descarte se `temAlteracoes=true`), restaura foco ao elemento disparador. |
| `DrawerComponent` (`<sigaas-drawer>`) | `aberto: boolean`, `titulo: string`, `subtitulo?: string` | `fechado: void` | Exclusivo para inspeção read-only na `GradeHoraria`: painel lateral direito com `role="dialog"`, `aria-modal="true"`, `Esc` fecha e restaura foco à célula da grade. |
| `ConfirmDialogComponent` (`<sigaas-confirm-dialog>`) | `aberto: boolean`, `titulo: string`, `mensagem: string`, `detalheObjeto?: string`, `rotuloConfirmar: string`, `rotuloCancelar: string = 'Cancelar'`, `variante: 'danger' \| 'warning' \| 'primary' = 'danger'`, `ocupado: boolean = false` | `confirmado: void`, `cancelado: void` | `role="alertdialog"`, `aria-modal="true"`, ícone `AlertTriangle`, foco inicial seguro no botão cancelar em variantes `danger`; `rotuloConfirmar` sempre com verbo específico + objeto (ex.: `"Excluir sala"`); desabilita botões e exibe estado inflight quando `ocupado=true`. |
| `SelectComponent` (`<sigaas-select>`) | `id: string`, `rotulo: string`, `opcoes: SelectOption<T>[]`, `placeholder: string`, `pesquisavel: boolean = false`, `obrigatorio: boolean = false`, `desabilitado: boolean = false`, `erro?: string \| null`, `dica?: string` | `ControlValueAccessor<T \| null>` + `buscaAlterada: string` | `<label [for]="id">` clicável; controle `<button role="combobox">` ou input pesquisável com `aria-expanded`, `aria-controls`, `aria-invalid`; navegação `ArrowDown`, `ArrowUp`, `Enter`, `Escape`; exibe estado vazio quando busca sem correspondência e trunca textos >100 chars com `title`. |
| `TextareaComponent` (`<sigaas-textarea>`) | `id: string`, `rotulo: string`, `linhas: number = 3`, `maxLength: number = 500`, `placeholder: string`, `obrigatorio: boolean = false`, `erro?: string \| null` | `ControlValueAccessor<string>` | `<label [for]="id">`, contador `tabular-nums` (`{{ valor.length }}/{{ maxLength }}`), `aria-describedby` apontando para contador e erro inline. |
| `DateInputComponent` (`<sigaas-date-input>`) | `id: string`, `rotulo: string`, `min?: string`, `max?: string`, `limpavel: boolean = true`, `erro?: string \| null` | `ControlValueAccessor<string>` | Wrapper estilizado com `<label [for]="id">`, `<input type="date">` (`16px` mobile), botão `"Limpar"` com `aria-label` e erro inline `aria-live="polite"`. |
| `ToggleComponent` (`<sigaas-toggle>`) | `id: string`, `rotulo: string`, `descricao?: string`, `desabilitado: boolean = false` | `ControlValueAccessor<boolean>` | Alvo de clique único englobando `<input type="checkbox" role="switch">` e `<label [for]="id">`, com `:focus-visible`. |
| `PaginationComponent` (`<sigaas-pagination>`) | `paginaAtual: number`, `pageSize: number`, `temProxima: boolean`, `carregando: boolean = false`, `totalExibido: number` | `paginaAlterada: number` | Botões `<button>` com ícones `ChevronLeft`/`ChevronRight`, indicador `tabular-nums` (`Página {{ paginaAtual + 1 }} • {{ totalExibido }} registros`), desabilita controles durante `carregando=true`. |
| `StatusBadgeComponent` (`<sigaas-status-badge>`) | `variante: 'success' \| 'warning' \| 'danger' \| 'info' \| 'neutral'`, `texto: string`, `icone?: 'check' \| 'alert' \| 'clock' \| 'sparkles' \| 'info'` | — | Garante regra de 3 pistas (`cor WCAG AA + ícone Lucide 16px + texto`), sem uso de `text-transform: uppercase` decorativo. |
| `EmptyStateComponent` (`<sigaas-empty-state>`) | `titulo: string`, `descricao: string`, `icone: 'file' \| 'calendar' \| 'search' \| 'building' = 'file'`, `rotuloAcao?: string` | `acaoAcionada: void` | Mensagem orientativa com ícone `32px` (`aria-hidden="true"`) e CTA opcional em voz ativa. |
| `ToastContainerComponent` (`<sigaas-toast>`) | Consome `ToastService` (`mensagens: Signal<ToastItem[]>`) | `dispensar(id)` | Região fixa `aria-live="polite"` para feedbacks de criação, edição, exclusão e erros HTTP, sem sobrepor foco ativo. |

### 3.4 Serviços Frontend, Contratos OpenAPI e Alinhamento RBAC

Conforme `.agent/skills/contract-testing/SKILL.md`, é proibido o uso de `HttpClient.get<any>()` e toda interface TypeScript deve espelhar exatamente os schemas Pydantic v2 do backend.

1. **Banco de Dados / Migrations Alembic:** **Não** — o escopo da SPEC-013 é exclusivamente Frontend consumindo os contratos REST existentes em `/api/v1`. As lacunas de endpoint do backend identificadas na auditoria ficam isoladas em **PRs Opcionais de Extensão Backend** (Seção 3.5), sem bloquear os 9 PRs de Frontend.
2. **Correções de Contrato em Serviços Existentes (Frontend-Only):**
   - `AuthService` (`auth.service.ts`): remover `setRole()` (`:121-128`) do código de produção; validar `exp` do payload JWT (Base64URL) em `isAuthenticated()` (`:86-88`); remover o alias implícito `coordenador -> admin` em `hasRole()` (`:90-93`), introduzindo `isAdminOnly(): boolean` e `canManageCampus(): boolean`; garantir mapeamento consistente para todos os perfis em `getHomeRoute()` (`:95-108`).
   - `HorarioService` (`horario.service.ts:26`): remover o campo inexistente `status: string` de `HorarioRead` (alinhado a `backend/app/schemas/horario.py:26-28`) e manter `carregarMeusHorarios` + `listarHorarios` (para inspeção opcional de grade por campus).
   - `AdminService` (`admin.service.ts`): tipar `SalaCreate.tipo` como `TipoSalaType` (`'regular' | 'laboratorio' | 'auditorio' | 'reuniao'`); adicionar parâmetros `skip?: number, limit?: number` em `listarSalas`, `listarEquipamentos`, `listarUsuarios`; adicionar `criarUsuario(payload: UsuarioCreate)` (`POST /api/v1/usuarios`), `atualizarUsuario(id: number, payload: UsuarioUpdate)` (`PATCH /api/v1/usuarios/{id}`) e `obterUsuario(id: number)` (`GET /api/v1/usuarios/{id}`).
   - `SecretariaService` (`secretaria.service.ts`): adicionar `TurmaUpdate` (`{ professor_id?: number | null; turno_preferido?: TurnoType }`) e `atualizarTurma(turmaId: number, payload: TurmaUpdate)` (`PATCH /api/v1/turmas/{turmaId}`); adicionar `created_at?: string | null` em `Matricula`; adicionar `skip?: number, limit?: number` em `listarCursos`, `listarDisciplinas`, `listarTurmas`, `listarMatriculas`.
   - `AlocacaoService` (`alocacao.service.ts:45`): tipar `AlocacaoBenchmarkRequest.cenario` como `'pequeno' | 'medio' | 'stress'` e usar contador numérico de carregamento.
   - `IaService` (`ia.service.ts:62`): adicionar `skip?: number, limit?: number` em `obterSugestoes`.
   - **Novo `CampusService` (`frontend/src/app/services/campus.service.ts`):** `listarCampi(skip?: number, limit?: number)` (`GET /api/v1/campi`), `obterCampus(id: number)` (`GET /api/v1/campi/{id}`), `criarCampus(payload: CampusCreate)` (`POST /api/v1/campi`) e mapa reativo `campiMap` para resolução de nomes sem `#ID`.
3. **Estratégia de Paginação `limit + 1` (Zero Quebra de Contrato):**
   - Todos os endpoints `GET` listam arrays planos `list[T]` com `limit <= 100` (`sugestoes.py`, `relatorios.py` e `logs.py` possuem `default=50, le=100`).
   - Cada tela paginada solicita `pageSize` (ex.: `20` para CRUDs e `50` para Relatórios/Logs, sempre `<= 99`) com `skip = page * pageSize` e `limit = pageSize + 1`.
   - O componente exibe `items.slice(0, pageSize)` e calcula `temProximaPagina = items.length > pageSize`, eliminando definitivamente o bug `length >= limit` de `RelatoriosComponent:145-148` e `HistoricoComponent:99`.
4. **Resolução de Nomes e Escala Real de Capacidade no Frontend:**
   - Para eliminar rótulos `#ID` em `Shell`, `Dashboard`, `Histórico`, `Secretaria` e `Aluno`, os serviços/componentes autorizados consomem `GET /api/v1/campi`, `GET /api/v1/usuarios`, `GET /api/v1/cursos`, `GET /api/v1/disciplinas` e `GET /api/v1/turmas` via mapas de lookup (`Map<number, string>`), mantendo fallback seguro `#ID` apenas quando o item ultrapassar o recorte carregado.
   - No `Dashboard`, a ocupação por turno/dia é contextualizada com os dados de `GET /api/v1/relatorios/ocupacao-salas?limit=100` (autorizado para `admin`, `coordenador` e `secretaria` em `relatorios.py:35`), calculando capacidade instalada do campus e evitando a distorção atual onde `1 aula = 100%`.
5. **Matriz de Alinhamento RBAC (Frontend <-> Backend):**
   - `/` -> redirecionamento dinâmico via `canActivate` para `authService.getHomeRoute()`.
   - `/login` -> redirecionamento automático para `getHomeRoute()` se já autenticado com token não expirado.
   - `/secretaria` -> `roles: ['admin', 'coordenador', 'secretaria']` (`app.routes.ts:49` e `ShellComponent`).
   - `/historico` -> `roles: ['admin', 'coordenador', 'secretaria']` (`app.routes.ts:37` e `ShellComponent`).
   - `/admin` -> `roles: ['admin', 'coordenador']`, porém `Excluir Sala`, `Benchmark Científico`, aba `Campi` e seletor multi-campus renderizados **exclusivamente** quando `authService.isAdminOnly() === true`.
   - `/usuarios` (ou aba dedicada em `/admin` + atalho para `secretaria`) -> acessível a `admin`, `coordenador` e `secretaria` conforme `usuarios.py:30,71,136`, com `<sigaas-select>` de `perfil` filtrado dinamicamente pela hierarquia BFLA (`secretaria -> ['professor','aluno']`; `coordenador -> ['secretaria','professor','aluno']`; `admin -> todos`).
   - `/professor` -> além da `GradeHoraria` (com `<sigaas-drawer>` read-only), exibe lista read-only de turmas e alunos matriculados via `GET /api/v1/matriculas` (já autorizado a `PROFESSOR` em `matriculas.py:24-32`).

### 3.5 Fronteira Explícita: PRs Frontend-Only vs. Dependências Opcionais de Backend

| Escopo | Operações Cobertas | Status no Backend Atual | Tratamento na SPEC-013 |
|---|---|---|---|
| **Frontend-Only (Imediato)** | `Salas` (CRUD completo), `Equipamentos` (`GET`/`POST` + `POST /salas/{id}/equipamentos`), `Cursos` (`GET`/`POST`), `Disciplinas` (`GET`/`POST`), `Turmas` (`GET`/`POST`/`PATCH`), `Matrículas` (`GET`/`POST`/`DELETE`), `Usuários` (`GET`/`POST`/`PATCH`), `Campi` (`GET`/`POST`), `Alocação`, `Sugestões`, `Dashboard`, `Relatórios`, `Logs`, `Horários`. | Todos os endpoints já existem e estão em produção em `/api/v1`. | Cobertos integralmente nos **PRs 1 a 9** da Seção 4 sem exigir alteração de backend. |
| **Dependência Backend A (Segurança / Campi — alinhada a M3)** | `PATCH/DELETE /api/v1/campi/{id}` + `require_role(ADMIN)` em `campi.py`. | `campi.py` não possui `PATCH`/`DELETE` nem guard de papel. | UI de criação/listagem de `Campi` entrega no PR 7; botões `Editar`/`Desativar` Campus ficam habilitados apenas após PR de Backend correspondente (M3/extensão). |
| **Dependência Backend B (Equipamentos e Vínculos de Sala)** | `PATCH/DELETE /api/v1/equipamentos/{id}`, `GET /api/v1/salas/{id}/equipamentos`, `DELETE /api/v1/salas/{id}/equipamentos/{equipamento_id}`, auth em `GET /equipamentos`. | `equipamentos.py` tem só `GET`/`POST`; `salas.py` tem só `POST /salas/{id}/equipamentos`. | No PR 5, a UI exibe criação de equipamento e associação à sala com visualização/atualização de quantidade; edição/desvinculação aguarda esta extensão de backend. |
| **Dependência Backend C (Opcional — Cursos/Disciplinas + Enriquecimento)** | `PATCH/DELETE` e `q` em `cursos.py`/`disciplinas.py`; campos nominais diretos em `LogRead` e `capacidade_total` em `DashboardResumoRead`. | `cursos.py`/`disciplinas.py` têm só `GET`/`POST` sem `q`. | Mitigado no frontend via lookup maps e `/relatorios/ocupacao-salas`; edição/exclusão de Cursos e Disciplinas aguarda este PR opcional. |

---

## 4. Fatiamento em PRs Incrementais (`<= 300-400` LOC de Produção)

Em estrita conformidade com `AGENTS.md` §6.4, `.agent/skills/diff-slicer/SKILL.md` e `scripts/check_pr_size.py`:
- **Arquivos isentos da contagem:** `frontend/src/styles.scss`, `*.spec.ts`, `*.json` (`package.json`, `angular.json`, `package-lock.json`) e `docs/`.
- **Arquivos contabilizados:** adições líquidas (`+additions`) em `.ts` de produção e `.html` (incluindo quaisquer novos componentes). Não serão criados novos arquivos `.scss` parciais para que toda a folha de estilos permaneça em `frontend/src/styles.scss`.
- Todo PR abaixo compila isoladamente (`ng build --configuration production`), passa no Prettier (`npm run format:check`) e mantém 100% da suíte Jasmine/Karma verde (`npx ng test --no-watch --browsers=ChromeHeadless`).

| PR | Branch | Escopo Atômico | Arquivos Alvo Principais | LOC Prod. Est. | Commit (Conventional Commits) | Dep. | Gate 2 |
|---|---|---|---|---|---|---|---|
| **PR 1** | `feat/ui-tokens-shell-rbac` | Instalar `lucide-angular`, remover `frontend-init`, unificar tokens 3 camadas/WCAG AA/fontes em `styles.scss` + `index.html`, corrigir `AuthService` (`exp`, remover `setRole()`, `isAdminOnly()`), rotas (`/` dinâmico, `/secretaria`, `/historico`) e `ShellComponent` (Lucide, diacritics, campus dinâmico via fallback inicial). | `package.json` (isento), `angular.json` (isento), `styles.scss` (isento), `index.html`, `app.ts`, `auth.service.ts`, `auth.guard.ts`, `role.guard.ts`, `app.routes.ts`, `shell.component.ts` (+ `.spec.ts` isentos) | **~240 LOC** | `feat(ui): unificar tokens 3 camadas, lucide-angular e alinhar rbac no shell` | — | Sim |
| **PR 2** | `feat/ui-shared-overlays` | Criar núcleo de overlays e feedback em `shared/ui/`: `ModalComponent`, `DrawerComponent`, `ConfirmDialogComponent`, `StatusBadgeComponent`, `EmptyStateComponent`, `ToastService` + `ToastContainerComponent`. | `frontend/src/app/shared/ui/{modal,drawer,confirm-dialog,status-badge,empty-state,toast}/*` (+ `.spec.ts` isentos) | **~320 LOC** | `feat(ui): adicionar componentes compartilhados de modal, drawer, confirmacao e badges` | PR 1 | Não |
| **PR 3** | `feat/ui-shared-forms-pagination` | Criar controles próprios acessíveis e paginação em `shared/ui/`: `SelectComponent` (pesquisável + CVA), `TextareaComponent`, `DateInputComponent`, `ToggleComponent`, `PaginationComponent` (`limit+1`). | `frontend/src/app/shared/ui/{select,textarea,date-input,toggle,pagination}/*` (+ `.spec.ts` isentos) | **~330 LOC** | `feat(ui): adicionar componentes acessiveis de formulario e paginacao` | PR 1, PR 2 | Não |
| **PR 4** | `feat/ui-login-dashboard-redesign` | Criar `CampusService`, limpar `LoginComponent` (remover `styles: [...]`, redirect autenticado, acessibilidade) e redesenhar `DashboardComponent` (campi dinâmicos, refresh, skeletons, escala real via `ocupacao-salas`, drill-down, nomes resolvidos e link `/historico`). | `campus.service.ts`, `login.component.ts`, `dashboard.component.ts` (+ `.spec.ts` isentos) | **~310 LOC** | `feat(ui): redesenhar login e dashboard com campi dinamicos e acessibilidade` | PR 1, PR 2, PR 3 | Não |
| **PR 5** | `feat/ui-admin-salas-equipamentos` | Extrair `SalasTabComponent` e `EquipamentosTabComponent` de `AdminComponent`: modais de criação/edição de Salas (`turnos_disponiveis` com `'integral'`, `ativo`), `excluirSala` apenas `isAdminOnly()` com `<sigaas-confirm-dialog>`, modais de Equipamentos/Vínculo, seletor de campus e paginação `limit+1`. | `admin.service.ts`, `admin.component.ts`, `pages/admin/tabs/salas-tab.component.ts`, `pages/admin/tabs/equipamentos-tab.component.ts` (+ `.spec.ts` isentos) | **~340 LOC** | `feat(ui): modularizar salas e equipamentos em modais dedicados com paginacao` | PR 2, PR 3, PR 4 | Sim |
| **PR 6** | `feat/ui-admin-alocacao-ia` | Extrair `AlocacaoTabComponent` e `RemanejamentoTabComponent`: confirmação ao `salvar_no_banco=true`, `Benchmark` restrito a `isAdminOnly()`, paginação local (25 itens) + filtro de conflitos na alocação, `<sigaas-textarea>` + confirmação e paginação `limit+1` em sugestões IA, remoção de `"Sprint 05"`/`"(Human-in-the-Loop)"`. | `alocacao.service.ts`, `ia.service.ts`, `admin.component.ts`, `pages/admin/tabs/alocacao-tab.component.ts`, `pages/admin/tabs/remanejamento-tab.component.ts` (+ `.spec.ts` isentos) | **~310 LOC** | `feat(ui): adicionar confirmacoes, paginacao e acessibilidade em alocacao e ia` | PR 5 | Sim |
| **PR 7** | `feat/ui-usuarios-campi-crud` | Implementar CRUD de `Usuários` (`GET/POST/PATCH` com hierarquia BFLA em `<sigaas-select>`, busca `q`, filtro campus, paginação `limit+1`, confirmação de desativação) e gestão de `Campi` (`GET/POST` em modal dedicado para `admin`) via `UsuariosCampiTabComponent` e rota/atalho autorizado. | `admin.service.ts`, `campus.service.ts`, `app.routes.ts`, `shell.component.ts`, `pages/admin/tabs/usuarios-campi-tab.component.ts` (+ `.spec.ts` isentos) | **~320 LOC** | `feat(ui): implementar gestao de usuarios com bfla hierarquico e cadastro de campi` | PR 4, PR 6 | Sim |
| **PR 8** | `feat/ui-secretaria-modais-turmas` | Refatorar `SecretariaComponent`: remover `styles: [...]`, mover Cursos/Disciplinas/Turmas/Matrículas para `<sigaas-modal>`, adicionar `atualizarTurma` (`PATCH /turmas/{id}`), trocar `professor_id`/`aluno_id` numéricos por `<sigaas-select>` pesquisável, resolver nomes, adicionar paginação `limit+1` e `<sigaas-confirm-dialog>` em `cancelarMatricula`. | `secretaria.service.ts`, `secretaria.component.ts` (+ modais/subcomponentes se necessário, `.spec.ts` isentos) | **~340 LOC** | `feat(ui): migrar secretaria para modais, edicao de turmas e seletores pesquisaveis` | PR 2, PR 3, PR 4 | Sim |
| **PR 9** | `feat/ui-grade-aluno-relatorios-logs` | Padronizar `GradeHoraria` (remover `styles: [...]` e `#0284c7`, matriz `M1-N4` + `<sigaas-drawer>` read-only, corrigir `HorarioRead`), `Professor` (lista read-only de matriculados), `Aluno` (nomes legíveis + confirmação alinhada a M3 + paginação), `Relatórios` & `Histórico` (corrigir `temProximaPagina` com `limit+1`, remover inline `style="..."` e `"(LogAlocacao)"`, `<sigaas-select>`/`<sigaas-date-input>`, nomes resolvidos, Lucide `Download`). | `horario.service.ts`, `grade-horaria.component.ts`, `professor.component.ts`, `aluno.component.ts`, `relatorios.component.ts`, `historico.component.ts` (+ `.spec.ts` isentos) | **~350 LOC** | `feat(ui): padronizar grade horaria com drawer, aluno, relatorios e historico` | PR 2, PR 3, PR 4 | Sim |

---

## 5. Plano de Testes TDD (RED / GREEN / REFACTOR)

Toda alteração de frontend segue o ciclo **RED -> GREEN -> REFACTOR** com `Jasmine/Karma` (`npx ng test --no-watch --browsers=ChromeHeadless`), `Prettier` (`npm run format:check`) e build de produção (`npm run build -- --configuration production`), conforme `.github/workflows/ci.yml:68-73,145-153`.

### 5.1 Saneamento Obrigatório de Testes Existentes (Atomicamente no PR 1 e seguintes)
1. **Substituição de `@ufma.br` por `@sigaas.edu`:** Atualizar as 7 ocorrências verificadas em `admin.component.spec.ts:26,71,517`, `secretaria.component.spec.ts:29,36,194` e `admin.service.spec.ts:209` (no PR 1 ou respectivo PR de componente, garantindo zero ocorrências no repositório).
2. **Remoção de `AuthService.setRole()` (24 chamadas em 7 `.spec.ts`):** Criar utilitário de teste em `frontend/src/app/testing/auth-test-helper.ts` (ou helper local nos specs, sem expor no bundle de produção) para semear `localStorage` (`sigaas_token` com payload JWT válido e `exp` futuro + `sigaas_user`), atualizando `role.guard.spec.ts`, `shell.component.spec.ts`, `dashboard.component.spec.ts`, `components.spec.ts`, `integration-flow.spec.ts` e `auth.service.spec.ts` no PR 1.
3. **Atualização de Asserções RBAC Legadas:** Atualizar `role.guard.spec.ts:47-50,81-100` e `components.spec.ts:58-77,158-163` para refletir o alinhamento com o backend (`coordenador` acessa `/secretaria`, `secretaria` acessa `/historico`, `coordenador` não vê `Excluir Sala` nem `Benchmark`).

### 5.2 Suíte de Testes por Camada (Fase RED antes da Implementação)

- **Testes Unitários de Biblioteca `shared/ui/*.spec.ts`:**
  - `modal.component.spec.ts`: valida `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, fechamento por `Esc`, bloqueio de fechamento quando `ocupado=true`, prevenção de duplo clique e restauração de foco.
  - `confirm-dialog.component.spec.ts`: valida `role="alertdialog"`, exibição de `detalheObjeto`, verbo específico no botão primário e emissão exclusiva de `confirmado` / `cancelado`.
  - `select.component.spec.ts`: valida associação `<label for>`, abertura/navegação por teclado (`ArrowDown`/`Enter`/`Escape`), filtragem pesquisável em listas `> 50` opções e truncamento de strings com `120+` caracteres.
  - `pagination.component.spec.ts`: valida cálculo `temProxima` via técnica `limit + 1` (ex.: `50` itens retornados com `pageSize=50` mantém `"Próxima"` **desabilitado**; `51` itens exibe `50` e habilita `"Próxima"`).
  - `status-badge.component.spec.ts` & `drawer.component.spec.ts`: validam presença simultânea de ícone Lucide + texto (nunca apenas cor) e abertura/fechamento não destrutivo do drawer.
- **Testes de Contrato HTTP (`HttpTestingController`):**
  - `campus.service.spec.ts`: valida `GET /api/v1/campi`, `POST /api/v1/campi` e tratamento de erro `401/403/422`.
  - `admin.service.spec.ts`, `secretaria.service.spec.ts`, `ia.service.spec.ts`, `horario.service.spec.ts`: validam envio de `skip` e `limit = pageSize + 1`, remoção de `status` em `HorarioRead`, payload exato de `PATCH /turmas/{id}`, `POST /usuarios`, `PATCH /usuarios/{id}` e propagação de erros `400/401/403/404/409/422/500`.
  - `auth.service.spec.ts`: valida rejeição de token com `exp` expirado em `isAuthenticated()`, separação `isAdminOnly()` vs `canManageCampus()` e redirecionamento dinâmico em `getHomeRoute()`.
- **Testes de Comportamento, Acessibilidade e Hardening por Página:**
  - Garantir em cada página (`Shell`, `Login`, `Dashboard`, `Salas`, `Equipamentos`, `Alocação`, `Remanejamento`, `Usuários`, `Secretaria`, `GradeHoraria`, `Aluno`, `Relatórios`, `Histórico`):
    - Zero emojis (`!/[\u{1F300}-\u{1FAFF}]/u.test(textContent)`) e zero ocorrências de `#id` cru onde há lookup disponível.
    - Presença de `<th scope="col">` nas tabelas e `<label for>` nos campos de formulário.
    - Execução de ações destrutivas somente após confirmação em `<sigaas-confirm-dialog>`.
    - Verificação `npm run format:check` e `npm run build -- --configuration production` verdes ao final de cada PR.

---

## 6. Decomposição ClickUp, Debate Adversarial e Portões (Gate 1 / Gate 2)

1. **Sincronização ClickUp (após aprovação do Gate 1):**
   - Executar `python scripts/clickup_sync.py sync-spec docs/specs/spec-redesign-ux-ui.md` para registrar épico e subtarefas correspondentes aos PRs 1 a 9.
2. **Gate 1 (Aprovação Humana da Especificação):**
   - Nenhuma linha de código de produção em `frontend/` deve ser alterada antes da aprovação formal desta `SPEC-013` pelo usuário/PO.
3. **Ciclo de Execução por PR:**
   - Criar branch semântica a partir da `main` (ex.: `git checkout -b feat/ui-tokens-shell-rbac`).
   - Executar ciclo TDD (`RED -> GREEN -> REFACTOR`), validar `python scripts/check_pr_size.py origin/main 400`, `npm run format:check`, `npx ng test --no-watch --browsers=ChromeHeadless` e `npm run build -- --configuration production`.
4. **Debate Adversarial Multi-Agente Pré-PR e Re-Review em Loop (`AGENTS.md` §7.1):**
   - Submeter cada PR ao comitê (`advocate-mapper`, `adversary-breaker`, `adversary-security`, `adversary-compliance` e `debate-arbiter`), verificando zero emojis, zero lógica de negócio no Angular, acessibilidade WCAG AA, contratos OpenAPI e `<= 400` LOC de produção. Havendo qualquer veto ou apontamento crítico, corrigir e re-executar o ciclo completo de Re-Review sobre o `git diff origin/main...HEAD` até consenso unânime.
5. **CodeRabbit AI, Gate 2 e Merge (`AGENTS.md` §6.3 e §7.2):**
   - Abrir PR via `gh pr create --base main`, inspecionar todos os checks e comentários textuais com `gh pr view <PR> --comments` (aplicando o protocolo de fallback caso ocorra rate limit do CodeRabbit) e aguardar aprovação humana (**Gate 2**) antes de concluir com `gh pr merge <PR> --squash --delete-branch`.
