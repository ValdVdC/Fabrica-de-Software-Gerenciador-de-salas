# [SPEC-015] Governança de Matrículas, Upload de Arquivos, Exportação PDF, Diário de Frequência, Scheduler de IA e Auditoria Completa

- **Sprint:** Fase de Remediação e Consolidação (M3 — Fluxos Acadêmicos e Gaps Operacionais)
- **Autor / Agente:** Planner-SDD & Squad SIGAAS (Grupo 31)
- **Status:** Draft - Aguardando Gate 1
- **Data de Criação:** 2026-11-27
- **ID ClickUp (Épico/Task):** [Pendente sync]
- **Identificação Acadêmica:** Disciplina: Fábrica de Software & Tópicos Avançados em Computação | Curso: Bacharelado em Ciência da Computação — Turma 8MB - CC | Equipe: Grupo 31 — SIGAAS

## Resumo Executivo e Plano de Entregas (9 PRs Incrementais <= 310 LOC)

Esta especificação redefine o cancelamento de matrícula pelo Aluno, corrige capacidade/auditoria em matrículas e fecha pendências operacionais (upload CSV/XLSX, PDF ABNT Grupo 31, diário de frequência docente para a IA real, scheduler `APScheduler` + `cron` e auditoria `LogAlocacao`). O plano é fatiado em **9 PRs incrementais** (`<= 310` LOC prod./PR, Seção 4):

- **PR 1 (`feat/audit-trail-completo`, ~75 LOC):** `LogAlocacao` em `cursos`, `disciplinas`, `salas`, `matriculas`, `sugestoes` (`REMANEJAMENTO` e rejeição) e `seed_db.py:201`.
- **PR 2 (`feat/matriculas-governanca-vagas`, ~220 LOC):** Migration `005_academic_flows_governance`, `Turma.vagas`/`prazo_cancelamento`, checagem atômica `409`, restrição `DELETE` (`403` Aluno), `solicitar`/`decidir-cancelamento` e `MatriculaRead` enriquecido (`joinedload`).
- **PR 3 (`feat/frontend-matriculas-confirmacao`, ~250 LOC):** Modais de confirmação com detalhes completos em `AlunoComponent` e `SecretariaComponent`, fluxo de trancamento e `atualizarTurma`.
- **PR 4 (`feat/backend-diario-frequencia`, ~170 LOC):** `GET/POST /api/v1/frequencias` (upsert idempotente) e filtro `Matricula.status == "ativa"` em `ia_service.py`.
- **PR 5 (`feat/frontend-diario-professor`, ~190 LOC):** `FrequenciaService`, output `aulaSelecionada` em `GradeHorariaComponent` e diário de chamada no `ProfessorComponent`.
- **PR 6 (`feat/relatorios-exportacao-pdf`, ~230 LOC):** `reportlab`, `pdf_service.py` ABNT (Grupo 31), `formato=pdf` em `relatorios.py`, sync OpenAPI em `main.py:39` e botões PDF no Angular.
- **PR 7 (`feat/backend-importacoes-lote`, ~310 LOC):** `openpyxl` e `POST /api/v1/importacoes/{salas|alunos|matriculas}` (magic bytes, anti-CSV Injection, `dry_run` + commit atômico).
- **PR 8 (`feat/frontend-importacoes-ui`, ~240 LOC):** `ImportacaoService` e modal reutilizável em `AdminComponent` e `SecretariaComponent`.
- **PR 9 (`feat/scheduler-apscheduler-cron`, ~190 LOC):** `scheduler_service.py` (advisory lock PG), `lifespan` `APScheduler`, `run_ia_job.py`, `--retrain` em `evaluate_model.py` e `docker/cron/`.

---

## 1. Contexto e Diagnóstico Atual

### 1.1 Diagnóstico do Fluxo "Cancelar Matrícula" (Perfil Aluno e Secretaria)

A auditoria direta sobre o fluxo atual de matrículas constatou um defeito grave de regra de negócio e de usabilidade:

| Componente | Evidência Verificada (`file:line` e Símbolos) | Problema / Risco Identificado | Solução Especificada |
| :--- | :--- | :--- | :--- |
| **Auto-cancelamento unilateral** | `backend/app/api/v1/endpoints/matriculas.py:98-155` (`cancelar_matricula`) | `require_role(..., PerfilUsuario.ALUNO)` permite que o discente execute `DELETE /api/v1/matriculas/{id}` em qualquer momento do semestre, sem janela letiva, justificativa ou análise da Secretaria/Coordenação. | Restringir `DELETE /matriculas/{id}` a `ADMIN`, `COORDENADOR`, `SECRETARIA` (`403` para `ALUNO`). Criar fluxo governado: `POST /matriculas/{id}/solicitar-cancelamento` (`ALUNO`) + `PATCH /matriculas/{id}/decidir-cancelamento` (`ADMIN`/`COORDENADOR`/`SECRETARIA`). |
| **UI sem contexto nem confirmação** | `frontend/src/app/pages/aluno/aluno.component.ts:16-71`; `secretaria.component.ts:130-137,285-292`; `schemas/matricula.py:15-20` | `MatriculaRead` expõe apenas `id`, `aluno_id`, `turma_id`, `data_matricula`, `status`, `created_at`. `AlunoComponent` exibe apenas `Turma #{{ m.turma_id }}` e dispara `DELETE` em clique único sem confirmação. `SecretariaComponent` exibe `Aluno #{{ m.aluno_id }}` e também cancela sem modal de confirmação. | Enriquecer `MatriculaRead` via `joinedload` (sem N+1) com `aluno_nome`, `disciplina_codigo`, `disciplina_nome`, `periodo_letivo`, `turno`, `professor_nome`, `horarios_resumo`, `turma_vagas`. Exigir modal de confirmação explícita em ambos os perfis. |
| **Capacidade e Auditoria em `POST /matriculas`** | `models/academico.py:52-71` (`Turma`); `schemas/turma.py:7-44`; `matriculas.py:13,38-95` | `Turma` não possui coluna `vagas`; `matricular_aluno` incrementa `num_matriculados` sem limite de capacidade e importa `registrar_evento` (`:13`) sem jamais chamá-lo. | Adicionar `Turma.vagas` (`nullable=True` para retrocompatibilidade) e `Turma.prazo_cancelamento` (`Date`, `nullable=True`); aplicar checagem atômica `num_matriculados < vagas` (`409 Conflict`) e registrar `LogAlocacao` (`CRIACAO`). |
| **Cascata dupla e unicidade em `Frequencia`** | `models/ia.py:19-33` (`Frequencia`); `001_initial_schema.py:212-213`; `alocacao.py:295` | `Frequencia` possui `ondelete="CASCADE"` em `matricula_id` e `horario_id` e nenhuma `UniqueConstraint`. Soft-cancel (`status="cancelada"`) mantém `Frequencia` atrelada a aluno inativo, distorcendo a IA; e `alocacao.py:295` ao apagar `Horario` elimina registros de presença em cascata. | Preservar integridade adicionando `UniqueConstraint("matricula_id", "horario_id", "data", name="uq_frequencia_matricula_horario_data")` e filtrando `Matricula.status == "ativa"` em `ia_service.py:extrair_dataset_frequencias`. |

### 1.2 Diagnóstico dos Gaps Funcionais (Aula 01 p. 12 e Dívidas Técnicas)

| Gap / Dívida | Evidência Verificada (`file:line`) | Impacto Atual | Solução Especificada |
| :--- | :--- | :--- | :--- |
| **Upload de Arquivos em Lote** | `backend/requirements.txt:17` (`python-multipart>=0.0.9`), ausência de `openpyxl` e de qualquer `UploadFile`; `export_service.py:12` (`PREFIXOS_PERIGOSOS_CSV`). | Cadastros em massa de salas, alunos e matrículas só são possíveis registro a registro; nenhum `<input type="file">` ou `FormData` existe no Angular. | Criar `POST /api/v1/importacoes/{salas\|alunos\|matriculas}` com validação de extensão, MIME, magic bytes, limite de 2 MB / 2.000 linhas, defesa contra CSV/Formula Injection, `dry_run` preview + commit transacional, e modal Angular. |
| **Exportação PDF Real e Drift OpenAPI** | `backend/app/main.py:39` (tag `Relatorios` promete CSV/PDF); `relatorios.py:30,63` (`Literal["json", "csv"]`); `relatorio.service.ts:63-102`; `relatorios.component.ts:22-27`. | `?formato=pdf` retorna `422 Unprocessable Entity`; nenhuma biblioteca de PDF está instalada e `main.py:39` promete exportação de grade horária inexistente. | Instalar `reportlab>=4.2.0`, implementar `pdf_service.py` no padrão ABNT Grupo 31 (zero alucinação institucional, zero emojis), habilitar `formato=pdf` em `/ocupacao-salas`, `/remanejamentos` e novo `/relatorios/grade-horaria`, e adicionar botões PDF no Angular. |
| **Diário de Frequência (`Frequencia`)** | `models/ia.py:19-33`; `ia_service.py:98-146`; `professor.component.ts:1-16`; `grade-horaria.component.ts:31-41`. | Professor não possui endpoint nem tela para lançar presença; em produção, `Frequencia` fica vazia e `ia_service.py` cai sempre nos 10 priors sintéticos. | Criar `/api/v1/frequencias` (`GET` e `POST` batch idempotente), filtrar `Matricula.status == "ativa"` em `ia_service.py`, adicionar clique em `GradeHorariaComponent` e diário de chamada em `ProfessorComponent`. |
| **Scheduler Real (`APScheduler` + `cron`)** | `requirements.txt:20` (`apscheduler` não importado); `main.py:44-58` (sem `lifespan`); `docker/cron/crontab:4` (`echo` stub); `docker/cron/entrypoint.sh:4-9`; `evaluate_model.py:65-89`; `relatorio_metricas_ml.json:15`. | Job periódico nunca executa; `cron` apenas escreve string no log sem exportar variáveis de ambiente; `evaluate_model.py` não retreina com novas frequências (`total_amostras: 2`, `acuracia: 0.5`). | Criar `scheduler_service.py` (advisory lock PostgreSQL), ativar `BackgroundScheduler` no `lifespan` (`ENABLE_SCHEDULER`), criar `scripts/run_ia_job.py`, atualizar `docker/cron/crontab` + `entrypoint.sh`, e adicionar `--retrain` + proveniência em `evaluate_model.py`. |
| **Auditoria Incompleta em `LogAlocacao`** | `cursos.py:49-74`, `disciplinas.py:52-75`, `salas.py:114-152` (`associar_equipamento`), `matriculas.py:38-95`, `sugestoes.py:181-200`, `scripts/seed_db.py:201-206`. | Mutações relevantes não geram auditoria; aprovação de sugestão registra `TipoEventoLog.ALTERACAO` em vez de `REMANEJAMENTO`; rejeição não registra nada; `seed_db.py:201` omite `campus_id`. | Padronizar `registrar_evento(...)` em todas as mutações, usar `TipoEventoLog.REMANEJAMENTO` na aprovação e `ALTERACAO` na rejeição de sugestões, e preencher `campus_id=c1.id` no seed. |

---

## 2. Matriz RBAC, Histórias de Usuário e Critérios de Aceite (Gherkin)

### 2.1 Matriz RBAC dos Fluxos Novos e Alterados

| Recurso / Rota | Método | Admin | Coordenador | Secretaria | Professor | Aluno | Escopo / Regra de Negócio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `/api/v1/matriculas/{id}` | DELETE | Sim | Sim (Campus) | Sim (Campus) | Não (403) | **Não (403)** | Cancelamento direto restrito à equipe administrativa/secretaria. |
| `/api/v1/matriculas/{id}/solicitar-cancelamento` | POST | Não (403) | Não (403) | Não (403) | Não (403) | Sim (Própria) | Exige `motivo` (10..500 chars), `status == "ativa"` e `prazo_cancelamento` vigente; não decrementa `num_matriculados`. |
| `/api/v1/matriculas/{id}/decidir-cancelamento` | PATCH | Sim | Sim (Campus) | Sim (Campus) | Não (403) | Não (403) | Exige `status == "cancelamento_solicitado"`; `aprovado` decrementa vaga atomicamente; `rejeitado` restaura `"ativa"`. |
| `/api/v1/importacoes/salas` | POST | Sim | Sim (Campus) | Não (403) | Não (403) | Não (403) | Upload `.csv`/`.xlsx` até 2 MB e 2.000 linhas; suporta `dry_run`. |
| `/api/v1/importacoes/alunos` | POST | Sim | Sim (Campus) | Sim (Campus) | Não (403) | Não (403) | Cria apenas `PerfilUsuario.ALUNO` no campus alvo; respeita bcrypt <= 72B. |
| `/api/v1/importacoes/matriculas` | POST | Sim | Sim (Campus) | Sim (Campus) | Não (403) | Não (403) | Valida campus único e capacidade atômica `Turma.vagas`. |
| `/api/v1/relatorios/{ocupacao-salas\|remanejamentos\|grade-horaria}` | GET | Sim | Sim (Campus) | Sim (Campus) | Não (403) | Não (403) | Aceita `formato=json \| csv \| pdf`; PDF no padrão ABNT Grupo 31. |
| `/api/v1/frequencias` | GET / POST | Sim | Sim (Campus) | Sim (Campus) | Sim (Suas turmas) | Não (403) | Professor só consulta/lança presença de `Horario` vinculado à sua `Turma`. |

### 2.2 Histórias de Usuário e Critérios de Aceite

#### História 1: Governança de Matrículas, Solicitação de Trancamento e Capacidade de Turmas
> **Como** Aluno e Secretário Acadêmico  
> **Quero** que o cancelamento direto de matrícula seja restrito à Secretaria/Coordenação, que o aluno possa apenas solicitar trancamento com justificativa dentro do prazo letivo mediante modal detalhada, e que novas matrículas respeitem a capacidade da turma  
> **Para que** não ocorram desistências acidentais com um clique, turmas superlotadas ou distorções silenciosas na base de frequência.

```gherkin
Cenário: Aluno é impedido de executar DELETE direto e solicita cancelamento com justificativa
  Dado que um Aluno autenticado possui matrícula ativa ID 100 na Turma 5 (com prazo_cancelamento futuro e 10 matriculados)
  Quando enviar DELETE /api/v1/matriculas/100
  Então a API deve responder com status 403 Forbidden
  E quando enviar POST /api/v1/matriculas/100/solicitar-cancelamento com motivo "Conflito de horario com estagio obrigatorio"
  Então a API deve responder com status 200 OK alterando o status para "cancelamento_solicitado"
  E Turma.num_matriculados deve permanecer igual a 10 até a decisão administrativa

Cenário: Bloqueio de solicitação fora do prazo letivo e aprovação atômica pela Secretaria
  Dado que a Turma 6 possui prazo_cancelamento anterior à data atual
  Quando o Aluno enviar POST /api/v1/matriculas/101/solicitar-cancelamento
  Então a API deve responder com status 400 Bad Request informando prazo encerrado
  E quando a Secretaria aprovar a matrícula 100 via PATCH /api/v1/matriculas/100/decidir-cancelamento com decisao "aprovado"
  Então o status deve passar para "cancelada", Turma.num_matriculados deve decrementar para 9 e um LogAlocacao CANCELAMENTO deve ser gravado

Cenário: Matrícula respeita limite atômico de vagas da turma
  Dado que a Turma 7 possui vagas = 1 e num_matriculados = 1
  Quando a Secretaria enviar POST /api/v1/matriculas para um segundo aluno
  Então a API deve responder com status 409 Conflict informando turma sem vagas disponíveis
```

#### História 2: Upload Seguro em Lote (Salas, Alunos e Matrículas)
> **Como** Administrador, Coordenador ou Secretário  
> **Quero** importar planilhas CSV ou XLSX com pré-visualização (`dry_run`), validação por linha e proteção contra payloads maliciosos  
> **Para que** o carregamento inicial e semestral de salas, alunos e matrículas ocorra sem falhas de integridade ou vulnerabilidades de upload.

```gherkin
Cenário: Pré-visualização e importação atômica de salas via XLSX válido
  Dado que o Coordenador do Campus 1 envia um arquivo ".xlsx" válido (magic bytes PK\x03\x04, <= 2 MB) para POST /api/v1/importacoes/salas?dry_run=true
  Quando o arquivo contiver 3 linhas válidas de salas
  Então a API deve responder com status 200 OK retornando validas = 3, inseridas = 0 e erros = []
  E quando reenviar com dry_run=false, as 3 salas devem ser inseridas em transação única no Campus 1 com LogAlocacao registrado

Cenário: Rejeição de arquivo disfarçado, CSV Injection ou tamanho excedido
  Dado que um usuário autenticado envia um arquivo executável renomeado para "alunos.xlsx" ou um CSV contendo célula iniciada por "=CMD|"
  Quando enviar para POST /api/v1/importacoes/alunos
  Então a API deve rejeitar com status 400 Bad Request (magic bytes inválidos) ou 422 Unprocessable Entity (fórmula perigosa detectada) sem persistir nenhuma linha
```

#### História 3: Exportação Real em PDF (Padrão ABNT Grupo 31)
> **Como** Gestor Acadêmico  
> **Quero** exportar os relatórios de ocupação de salas, remanejamentos e grade horária em PDF diretamente pela API e pelo Angular  
> **Para que** os documentos gerenciais possam ser arquivados e apresentados com formatação oficial sem alucinação institucional.

```gherkin
Cenário: Download de relatório de ocupação em PDF com cabeçalho oficial do Grupo 31
  Dado que um Coordenador do Campus 1 está autenticado
  Quando requisitar GET /api/v1/relatorios/ocupacao-salas?formato=pdf
  Então a API deve responder com status 200 OK, Content-Type "application/pdf" e payload iniciado por "%PDF-"
  E o PDF deve conter estritamente os metadados da disciplina, curso/turma 8MB - CC e Grupo 31 - SIGAAS, sem nomes inventados de faculdade ou cidade
```

#### História 4: Diário de Frequência do Professor, Scheduler de IA e Auditoria Integral
> **Como** Professor e Equipe de Operação  
> **Quero** registrar a frequência dos alunos ativos de minhas aulas na SPA e contar com retreinamento/inferência agendada automaticamente pelo `APScheduler` e `cron`, com todas as mutações auditadas  
> **Para que** o modelo de absenteísmo utilize dados reais de sala de aula e toda operação crítica deixe trilha em `LogAlocacao`.

```gherkin
Cenário: Professor registra chamada idempotente para aula própria e alimenta IA
  Dado que o Professor ID 10 leciona a Turma 5 (Horário ID 20) que possui o Aluno A (status "ativa") e Aluno B (status "cancelada")
  Quando enviar POST /api/v1/frequencias para o Horário 20 e data "2026-11-27" com o Aluno A presente
  Então a API deve persistir o registro (fazendo upsert idempotente em reenvios na mesma data) e retornar status 200 OK
  E ao tentar lançar frequência para Aluno B (cancelado) ou para Horário de outro professor, deve retornar 400 ou 403 respectivamente
  E extrair_dataset_frequencias() deve considerar apenas matrículas com status "ativa"

Cenário: Aprovação e rejeição de sugestão de remanejamento gravam auditoria correta
  Dado que existe uma SugestaoRemanejamento pendente no Campus 1
  Quando o Coordenador aprovar via PATCH /api/v1/sugestoes/{id}
  Então deve ser gravado um LogAlocacao com tipo_evento = "remanejamento" e snapshot contendo sala_anterior_id e nova_sala_id
  E quando rejeitar outra sugestão, deve ser gravado um LogAlocacao com tipo_evento = "alteracao" e decisao = "rejeitado"
```

---

## 3. Arquitetura e Contratos Técnicos

### 3.1 Endpoints FastAPI e Contratos Pydantic v2

1. **Matrículas e Turmas (`schemas/turma.py`, `schemas/matricula.py`, `endpoints/turmas.py`, `endpoints/matriculas.py`):**
   - `TurmaCreate` / `TurmaUpdate` / `TurmaRead`: adicionar `vagas: Optional[int] = Field(default=None, gt=0, le=5000)` e `prazo_cancelamento: Optional[date] = None`.
   - `MatriculaRead`: enriquecer com `aluno_nome: Optional[str] = None`, `aluno_email: Optional[str] = None`, `disciplina_codigo: Optional[str] = None`, `disciplina_nome: Optional[str] = None`, `periodo_letivo: Optional[str] = None`, `turno: Optional[str] = None`, `professor_nome: Optional[str] = None`, `turma_vagas: Optional[int] = None`, `turma_num_matriculados: Optional[int] = None`, `horarios_resumo: list[str] = Field(default_factory=list)`, `motivo_solicitacao: Optional[str] = None`, `solicitado_em: Optional[datetime] = None`, `parecer_decisao: Optional[str] = None`, `decidido_em: Optional[datetime] = None`. Todas as consultas em `matriculas.py` devem usar `joinedload`/`selectinload` (zero N+1).
   - `SolicitacaoCancelamentoCreate`: `{ motivo: str = Field(..., min_length=10, max_length=500) }` (`extra="forbid"`).
   - `DecisaoCancelamentoUpdate`: `{ decisao: Literal["aprovado", "rejeitado"], parecer: Optional[str] = Field(default=None, max_length=500) }` (`extra="forbid"`).
   - `POST /api/v1/matriculas`: antes de inserir/reativar, executar `update(Turma).where(Turma.id == payload.turma_id, or_(Turma.vagas.is_(None), Turma.num_matriculados < Turma.vagas)).values(num_matriculados=Turma.num_matriculados + 1)` — se `rowcount == 0`, lançar `409 Conflict`. Gravar `LogAlocacao` (`TipoEventoLog.CRIACAO`, `entidade="matricula"`).
   - `DELETE /api/v1/matriculas/{id}`: remover `PerfilUsuario.ALUNO` de `require_role(...)`.
   - `POST /api/v1/matriculas/{id}/solicitar-cancelamento`: exige `PerfilUsuario.ALUNO` e posse `matricula.aluno_id == current_user.id`; verifica `status == "ativa"`; se `turma.prazo_cancelamento` estiver definido e `date.today() > turma.prazo_cancelamento`, retorna `400 Bad Request`; atualiza `status = "cancelamento_solicitado"`, `motivo_solicitacao`, `solicitado_em = now(utc)` sem alterar `Turma.num_matriculados`; grava `LogAlocacao` (`ALTERACAO`).
   - `PATCH /api/v1/matriculas/{id}/decidir-cancelamento`: exige `ADMIN`, `COORDENADOR`, `SECRETARIA` + `require_campus_access`; exige `status == "cancelamento_solicitado"`; se `aprovado`, muda para `"cancelada"` e decrementa `Turma.num_matriculados > 0` atomicamente (`TipoEventoLog.CANCELAMENTO`); se `rejeitado`, restaura `"ativa"` (`TipoEventoLog.ALTERACAO`).
2. **Importações em Lote (`schemas/importacao.py`, `services/importacao_service.py`, `endpoints/importacoes.py`):**
   - Rotas: `POST /api/v1/importacoes/{entidade}` (`entidade: Literal["salas", "alunos", "matriculas"]`) com `file: UploadFile = File(...)`, `dry_run: bool = Query(default=True)`, `campus_id: Optional[int] = Query(default=None, gt=0)`.
   - Validações obrigatórias na camada de serviço (`importacao_service.py`):
     - Tamanho máximo `MAX_IMPORT_BYTES = 2 * 1024 * 1024` (retorna `413` se excedido) e `MAX_IMPORT_ROWS = 2000` (retorna `422` se excedido).
     - Extensão permitida `.csv` ou `.xlsx`, `Content-Type` compatível e inspeção real de magic bytes (`b"PK\x03\x04"` para `.xlsx`; UTF-8/UTF-8-BOM válido sem byte nulo `\x00` para `.csv`, retornando `400` em mismatch).
     - Leitura `.xlsx` via `openpyxl.load_workbook(..., read_only=True, data_only=True)` com limite de 1 aba processada e proteção contra dimensões excessivas.
     - Rejeição de qualquer valor textual iniciado por `PREFIXOS_PERIGOSOS_CSV` (`=`, `+`, `-`, `@`, `\t`, `\r`) para prevenir CSV/Formula Injection.
     - Para `alunos`, validação de e-mail único, política de senha <= 72 bytes UTF-8 (ou geração automática de senha temporária segura + `deve_trocar_senha=True` quando coluna `senha` opcional for omitida), criando estritamente `PerfilUsuario.ALUNO`.
     - Modo atômico: se `erros` não estiver vazio e `dry_run=False`, realiza rollback integral e retorna `422` com relatório linha a linha (`ImportacaoErroLinha(linha, campo, mensagem)`).
3. **Exportação PDF Real (`services/pdf_service.py`, `endpoints/relatorios.py`, `main.py`):**
   - `relatorios.py`: atualizar `formato: Optional[Literal["json", "csv", "pdf"]]` em `/ocupacao-salas` e `/remanejamentos`, e adicionar `GET /api/v1/relatorios/grade-horaria` (`json | csv | pdf`) alinhado à descrição da tag `"Relatorios"` em `main.py:39`.
   - `pdf_service.py` (com `reportlab>=4.2.0`):
     - Cabeçalho institucional estrito: `FÁBRICA DE SOFTWARE & TÓPICOS AVANÇADOS EM COMPUTAÇÃO`, `CURSO DE BACHARELADO EM CIÊNCIA DA COMPUTAÇÃO — TURMA 8MB - CC`, `Grupo 31 — SIGAAS` (proibido inventar instituição de ensino, cidade ou estado; zero emojis).
     - Paleta visual: `#1f4e79` (cabeçalho de tabelas e títulos), `#cbd5e1` (bordas), `#f8fafc` (linhas alternadas), fonte serifada/Times e monoespaçada para códigos/IDs, rodapé com `Página X de Y` via `Canvas` numerado.
4. **Diário de Frequência (`schemas/frequencia.py`, `endpoints/frequencias.py`, `services/ia_service.py`):**
   - `GET /api/v1/frequencias`: query `horario_id: int`, `data_aula: date`. Valida que o `Professor` é titular da `Turma` ou que o usuário administrativo pertence ao campus (`require_campus_access`).
   - `POST /api/v1/frequencias`: recebe `FrequenciaLoteCreate(horario_id: int, data: date, registros: list[FrequenciaRegistroItem])` (`min_length=1, max_length=200`). Valida que cada `matricula_id` pertence à `turma_id` do `horario` e possui `status == "ativa"`. Executa upsert determinístico respeitando `uq_frequencia_matricula_horario_data` e registra `LogAlocacao` (`CRIACAO`/`ALTERACAO`).
   - `ia_service.py:extrair_dataset_frequencias`: adicionar `.join(Matricula, Frequencia.matricula_id == Matricula.id).where(Matricula.status == "ativa")` e retornar metadado explícito indicando se houve uso de priors sintéticos ou dados reais.
5. **Scheduler Real & Auditoria (`services/scheduler_service.py`, `main.py`, `scripts/run_ia_job.py`, `scripts/evaluate_model.py`, `docker/cron/`):**
   - `config.py`: adicionar `ENABLE_SCHEDULER: bool = False` e `IA_JOB_INTERVAL_HOURS: int = 6`.
   - `scheduler_service.py`: `executar_rotina_ia_agendada()` adquire advisory lock PostgreSQL (`pg_try_advisory_lock(931015)` quando dialeto for `postgresql`), retreina `treinar_modelo_absenteismo(db)` se contagem de `Frequencia` >= 10, executa `avaliar_pipeline_modelo` e gera `SugestaoRemanejamento` pendentes por `Campus` ativo, liberando o lock em `finally`.
   - `main.py`: configurar `lifespan` do `FastAPI` iniciando `BackgroundScheduler` (`max_instances=1, coalesce=True`) quando `settings.ENABLE_SCHEDULER` for `True`.
   - `docker/cron/entrypoint.sh` e `docker/cron/crontab`: exportar `DATABASE_URL`, `POSTGRES_*`, `SECRET_KEY`, `PYTHONPATH` para `/etc/environment` antes do daemon `cron`, e substituir o `echo` da linha 4 por `0 */6 * * * root . /etc/environment; cd /app && python scripts/run_ia_job.py >> /var/log/cron.log 2>&1`.
   - `scripts/evaluate_model.py`: adicionar flag `--retrain` e campo `origem_dados` (`"frequencias_reais"` vs `"priors_sinteticos"`) em `relatorio_metricas_ml.{json,md}`.

### 3.2 Modelo de Dados PostgreSQL e Migration Alembic (`005_academic_flows_governance`)

- **Cadeia Alembic:** `revision = "005_academic_flows_governance"`, `down_revision = "004_seguranca_auth_mfa"` (caso implementada antes de `SPEC-014`, encadear em `003_release_candidate_indexes`, mantendo grafo linear sem cabeças múltiplas).
- **Alterações com `with op.batch_alter_table(...)` (compatibilidade SQLite e PostgreSQL sem lock de tabela):**
  1. Tabela `turma` (`models/academico.py`):
     - `vagas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)`
     - `prazo_cancelamento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)`
     - `CheckConstraint("vagas IS NULL OR vagas > 0", name="ck_turma_vagas_positiva")`
  2. Tabela `matricula` (`models/academico.py`):
     - `motivo_solicitacao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)`
     - `solicitado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)`
     - `decidido_por: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)`
     - `parecer_decisao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)`
     - `decidido_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)`
     - `Index("ix_matricula_status_turma", "turma_id", "status")`
  3. Tabela `frequencia` (`models/ia.py`):
     - `UniqueConstraint("matricula_id", "horario_id", "data", name="uq_frequencia_matricula_horario_data")`
- **Reversibilidade (`downgrade()`):** Remove `uq_frequencia_matricula_horario_data` em `frequencia`, remove `ix_matricula_status_turma` + FK/colunas de solicitação em `matricula`, e remove `ck_turma_vagas_positiva` + `vagas` + `prazo_cancelamento` em `turma` usando `batch_alter_table`.

### 3.3 Contratos `openapi-typescript` e Arquitetura Frontend Angular 20

- **`openapi-typescript`:** Após alteração dos schemas backend (PRs 2, 4, 6, 7), regenerar `frontend/src/app/core/models/api-contracts.ts` sem usar `any` em chamadas `HttpClient`.
- **`AlunoComponent` & `SecretariaComponent`:**
  - Exibir na listagem de matrículas: `disciplina_codigo`, `disciplina_nome`, `periodo_letivo`, `turno`, `professor_nome`, `horarios_resumo` e badge de status (`ativa`, `cancelamento_solicitado`, `cancelada`).
  - Substituir o clique direto por **modal dedicada de confirmação** (`Solicitar Trancamento` com campo `motivo` no `AlunoComponent`; `Confirmar Cancelamento` e painel de `Solicitações Pendentes` com `Aprovar`/`Rejeitar` + `parecer` na `SecretariaComponent`).
  - Adicionar `atualizarTurma` e campo opcional `vagas` / `prazo_cancelamento` no formulário de Turmas da Secretaria.
- **`ProfessorComponent`, `GradeHorariaComponent` & `FrequenciaService`:**
  - `GradeHorariaComponent` emite `aulaSelecionada = output<HorarioMeu>()` ao acionar botão `"Registrar Frequência"` com ícone `lucide-angular` (`ClipboardCheck`).
  - `ProfessorComponent` abre o diário de chamada da aula selecionada carregando alunos ativos e enviando lote via `POST /api/v1/frequencias`.
- **`RelatoriosComponent`, `RelatorioService`, `AdminComponent`, `SecretariaComponent` & `ImportacaoModalComponent`:**
  - `RelatorioService` ganha `exportarOcupacaoPdf()`, `exportarRemanejamentosPdf()` e `exportarGradeHorariaPdf()` reutilizando `dispararDownloadBlob` (`application/pdf`).
  - Novo componente reutilizável de modal de importação (`ImportacaoModalComponent`) acionado por botão `"Importar CSV/XLSX"` em `AdminComponent` (Salas) e `SecretariaComponent` (Alunos e Matrículas), exibindo pré-visualização `dry_run`, lista de erros por linha e confirmação transacional.

---

## 4. Fatiamento em PRs Incrementais (Limite `<= 310` LOC Prod.)

| PR | Branch | Escopo Técnico | Arquivos de Produção Alvo | LOC Prod. Est. | Conventional Commit | Dependência | Gate 2 |
| :---: | :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| **PR 1** | `feat/audit-trail-completo` | Completar `LogAlocacao` em `cursos`, `disciplinas`, `salas`, `matriculas`, `sugestoes` (`REMANEJAMENTO` + rejeição) e `seed_db.py:201`. | `cursos.py`, `disciplinas.py`, `salas.py`, `matriculas.py`, `sugestoes.py`, `scripts/seed_db.py` | ~75 | `feat(audit): completar registros de log_alocacao e evento remanejamento` | - | **Sim (toca `sugestoes.py`)** |
| **PR 2** | `feat/matriculas-governanca-vagas` | Migration `005_academic_flows_governance`; `Turma.vagas`/`prazo_cancelamento`; `Matricula` governada (`403` `DELETE` Aluno, `solicitar`/`decidir-cancelamento`, checagem atômica `409`, `MatriculaRead` enriquecido). | `models/academico.py`, `models/ia.py`, `schemas/turma.py`, `schemas/matricula.py`, `endpoints/turmas.py`, `endpoints/matriculas.py` (`005_*.py` isento) | ~220 | `feat(matriculas): restringir auto-cancelamento, adicionar vagas e fluxo de trancamento` | PR 1 | **Sim (Migration + `matriculas.py`)** |
| **PR 3** | `feat/frontend-matriculas-confirmacao` | `SecretariaService` (`solicitarCancelamento`, `decidirCancelamento`, `atualizarTurma`), modais de confirmação com detalhes completos em `AlunoComponent` e `SecretariaComponent` e fila de aprovação. | `secretaria.service.ts`, `aluno.component.ts`, `secretaria.component.ts`, `api-contracts.ts` | ~250 | `feat(frontend): adicionar modais de confirmacao e fluxo de trancamento de matricula` | PR 2 | Sim (revisão PR) |
| **PR 4** | `feat/backend-diario-frequencia` | `schemas/frequencia.py`, `endpoints/frequencias.py`, registro em `api.py` + tag `Frequencias` em `main.py`, filtro `Matricula.status == "ativa"` e proveniência em `ia_service.py`. | `schemas/frequencia.py`, `endpoints/frequencias.py`, `api/v1/api.py`, `main.py`, `services/ia_service.py` | ~170 | `feat(frequencia): implementar diario de frequencia e filtro ativo na ia` | PR 2 | Sim (revisão PR) |
| **PR 5** | `feat/frontend-diario-professor` | `FrequenciaService`, output `aulaSelecionada` em `GradeHorariaComponent` e painel/modal de chamada no `ProfessorComponent`. | `frequencia.service.ts`, `grade-horaria.component.ts`, `professor.component.ts`, `api-contracts.ts` | ~190 | `feat(frontend): implementar diario de frequencia na visao do professor` | PR 4 | Sim (revisão PR) |
| **PR 6** | `feat/relatorios-exportacao-pdf` | `reportlab>=4.2.0`, `pdf_service.py` ABNT (Grupo 31), `formato=pdf` em `relatorios.py`, `/grade-horaria`, sync tag `main.py:39`, `RelatorioService` e botões PDF em `RelatoriosComponent`. | `requirements.txt`, `services/pdf_service.py`, `endpoints/relatorios.py`, `main.py`, `relatorio.service.ts`, `relatorios.component.ts` | ~230 | `feat(relatorios): implementar exportacao pdf abnt com dados do grupo 31` | PR 4 | Sim (revisão PR) |
| **PR 7** | `feat/backend-importacoes-lote` | `openpyxl>=3.1.2`, `schemas/importacao.py`, `services/importacao_service.py` (magic bytes, limite 2MB/2000 linhas, anti-CSV Injection, `dry_run` + commit), `endpoints/importacoes.py`, `api.py`, `main.py`. | `requirements.txt`, `schemas/importacao.py`, `services/importacao_service.py`, `endpoints/importacoes.py`, `api.py`, `main.py` | ~310 | `feat(importacoes): adicionar upload seguro csv e xlsx com dry-run` | PR 2 | Sim (revisão PR) |
| **PR 8** | `feat/frontend-importacoes-ui` | `ImportacaoService`, `ImportacaoModalComponent` reutilizável e botões de importação em `AdminComponent` (`salas`) e `SecretariaComponent` (`alunos`, `matriculas`). | `importacao.service.ts`, `importacao-modal.component.ts`, `admin.component.ts`, `secretaria.component.ts`, `api-contracts.ts` | ~240 | `feat(frontend): adicionar modal de importacao em lote com pre-visualizacao` | PR 7 | Sim (revisão PR) |
| **PR 9** | `feat/scheduler-apscheduler-cron` | `ENABLE_SCHEDULER` em `config.py`, `scheduler_service.py` (advisory lock PG), `lifespan` em `main.py`, `scripts/run_ia_job.py`, `--retrain` em `evaluate_model.py`, `docker/cron/crontab` + `entrypoint.sh`. | `config.py`, `services/scheduler_service.py`, `main.py`, `scripts/run_ia_job.py`, `scripts/evaluate_model.py`, `docker/cron/crontab`, `docker/cron/entrypoint.sh` | ~190 | `feat(scheduler): ativar apscheduler, cron real e retreinamento de ia` | PR 4 | Sim (revisão PR) |

---

## 5. Plano de Testes TDD (RED / GREEN / REFACTOR)

Esta seção utiliza exclusivamente listas numeradas e marcadores simples (sem caixas de seleção Markdown) para preservar o parsing exclusivo da Seção 6 pelo `scripts/clickup_sync.py`.

### 5.1 Atualizações Obrigatórias em Lockstep nos Testes Existentes

1. **PR 1 (`feat/audit-trail-completo`):**
   - `backend/tests/test_api_sugestoes.py:252,278`: atualizar asserção de `log_recente.tipo_evento` na aprovação de `TipoEventoLog.ALTERACAO` para `TipoEventoLog.REMANEJAMENTO`, e adicionar verificação de log na rejeição.
2. **PR 2 (`feat/matriculas-governanca-vagas`):**
   - `backend/tests/test_matriculas_lifecycle.py:102-124, 191-230`: atualizar cenários de `ALUNO` invocando `DELETE /api/v1/matriculas/{id}` para esperar `403 Forbidden`, movendo os fluxos discentes para `POST /solicitar-cancelamento` e `PATCH /decidir-cancelamento`.
   - `backend/tests/test_migrations.py:40-141`: validar `upgrade head` -> `downgrade -1` -> `upgrade head` contemplando `005_academic_flows_governance` (`turma.vagas`, `turma.prazo_cancelamento`, `matricula.*`, `uq_frequencia_matricula_horario_data`).
   - `backend/tests/test_turmas_matriculas.py:70-147`: manter compatibilidade dos testes sem `vagas` (`nullable=True`) e adicionar cenários explícitos com `vagas=1` retornando `409 Conflict` e checagem de `LogAlocacao`.
3. **PR 3 (`feat/frontend-matriculas-confirmacao`):**
   - `frontend/src/app/pages/components.spec.ts:96-164`: atualizar o teste de `[data-testid="btn-aluno-cancelar-matricula-100"]` para abrir a modal de solicitação, preencher o motivo (>= 10 chars), confirmar e verificar chamada a `solicitarCancelamento(100, motivo)`.
   - `frontend/src/app/pages/secretaria/secretaria.component.spec.ts:172-188`: atualizar o clique em `[data-testid="btn-cancelar-matricula-50"]` para confirmar na modal antes da chamada `cancelarMatricula(50)`.
   - `frontend/src/app/services/secretaria.service.spec.ts`: incluir cobertura de `solicitarCancelamento`, `decidirCancelamento` e `atualizarTurma`.
4. **PR 4 & PR 7 (`feat/backend-diario-frequencia`, `feat/backend-importacoes-lote`):**
   - `backend/tests/test_openapi_docs.py:9-29, 91-97`: registrar as novas tags `"Frequencias"` e `"Importacoes"` em `OPENAPI_TAGS` (`main.py`) e em `EXPECTED_TAGS` (`test_openapi_docs.py`).
5. **PR 6 (`feat/relatorios-exportacao-pdf`):**
   - `backend/tests/test_api_relatorios.py:449-458`: remover `?formato=pdf` da lista que espera `422` em `/relatorios/ocupacao-salas` e `/relatorios/remanejamentos` (mantendo `xlsx -> 422` e `/logs?formato=pdf -> 422`), e adicionar testes de geração PDF válida.
   - `frontend/src/app/pages/relatorios/relatorios.component.spec.ts` & `relatorio.service.spec.ts`: adicionar spies e testes para `exportarOcupacaoPdf`, `exportarRemanejamentosPdf` e `exportarGradeHorariaPdf`.

### 5.2 Novos Casos de Teste TDD (RED -> GREEN -> REFACTOR)

1. **Fase RED — Backend (`test_matriculas_lifecycle.py`, `test_importacoes.py`, `test_api_relatorios.py`, `test_frequencias.py`, `test_scheduler_ia.py`):**
   - `test_matriculas_lifecycle.py`: bloqueio `403` no `DELETE` por aluno; `400` após `prazo_cancelamento`; `409` ao exceder `Turma.vagas`; ciclo completo `solicitar` -> `rejeitar` (volta para `"ativa"`) -> `solicitar` -> `aprovar` (`"cancelada"` + decremento atômico + `LogAlocacao`).
   - `test_importacoes.py`: rejeição de arquivo `.exe` renomeado para `.xlsx` (`400`); rejeição de fórmula CSV `=1+1` (`422`); rejeição de arquivo > 2 MB (`413`); rollback integral quando linha 3 falha com `dry_run=false`; `dry_run=true` sem escrita em banco; isolamento de campus para Coordenador/Secretaria.
   - `test_api_relatorios.py`: `GET /api/v1/relatorios/ocupacao-salas?formato=pdf` e `/remanejamentos?formato=pdf` e `/grade-horaria?formato=pdf` retornam `200`, `application/pdf`, assinatura `%PDF-` e conteúdo textual contendo `Grupo 31` sem nomes de instituições externas.
   - `test_frequencias.py`: professor titular registra e atualiza chamada idempotente (`uq_frequencia_matricula_horario_data`); outro professor recebe `403`; matrícula `"cancelada"` recebe `400`; `extrair_dataset_frequencias` ignora aluno com matrícula `"cancelada"`.
   - `test_scheduler_ia.py`: `executar_rotina_ia_agendada()` treina e gera sugestões apenas pendentes, grava `origem_dados`, e `scripts/run_ia_job.py` executa ponta a ponta sem erro.
2. **Fase RED — Frontend (`professor.component.spec.ts`, `importacao-modal.component.spec.ts`):**
   - `professor.component.spec.ts`: clicar em aula da grade carrega lista de alunos ativos e envia `POST /api/v1/frequencias`.
   - `importacao-modal.component.spec.ts`: selecionar arquivo, disparar `dry_run=true`, exibir tabela de erros/preview e habilitar confirmação apenas quando `erros.length === 0`.
3. **Fase GREEN + REFACTOR — Comandos de Verificação:**
   - `pytest --cov=backend/app --cov-fail-under=85`
   - `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`
   - `bandit -r backend/app -ll` e `ruff check backend/app --select=S,B,E,F`
   - `npx ng test --watch=false --browsers=ChromeHeadless` e `npx ng build`
   - `npx openapi-typescript openapi.json -o frontend/src/app/core/models/api-contracts.ts`
   - `python scripts/check_pr_size.py origin/main 400`

---

## 6. Decomposição ClickUp e Portões (Gate 1 / Debate Adversarial / Gate 2)

### 6.1 Subtasks para Sincronização ClickUp (`clickup_sync.py sync-spec`)

- [ ] [SPEC-015-PR1] Completar trilha `LogAlocacao` em `cursos`, `disciplinas`, `salas`, `matriculas`, `sugestoes` (`REMANEJAMENTO` e rejeição) e corrigir `campus_id` em `scripts/seed_db.py`
- [ ] [SPEC-015-PR2] Criar migration `005_academic_flows_governance`, adicionar `Turma.vagas`/`prazo_cancelamento`, restringir `DELETE` do aluno, criar `/solicitar-cancelamento` e `/decidir-cancelamento`, checagem atômica `409` e `MatriculaRead` enriquecido
- [ ] [SPEC-015-PR3] Implementar modais de confirmação explícita com contexto acadêmico completo e fila de trancamento em `AlunoComponent`, `SecretariaComponent` e `SecretariaService`
- [ ] [SPEC-015-PR4] Implementar endpoints `GET/POST /api/v1/frequencias` (upsert idempotente) e filtrar `Matricula.status == "ativa"` em `ia_service.py`
- [ ] [SPEC-015-PR5] Implementar `FrequenciaService`, evento `aulaSelecionada` em `GradeHorariaComponent` e diário de chamada no `ProfessorComponent`
- [ ] [SPEC-015-PR6] Implementar `pdf_service.py` com `reportlab` (padrão ABNT Grupo 31 sem alucinações), `formato=pdf` em `relatorios.py`, `/grade-horaria`, sync OpenAPI em `main.py` e download PDF no Angular
- [ ] [SPEC-015-PR7] Implementar `POST /api/v1/importacoes/{salas|alunos|matriculas}` com `openpyxl`, validação MIME/magic bytes, limite 2MB/2000 linhas, anti-CSV Injection e `dry_run` transacional
- [ ] [SPEC-015-PR8] Implementar `ImportacaoService` e `ImportacaoModalComponent` integrados a `AdminComponent` e `SecretariaComponent`
- [ ] [SPEC-015-PR9] Ativar `APScheduler` no `lifespan` do FastAPI com advisory lock PostgreSQL, `scripts/run_ia_job.py`, `--retrain` em `evaluate_model.py` e corrigir `docker/cron/crontab` + `entrypoint.sh`

### 6.2 Protocolo de Portões e Auditoria (AGENTS.md §5-7)

1. **Gate 1 (Pré-Implementação):** Aprovação formal desta especificação `[SPEC-015]` antes de abrir branches ou alterar código-fonte, seguida do comando `python scripts/clickup_sync.py sync-spec docs/specs/spec-fluxos-matricula-academico.md`.
2. **Debate Adversarial Multi-Agente Pré-PR:** Execução obrigatória antes de cada PR com `advocate-mapper`, `adversary-breaker`, `adversary-security`, `adversary-compliance` e `debate-arbiter`, incluindo loop de Re-Review sobre `git diff origin/main...HEAD` até aprovação unânime sem vetos.
3. **Inspeção CodeRabbit AI & Fallback:** Leitura obrigatória de comentários via `gh pr view <PR> --comments`; em caso de rate limit do CodeRabbit, utilizar o veredito do debate adversarial local.
4. **Gate 2 (Pré-Merge Human-in-the-Loop):** Aprovação humana explícita obrigatória antes de executar PR 1 (`sugestoes.py`), PR 2 (migration `005_academic_flows_governance` e `matriculas.py`) e antes de qualquer `gh pr merge <PR> --squash --delete-branch` em `main`.
