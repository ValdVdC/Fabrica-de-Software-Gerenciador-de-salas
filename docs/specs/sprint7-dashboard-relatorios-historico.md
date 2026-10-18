# [SPEC-007] Dashboard, Relatorios, Pesquisa, Filtros, Exportacao e Historico de Operacoes

- **Sprint:** Sprint 07 - Sistema Quase Completo
- **Autor / Agente:** Planner-SDD & Squad SIGAAS
- **Status:** Aprovado (Gate 1)
- **Data de Criacao:** 2026-10-18
- **Prazo de entrega academica:** 2026-10-24 23:59
- **ID ClickUp (Epico/Task):** a registrar apos aprovacao do Gate 1

---

## 1. Contexto e Objetivos

As Sprints 04 a 06 entregaram CRUD (Modulo 1), motor de alocacao C/OpenMP (Modulo 2) e IA de remanejamento (Modulo 3). Os dados necessarios para acompanhamento ja sao persistidos (`horario`, `sala`, `turma`, `sugestao_remanejamento`, `log_alocacao`), mas nao ha consulta consolidada, busca, filtros por criterio de negocio, exportacao ou leitura do historico.

A Sprint 07 expoe esses dados por meio de seis entregas obrigatorias: dashboard, relatorios, pesquisa, filtros, exportacao e historico de operacoes.

### 1.1 Estado de partida (verificado no repositorio em 2026-10-18)

| Entrega | Estado atual |
| :--- | :--- |
| Dashboard | Inexistente (sem rota Angular e sem endpoint de agregacao) |
| Relatorios | Inexistentes |
| Pesquisa | Inexistente (apenas `skip` e `limit`) |
| Filtros | Parciais, por ID: `campus_id`, `curso_id`, `disciplina_id`, `turma_id`, `status` de sugestoes. `/horarios` sem filtros |
| Exportacao | Inexistente |
| Historico | `LogAlocacao` gravado em `alocacao.py` e `sugestoes.py`; sem endpoint de leitura, sem tela, sem `campus_id` na tabela |

### 1.2 Decisoes de design (a confirmar no Gate 1)

1. **Exportacao somente CSV.** PDF/XLSX nao se aplicam: os dados sao tabulares, o CSV abre em planilhas e evita nova dependencia. A nao aplicabilidade de PDF/XLSX sera justificada no documento da Sprint.
2. **Sem biblioteca de graficos.** Graficos de barras em SVG/CSS com a paleta neutra do SIGAAS, sem nova dependencia npm e sem estilos fora do design system.
3. **Isolamento por campus no historico.** `log_alocacao` nao possui `campus_id` e `horario_id` e anulado em `ON DELETE SET NULL`. Adicionar `campus_id` (nullable, indexado) via migration Alembic, com backfill a partir de `horario.campus_id` (Gate 2).
4. **Ampliacao do historico.** Alem de alocacao e remanejamento, registrar criacao, alteracao e remocao de salas, turmas e usuarios, reutilizando `TipoEventoLog` e identificando a entidade em `snapshot_evento`. Sem novos valores de enum.
5. **Perfis.** Dashboard, relatorios e historico: `admin`, `coordenador`, `secretaria` (escopo de campus aplicado no backend). `professor` e `aluno` nao acessam.

---

## 2. Historias de Usuario e Criterios de Aceite (Gherkin)

### Historia 1: Dashboard
> **Como** Coordenador ou Administrador **quero** visualizar indicadores consolidados do campus **para** acompanhar ocupacao e remanejamentos.

```gherkin
Cenario: Resumo de indicadores do campus
  Dado um Coordenador vinculado ao Campus 1 com salas, turmas e horarios cadastrados
  Quando consultar GET /api/v1/dashboard/resumo
  Entao o status deve ser 200 OK
  E o corpo deve conter total de salas ativas, turmas, horarios, sugestoes por status e vagas recuperadas
  E todos os valores devem considerar exclusivamente o Campus 1

Cenario: Administrador filtra por campus
  Dado um Administrador autenticado
  Quando consultar GET /api/v1/dashboard/resumo?campus_id=2
  Entao os indicadores devem refletir apenas o Campus 2

Cenario: Ocupacao por dia da semana e turno
  Dado horarios alocados em diferentes dias e turnos
  Quando consultar GET /api/v1/dashboard/ocupacao
  Entao a resposta deve conter a contagem de horarios por dia_semana (0 a 6) e por turno

Cenario: Perfil sem privilegio
  Dado um Aluno ou Professor autenticado
  Quando consultar qualquer endpoint /api/v1/dashboard
  Entao a API deve retornar 403 Forbidden

Cenario: Campus alheio
  Dado um Coordenador do Campus 1
  Quando consultar GET /api/v1/dashboard/resumo?campus_id=2
  Entao o filtro deve ser ignorado e os dados devem ser do Campus 1
```

### Historia 2: Relatorios
> **Como** Secretaria ou Coordenacao **quero** relatorios consolidados **para** apoiar decisoes de alocacao.

```gherkin
Cenario: Relatorio de ocupacao de salas
  Dado salas com horarios alocados no campus
  Quando consultar GET /api/v1/relatorios/ocupacao-salas
  Entao cada linha deve conter sala, bloco, capacidade, tipo, quantidade de horarios e taxa de ocupacao semanal

Cenario: Relatorio de remanejamentos
  Dado sugestoes em status pendente, aprovado e rejeitado
  Quando consultar GET /api/v1/relatorios/remanejamentos?status=aprovado&data_inicio=2026-10-01&data_fim=2026-10-31
  Entao somente sugestoes aprovadas no periodo devem ser retornadas, com sala origem, sala destino e decisor

Cenario: Relatorio vazio
  Dado um filtro sem resultados
  Quando consultar qualquer relatorio
  Entao a resposta deve ser 200 OK com lista vazia
```

### Historia 3: Pesquisa e filtros
> **Como** usuario autorizado **quero** pesquisar e filtrar registros **para** localiza-los rapidamente.

```gherkin
Cenario: Pesquisa textual de salas
  Dado salas cadastradas nos blocos A e B
  Quando consultar GET /api/v1/salas?q=lab
  Entao devem ser retornadas salas cujo bloco ou numero contenha "lab" sem distincao de maiusculas

Cenario: Filtros combinados de horarios
  Dado horarios de varios dias, turnos e salas
  Quando consultar GET /api/v1/horarios?dia_semana=1&turno=noturno&sala_id=5
  Entao devem ser retornados apenas horarios que satisfacam todos os criterios

Cenario: Parametro invalido
  Quando consultar GET /api/v1/horarios?dia_semana=9
  Entao a API deve retornar 422 Unprocessable Entity

Cenario: Termo com caracteres especiais
  Quando consultar GET /api/v1/salas?q=%25
  Entao o caractere deve ser tratado literalmente (sem wildcard SQL) e nao deve gerar erro 500
```

### Historia 4: Exportacao CSV
> **Como** Secretaria **quero** exportar relatorios e historico **para** analise em planilha.

```gherkin
Cenario: Exportar relatorio em CSV
  Quando consultar GET /api/v1/relatorios/ocupacao-salas?formato=csv
  Entao o Content-Type deve ser text/csv; charset=utf-8
  E o cabecalho Content-Disposition deve indicar o arquivo com extensao .csv
  E o arquivo deve respeitar os mesmos filtros e o isolamento de campus da consulta JSON

Cenario: Protecao contra CSV injection
  Dado um registro cujo texto comeca com =, +, - ou @
  Quando exportado em CSV
  Entao a celula deve ser prefixada com apostrofo

Cenario: Limite de linhas
  Dado mais de 10000 registros no filtro
  Quando exportar
  Entao o arquivo deve conter no maximo 10000 linhas
```

### Historia 5: Historico de operacoes
> **Como** Coordenador ou Administrador **quero** consultar o historico de operacoes **para** garantir rastreabilidade.

```gherkin
Cenario: Consulta do historico filtrado
  Dado eventos registrados por varios usuarios
  Quando consultar GET /api/v1/logs?tipo_evento=remanejamento&usuario_id=3&data_inicio=2026-10-01
  Entao devem ser retornados apenas eventos que satisfacam os criterios, do mais recente ao mais antigo

Cenario: Isolamento por campus
  Dado eventos dos Campus 1 e 2
  Quando um Coordenador do Campus 1 consultar GET /api/v1/logs
  Entao somente eventos do Campus 1 devem ser retornados

Cenario: Registro de operacoes de CRUD
  Quando uma sala for criada, alterada ou removida
  Entao deve existir um log com tipo_evento, usuario_responsavel, campus_id, entidade e identificador em snapshot_evento

Cenario: Historico somente leitura
  Quando houver tentativa de POST, PUT, PATCH ou DELETE em /api/v1/logs
  Entao a API deve retornar 405 Method Not Allowed

Cenario: Perfil sem privilegio
  Dado um Professor ou Aluno
  Quando consultar GET /api/v1/logs
  Entao a API deve retornar 403 Forbidden
```

---

## 3. Design de Arquitetura

### 3.1 Backend (FastAPI, camadas routers -> services -> queries)
- `app/api/v1/endpoints/dashboard.py`, `relatorios.py`, `logs.py` (novos).
- `app/services/dashboard_service.py` e `relatorio_service.py`: agregacoes via SQL (`func.count`, `group_by`), sem N+1 e sem calculo em memoria sobre listas grandes.
- `app/services/export_service.py`: serializacao CSV em streaming (`StreamingResponse`), UTF-8 com BOM, sanitizacao de CSV injection, teto de 10000 linhas.
- `app/services/log_service.py`: funcao unica `registrar_evento(db, tipo, usuario, campus_id, entidade, entidade_id, detalhes)` reutilizada pelos endpoints de CRUD, alocacao e sugestoes.
- Filtros e busca: parametros `Query` validados por Pydantic v2; `q` escapado com `ilike(..., escape='\\')`; todo filtro de campus derivado do usuario autenticado (nunca confiado ao cliente, exceto `admin`).
- Paginacao padrao `skip` e `limit` (maximo 100); exportacao usa o teto proprio.

### 3.2 Banco de dados (Gate 2)
- Migration Alembic: `log_alocacao.campus_id` (FK `campus.id`, nullable, indexado), backfill por `horario.campus_id`, indice composto `(campus_id, timestamp)`. Downgrade reversivel.
- Nenhuma outra alteracao de schema.

### 3.3 Frontend (Angular, sem regra de negocio)
- Rotas `dashboard`, `relatorios`, `historico` sob o shell, protegidas por `RoleGuard`.
- Servicos `dashboard.service.ts`, `relatorio.service.ts`, `log.service.ts` com tipos alinhados ao OpenAPI.
- Graficos em SVG/CSS; filtros em formularios reativos com debounce na busca; exportacao via download de blob autenticado (header JWT).
- Estado via signals; estados de carregamento, vazio e erro explicitos; icones vetoriais; sem emojis; sem paleta fora do design system.

### 3.4 Dependencias entre PRs
- Issues #72, #73 e #74 (correcao do PR #69) devem estar mergeadas antes dos PRs de frontend, pois alteram `styles.scss`, `shell.component.ts` e `admin.component.ts`.
- PR 1 (migration e logs) precede os demais PRs de backend que gravam eventos.

---

## 4. Fatiamento em PRs (limite de 400 linhas de producao cada)

| PR | Escopo | Tipo/Escopo do commit | Depende de |
| :--- | :--- | :--- | :--- |
| 1 | Migration `campus_id` em log, `log_service`, `GET /logs`, registro nos CRUDs de sala/turma/usuario | `feat(logs)` | - |
| 2 | `GET /dashboard/resumo` e `/dashboard/ocupacao` | `feat(dashboard)` | PR 1 |
| 3 | `GET /relatorios/*`, `export_service` (CSV), CSV em `/logs` | `feat(relatorios)` | PR 1 |
| 4 | Busca `q` e filtros em `/salas`, `/turmas`, `/usuarios`, `/horarios` | `feat(filtros)` | - |
| 5 | Frontend: dashboard e navegacao | `feat(frontend)` | PR 2, #72-#74 |
| 6 | Frontend: relatorios, historico, filtros e exportacao | `feat(frontend)` | PR 3, 4, #72-#74 |
| 7 | Documentacao: relatorio da Sprint 07, atualizacao da Sprint 06, PDF cumulativo | `docs(academic)` | PR 1 a 6 |

Se algum PR exceder 400 linhas, o planner deve dividi-lo antes de abrir (por exemplo, separar CSV de relatorios).

---

## 5. Plano de Testes TDD

### Backend (Pytest, cobertura global >= 85%)
- `test_api_logs.py`: filtros combinados, ordenacao, paginacao, isolamento de campus (BOLA), 403 para professor/aluno, 405 em escrita, backfill da migration.
- `test_log_service.py`: registro em criacao, alteracao e remocao de sala/turma/usuario com `campus_id` e `snapshot_evento`.
- `test_api_dashboard.py`: indicadores com dados semeados, isolamento de campus, filtro `campus_id` ignorado para coordenador, 403 por perfil.
- `test_api_relatorios.py`: ocupacao, remanejamentos, periodo invalido (`data_fim < data_inicio` retorna 422), lista vazia.
- `test_export_service.py`: cabecalhos, BOM, CSV injection, teto de linhas, mesmo filtro do JSON.
- `test_api_busca_filtros.py`: `q` com `%` e `_`, filtros combinados, `dia_semana` fora de 0 a 6, limites de paginacao.

### Frontend (Karma/Jasmine)
- Servicos: URL, parametros e headers por chamada, download de blob.
- Componentes: renderizacao de indicadores, estados de carregamento/vazio/erro, debounce da busca, desabilitar exportacao durante a requisicao, guard por perfil.

### Contrato
- Verificar tipos TypeScript contra `openapi.json` gerado pelo FastAPI (skill `contract-testing`).

---

## 6. Gates e Riscos

- **Gate 1:** aprovacao desta spec (Aprovado).
- **Gate 2:** migration do PR 1 (Aprovado formalmente pelo usuario em 2026-10-18); endpoints que gravam em `Horario` nao sao alterados nesta sprint.
- **Debate adversarial pre-PR** obrigatorio em todos os PRs, com Re-Review em loop ate consenso unanime.
- **Risco de prazo:** congelamento de codigo em 22/10; documentacao e PDF em 23/10; 24/10 reservado para contingencia e envio pelo Scrum Master.
- **Risco de consistencia documental:** apos #72 a #74, a secao 6.4 do relatorio da Sprint 06 e a Figura 11 deixam de refletir o sistema e devem ser revisadas no PR 7.
- **Fora de escopo:** PDF/XLSX, graficos interativos, notificacoes, novos perfis, alteracoes no motor C e no modelo de IA.
