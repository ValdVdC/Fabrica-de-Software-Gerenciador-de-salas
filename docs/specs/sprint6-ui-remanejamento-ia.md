# [SPEC-007] Interface de Usuario para Remanejamento IA e Navegacao Global

- **Sprint:** Sprint 06 - Terceiro Modulo Funcional
- **Autor / Responsavel:** Gabriel Porfirio (Dev Frontend) & Squad SIGAAS
- **Status:** Aprovado (Gate 1 Concluido)
- **Data de Criacao:** 2026-10-15
- **Prazo de Entrega:** 17/10/2026
- **ID ClickUp (Epico/Task):** #CU-SPRINT06-UI-REMANEJAMENTO-IA
- **Referencia Backend:** SPEC-006 (`docs/specs/sprint6-ia-remanejamento-e-aprimoramento.md`)

---

## 1. Contexto e Objetivos

Na Sprint 06, o SIGAAS implementa o modelo de Inteligencia Artificial Preditiva de Absenteismo Discente e Otimizacao de Espacos Fisicos. Conforme a regra de ouro inviolavel da arquitetura (definida no AGENTS.md), o modelo de IA e os jobs em lote **nunca alteram diretamente a grade de horarios**. Toda recomendacao de otimizacao e persistida como uma sugestao pendente (`sugestao_remanejamento`), demandando aprovacao humana explicita (*Human-in-the-Loop*).

Este card, sob responsabilidade de Gabriel Porfirio (Dev Frontend), tem como objetivo principal implementar a interface grafica no Angular para visualizacao operacional, comparativo de ganhos de capacidade e acao de aprovacao ou rejeicao humana das sugestoes de remanejamento da IA, alem de unificar o cabecalho superior e aprimorar a consistencia de navegacao no sistema.

### 1.1 Diretrizes do Design System Anti-Vibe Coding
A implementacao deve gerar uma interface estritamente profissional, corporativa e sobria. Esta expressamente proibido o uso de caracteristicas de "vibe coding" frequentemente associadas a IA, tais como elementos neon, glassmorphism (fundos translucidos com desfoque), dark-mode nao solicitado, sombras brilhantes (glow), gradientes complexos ou layouts futuristas. A interface deve ser utilitaria, focada em legibilidade de dados e com componentes bem definidos.

As variaveis CSS (`styles.scss`) adotam obrigatoriamente a paleta institucional:
- **Principal (`#252CEB`)**: Uso restrito a acoes afirmativas primarias (ex: botao "Aprovar Troca"), links principais e cabecalhos de destaque.
- **Secundaria (`#4F46E5`)**: Uso em acoes secundarias, contornos (borders) de botoes outline, iconografia de menu e estados de hover (`:hover`).
- **Destaque (`#7C3AED`)**: Uso exclusivo para identificar componentes que provem da IA (ex: Badges de probabilidade de absenteismo, tags de "Recomendacao").
- **Fundo (`#F8FAFC`)**: Background geral da aplicacao e area externa aos cards. Para os cards em si, utilizar fundo branco `#FFFFFF` com sombra utilitaria leve (`box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #E2E8F0;`).
- **Texto (`#0F172A`)**: Cor absoluta para textos corporais, titulos, rotulos de formularios e dados da tabela, garantindo altissimo contraste e acessibilidade.

### 1.1 Metas Especificas
1. **Servico HTTP Reativo (`IaService`)**:
   - Comunicacao tipada com a API REST do FastAPI (`/api/v1/sugestoes`).
   - Gestao reativa de estado atraves de Signals (`sugestoes`, `isLoading`, `errorMessage`, `sucessoMessage`).
   - Tratamento defensivo universal de falhas HTTP (400, 401, 403, 404, 409) com mensagens amigaveis em conformidade com as devolutivas da Pre-Banca.
2. **Painel Operacional no Admin (`AdminComponent`)**:
   - Nova aba de navegacao interna: `'remanejamento'` (rotulo: "Remanejamento IA").
   - Cards visuais de alto contraste contendo identificacao da turma/disciplina, probabilidade estimada de absenteismo, comparativo sala atual vs recomendada e calculo de economia de vagas.
   - Botoes de acao `[Aprovar Troca]` e `[Rejeitar]` com campo de justificativa e prevencao de clique duplo (`disabled=isLoading()`).
3. **Cabecalho Superior Unificado e Navegacao Global (`ShellComponent`)**:
   - Exibicao padronizada de Nome do Usuario, Perfil de Acesso e Campus Ativo.
   - Atalhos de navegacao contextuais e atalho de encerramento de sessao (`Sair`).
4. **Conformidade Normativa e Rigor Visual**:
   - Zero emojis em qualquer string, icone, template, estilo ou teste automatizado.
   - Nenhuma regra de negocio ou calculo pesado no frontend (apenas projecao e chamada de API).
   - Governanca de Diff: particionamento em 2 PRs atômicos com `<= 300 a 400 linhas` de codigo de producao.
   - Cobertura de 100% de sucesso nos testes unitarios Jasmine/Karma.

---

## 2. Historias de Usuario e Criterios de Aceite (Gherkin)

### Historia 1: Listagem Reativa de Sugestoes de Remanejamento
> **Como** Coordenador de Campus ou Administrador Geral  
> **Quero** visualizar a lista de turmas com sugestao de remanejamento geradas pela IA  
> **Para que** eu possa avaliar o risco de absenteismo e as oportunidades de realocacao para salas menores.

#### Criterios de Aceite:
```gherkin
Cenario: Carregamento bem-sucedido das sugestoes na aba de remanejamento
  Dado que o usuario autenticado (Admin ou Coordenador) acessa a aba "Remanejamento IA"
  Quando o componente inicializar a consulta ao IaService
  Entao o signal isLoading deve permanecer true durante o carregamento
  E ao concluir com sucesso o signal sugestoes deve conter a lista ordenada por probabilidade de absenteismo
  E cada card deve exibir: Turma, Codigo e Nome da Disciplina, Sala Atual (Capacidade), Sala Sugerida (Capacidade) e Economia de Vagas
  E o badge de probabilidade deve indicar a porcentagem formatada (ex: 78% de risco de ociosidade)

Cenario: Estado vazio de sugestoes
  Dado que nao existem sugestoes de remanejamento pendentes para o campus
  Quando a consulta for concluida
  Entao uma mensagem profissional deve ser exibida informando "Nenhuma sugestao de remanejamento pendente para este campus."
  E nenhum emoji deve estar presente na mensagem ou tela
```

### Historia 2: Aprovacao Humana de Remanejamento (Human-in-the-Loop)
> **Como** Coordenador ou Administrador  
> **Quero** aprovar a troca de sala sugerida pela IA  
> **Para que** a nova sala seja efetivamente gravada no horario da turma e o espaco anterior seja liberado.

#### Criterios de Aceite:
```gherkin
Cenario: Aprovacao confirmada com sucesso
  Dado uma sugestao com status pendente selecionada no painel
  Quando o usuario clicar no botao "Aprovar Troca"
  Entao os botoes do card devem ficar desativados (disabled=isLoading()) impedindo cliques duplicados
  E uma requisicao PATCH /api/v1/sugestoes/{id} deve ser enviada com status="aprovado"
  E ao receber resposta 200 OK, a sugestao deve ser atualizada na interface
  E uma mensagem de sucesso profissional deve ser exibida
  E o estado isLoading deve retornar para false

Cenario: Bloqueio por conflito de ocupacao (HTTP 409 Conflict)
  Dado que a sala sugerida foi ocupada por outra turma antes da confirmacao
  Quando o usuario tentar aprovar a sugestao
  Entao a API retornara status 409 Conflict
  E o signal errorMessage deve exibir "Sala sugerida nao esta mais disponivel no horario especificado"
  E nenhum travamento de tela ou crash de JavaScript deve ocorrer
```

### Historia 3: Rejeicao Motivada de Remanejamento
> **Como** Coordenador ou Administrador  
> **Quero** rejeitar uma recomendacao da IA fornecendo uma justificativa  
> **Para que** a alocacao original seja mantida e o historico registre o motivo do descarte.

#### Criterios de Aceite:
```gherkin
Cenario: Rejeicao de sugestao com justificativa
  Dado uma sugestao pendente
  Quando o usuario informar a justificativa e acionar o botao "Rejeitar"
  Entao uma requisicao PATCH /api/v1/sugestoes/{id} deve ser despachada com status="rejeitado" e justificativa preenchida
  E a grade de horarios nao sofrera alteracao
  E o card deve indicar o encerramento do processo com status rejeitado
```

### Historia 4: Cabecalho Superior Unificado e Navegacao Consistente
> **Como** Qualquer Usuario Autenticado no SIGAAS  
> **Quero** visualizar no cabecalho superior meu nome, perfil e campus ativo, com atalhos claros entre as telas  
> **Para que** eu tenha contexto imediato de acesso e possa navegar sem ambiguidade.

#### Criterios de Aceite:
```gherkin
Cenario: Renderizacao do cabecalho unificado
  Dado um usuario autenticado com sessao ativa
  Quando qualquer tela filha do ShellComponent for carregada
  Entao o cabecalho superior deve exibir o Nome do Usuario, Perfil formatado e Identificacao do Campus
  E deve conter atalhos rapidos para as areas autorizadas ao perfil do usuario
  E o botao "Sair" deve encerrar a sessao e redirecionar para a rota /login
```

---

## 3. Arquitetura Tecnica e Contratos OpenAPI ↔ Angular

### 3.1 Contrato da API REST (FastAPI)
- `GET /api/v1/sugestoes?status=pendente`:
  - Retorno: `SugestaoRemanejamentoRead[]`
- `PATCH /api/v1/sugestoes/{id}`:
  - Payload: `{ "status": "aprovado" | "rejeitado", "justificativa": string | null }`
  - Retorno: `SugestaoRemanejamentoRead`
  - Status HTTP possiveis: 200 (Sucesso), 400 (Ja processada), 401 (Nao autenticado), 403 (Nao autorizado), 404 (Nao encontrada/BOLA), 409 (Conflito de horario).

### 3.2 Modelos e Interfaces TypeScript (`frontend/src/app/services/ia.service.ts`)
```typescript
export type StatusSugestaoType = 'pendente' | 'aprovado' | 'rejeitado';

export interface SugestaoRemanejamento {
  id: number;
  horario_id: number;
  sala_atual_id: number;
  sala_sugerida_id: number;
  motivo: string;
  justificativa?: string | null;
  status: StatusSugestaoType;
  aprovado_por?: number | null;
  criado_em: string;
  atualizado_em: string;
  prob_ausencia?: number | null;
  turma_id?: number | null;
  disciplina_codigo?: string | null;
  disciplina_nome?: string | null;
  sala_atual_bloco?: string | null;
  sala_atual_numero?: string | null;
  sala_atual_capacidade?: number | null;
  sala_sugerida_bloco?: string | null;
  sala_sugerida_numero?: string | null;
  sala_sugerida_capacidade?: number | null;
  dia_semana?: number | null;
  hora_inicio?: string | null;
  hora_fim?: string | null;
  campus_id?: number | null;
}

export interface SugestaoDecisaoPayload {
  status: 'aprovado' | 'rejeitado';
  justificativa?: string;
}
```

### 3.3 Estrutura Reativa do `IaService`
- Signals gerenciados:
  - `readonly sugestoes = signal<SugestaoRemanejamento[]>([])`
  - `readonly isLoading = signal<boolean>(false)`
  - `readonly errorMessage = signal<string | null>(null)`
  - `readonly sucessoMessage = signal<string | null>(null)`
- Metodos publicos:
  - `obterSugestoes(status?: string): Observable<SugestaoRemanejamento[]>`
  - `aprovarSugestao(id: number, justificativa?: string): Observable<SugestaoRemanejamento>`
  - `rejeitarSugestao(id: number, justificativa?: string): Observable<SugestaoRemanejamento>`
  - `limparMensagens(): void`

---

## 4. Estrategia de Fatiamento Atomico (Diff Slicer <= 400 linhas)

Para manter estrita conformidade com a regra de diff de no maximo 300 a 400 linhas de codigo de producao (verificado por `python scripts/check_pr_size.py`), a implementacao e decomposta em 2 fatias atômicas e testaveis:

```text
Fatia 1 (PR 1): Camada de Servico HTTP e Contrato de Dados IA
├── frontend/src/app/services/ia.service.ts (~90 linhas)
└── frontend/src/app/services/ia.service.spec.ts (~120 linhas)
Estimativa total de diff: ~210 linhas de codigo (bem abaixo de 400)

Fatia 2 (PR 2): Camada de Apresentacao, Aprovacao Human-in-the-Loop e Header Unificado
├── frontend/src/app/pages/admin/admin.component.ts (~100 linhas adicionadas/modificadas)
├── frontend/src/app/pages/admin/admin.component.spec.ts (~90 linhas adicionadas)
├── frontend/src/app/layout/shell/shell.component.ts (~35 linhas modificadas)
└── frontend/src/styles.scss (~25 linhas)
Estimativa total de diff: ~250 linhas de codigo (bem abaixo de 400)
```

---

## 5. Plano de Testes TDD (Karma / Jasmine)

### 5.1 Fase RED (Escrever testes antes do codigo de producao)
1. **`ia.service.spec.ts`**:
   - `deve inicializar com estado padrao vazio e isLoading false`.
   - `deve obter sugestoes via GET /api/v1/sugestoes e atualizar signal sugestoes`.
   - `deve aprovar sugestao via PATCH /api/v1/sugestoes/{id} com status aprovado`.
   - `deve rejeitar sugestao via PATCH /api/v1/sugestoes/{id} com status rejeitado`.
   - `deve tratar erro 401/403/404/409 e atualizar signal errorMessage com feedback amigavel`.
   - `deve redefinir isLoading para false em caso de sucesso ou falha`.

2. **`admin.component.spec.ts`**:
   - `deve exibir aba de remanejamento e listar sugestoes pendentes`.
   - `deve exibir badge de probabilidade de absenteismo formatada`.
   - `deve acionar aprovacao de remanejamento ao clicar em Aprovar Troca`.
   - `deve desativar botoes de acao quando isLoading for true`.
   - `deve acionar rejeicao de remanejamento com justificativa`.

### 5.2 Fase GREEN + REFACTOR
- Executar testes automatizados via `npm test` garantindo 100% de sucesso.
- Formatar codigo com Prettier (`npm run format:check`).

---

## 6. Decomposicao de Subtarefas e Checklist

- [ ] [Fatia 1 / TDD] Criar `ia.service.spec.ts` com testes unitarios cobrindo GET, PATCH e erros defensivos (Fase RED)
- [ ] [Fatia 1 / Impl] Criar `ia.service.ts` com HttpClient, Signals e tratamento de status 401, 403, 404, 409 (Fase GREEN)
- [ ] [Fatia 1 / Audit] Validar testes e diff da Fatia 1 (`python scripts/check_pr_size.py`)
- [ ] [Fatia 2 / TDD] Adicionar testes unitarios em `admin.component.spec.ts` para a aba de remanejamento e prevencao de corrida
- [ ] [Fatia 2 / Impl] Adicionar aba 'remanejamento' no `admin.component.ts` com cards, comparativo e acoes
- [ ] [Fatia 2 / Shell] Unificar cabecalho no `shell.component.ts` com usuario, perfil, campus e atalhos rapidos
- [ ] [Fatia 2 / Review] Executar debate adversarial multi-agente e auditoria de conformidade (zero emojis)
