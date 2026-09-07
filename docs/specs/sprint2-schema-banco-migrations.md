# [SPEC-003] Schema PostgreSQL, Models SQLAlchemy 2.0 e Migrations Alembic

- **Sprint:** Sprint 2
- **Autor / Agente:** Planner-SDD (Antigravity)
- **Status:** Em Revisao
- **Data de Criacao:** 2026-09-07
- **ID ClickUp (Epico/Task):** 86e35a8uw

---

## 1. Contexto e Objetivos

O SIGAAS necessita de uma camada de persistencia relacional robusta, transacional e escalavel. Este documento especifica o schema fisico completo no PostgreSQL (14 tabelas), a implementacao dos modelos ORM com SQLAlchemy 2.0 moderno (`DeclarativeBase` e `Mapped[T]`), o versionamento estrutural via migrações Alembic e a carga de dados iniciais (seed) idempotente.

---

## 2. Decisoes Tecnicas Fundamentais

1. **Identificadores (PKs)**: Inteiros sequenciais (`Integer` / `BigInteger` com autoincremento/IDENTITY) para permitir interoperabilidade direta com vetores de estruturas de alocacao em C (`ctypes`).
2. **Campos Categoricos / Enums**: Mapeados como `VARCHAR` com `native_enum=False` e validacao estrita no modelo Python (`enum.Enum`), garantindo compatibilidade total e migrações Alembic sem bloqueios de DDL transacional no PostgreSQL.
3. **Controle Temporal**: Colunas padrao `created_at` e `updated_at` com timezone (`DateTime(timezone=True)`).
4. **Isolamento Multi-Campus**: Coluna `campus_id` indexada em tabelas de fronteira (`usuario`, `sala`, `curso`).

---

## 3. Especificacao Detalhada das Tabelas (DDL Relacional)

### 3.1 Entidades de Infraestrutura e Autenticacao

#### Tabela `campus`
- `id`: Integer, Primary Key, Autoincrement
- `nome`: String(150), Not Null
- `cidade`: String(100), Not Null
- `endereco`: String(255), Not Null
- `ativo`: Boolean, Default True, Not Null
- `created_at`: DateTime(timezone=True), Server Default now()
- `updated_at`: DateTime(timezone=True), Server Default now(), On Update now()

#### Tabela `usuario`
- `id`: Integer, Primary Key, Autoincrement
- `campus_id`: Integer, ForeignKey("campus.id", ondelete="RESTRICT"), Not Null, Index
- `nome`: String(150), Not Null
- `email`: String(255), Unique, Not Null, Index
- `senha_hash`: String(255), Not Null
- `perfil`: String(30), Not Null (Valores: admin, coordenador, professor, aluno, secretaria)
- `ativo`: Boolean, Default True, Not Null
- `created_at`: DateTime(timezone=True), Server Default now()
- `updated_at`: DateTime(timezone=True), Server Default now(), On Update now()

#### Tabela `equipamento`
- `id`: Integer, Primary Key, Autoincrement
- `nome`: String(100), Unique, Not Null
- `descricao`: String(255), Nullable
- `created_at`: DateTime(timezone=True), Server Default now()

#### Tabela `sala`
- `id`: Integer, Primary Key, Autoincrement
- `campus_id`: Integer, ForeignKey("campus.id", ondelete="RESTRICT"), Not Null, Index
- `bloco`: String(50), Not Null
- `numero`: String(50), Not Null
- `tipo`: String(30), Not Null (Valores: regular, laboratorio, auditorio, reuniao)
- `capacidade`: Integer, Not Null (Check: capacidade > 0)
- `turnos_disponiveis`: String(100), Not Null (Ex.: "matutino,vespertino,noturno")
- `ativo`: Boolean, Default True, Not Null
- `created_at`: DateTime(timezone=True), Server Default now()
- `updated_at`: DateTime(timezone=True), Server Default now(), On Update now()
- *Constraint*: `UniqueConstraint("campus_id", "bloco", "numero", name="uq_sala_campus_bloco_numero")`

#### Tabela `sala_equipamento` (Associativa N-N)
- `sala_id`: Integer, ForeignKey("sala.id", ondelete="CASCADE"), Primary Key
- `equipamento_id`: Integer, ForeignKey("equipamento.id", ondelete="RESTRICT"), Primary Key
- `quantidade`: Integer, Default 1, Not Null (Check: quantidade > 0)

---

### 3.2 Entidades Academicas

#### Tabela `curso`
- `id`: Integer, Primary Key, Autoincrement
- `campus_id`: Integer, ForeignKey("campus.id", ondelete="RESTRICT"), Not Null, Index
- `nome`: String(150), Not Null
- `codigo`: String(30), Not Null
- `created_at`: DateTime(timezone=True), Server Default now()
- `updated_at`: DateTime(timezone=True), Server Default now(), On Update now()
- *Constraint*: `UniqueConstraint("campus_id", "codigo", name="uq_curso_campus_codigo")`

#### Tabela `disciplina`
- `id`: Integer, Primary Key, Autoincrement
- `curso_id`: Integer, ForeignKey("curso.id", ondelete="RESTRICT"), Not Null, Index
- `nome`: String(150), Not Null
- `codigo`: String(30), Not Null
- `carga_horaria`: Integer, Not Null (Check: carga_horaria > 0)
- `created_at`: DateTime(timezone=True), Server Default now()
- `updated_at`: DateTime(timezone=True), Server Default now(), On Update now()
- *Constraint*: `UniqueConstraint("curso_id", "codigo", name="uq_disciplina_curso_codigo")`

#### Tabela `turma`
- `id`: Integer, Primary Key, Autoincrement
- `disciplina_id`: Integer, ForeignKey("disciplina.id", ondelete="RESTRICT"), Not Null, Index
- `professor_id`: Integer, ForeignKey("usuario.id", ondelete="SET NULL"), Nullable, Index
- `periodo_letivo`: String(20), Not Null, Index (Ex.: "2026.1")
- `num_matriculados`: Integer, Default 0, Not Null (Check: num_matriculados >= 0)
- `turno_preferido`: String(20), Not Null (Valores: matutino, vespertino, noturno, integral)
- `created_at`: DateTime(timezone=True), Server Default now()
- `updated_at`: DateTime(timezone=True), Server Default now(), On Update now()

#### Tabela `matricula`
- `id`: Integer, Primary Key, Autoincrement
- `aluno_id`: Integer, ForeignKey("usuario.id", ondelete="RESTRICT"), Not Null, Index
- `turma_id`: Integer, ForeignKey("turma.id", ondelete="CASCADE"), Not Null, Index
- `data_matricula`: Date, Server Default now(), Not Null
- `status`: String(20), Default "ativa", Not Null
- `created_at`: DateTime(timezone=True), Server Default now()
- *Constraint*: `UniqueConstraint("aluno_id", "turma_id", name="uq_matricula_aluno_turma")`

---

### 3.3 Entidades de Alocacao e Inteligencia Artificial

#### Tabela `horario`
- `id`: Integer, Primary Key, Autoincrement
- `turma_id`: Integer, ForeignKey("turma.id", ondelete="CASCADE"), Not Null, Index
- `sala_id`: Integer, ForeignKey("sala.id", ondelete="RESTRICT"), Not Null, Index
- `dia_semana`: SmallInteger, Not Null (Valores: 0=Segunda a 6=Domingo)
- `hora_inicio`: Time, Not Null
- `hora_fim`: Time, Not Null
- `created_at`: DateTime(timezone=True), Server Default now()
- `updated_at`: DateTime(timezone=True), Server Default now(), On Update now()
- *Constraint*: `UniqueConstraint("sala_id", "dia_semana", "hora_inicio", name="uq_horario_sala_dia_hora")`

#### Tabela `frequencia` (Base de Treinamento da IA)
- `id`: Integer, Primary Key, Autoincrement
- `matricula_id`: Integer, ForeignKey("matricula.id", ondelete="CASCADE"), Not Null, Index
- `horario_id`: Integer, ForeignKey("horario.id", ondelete="CASCADE"), Not Null, Index
- `data`: Date, Not Null, Index
- `presente`: Boolean, Not Null
- `created_at`: DateTime(timezone=True), Server Default now()

#### Tabela `previsao_falta`
- `id`: Integer, Primary Key, Autoincrement
- `turma_id`: Integer, ForeignKey("turma.id", ondelete="CASCADE"), Not Null, Index
- `horario_id`: Integer, ForeignKey("horario.id", ondelete="CASCADE"), Not Null, Index
- `data_prevista`: Date, Not Null
- `prob_ausencia`: Float, Not Null
- `versao_modelo`: String(50), Not Null
- `criado_em`: DateTime(timezone=True), Server Default now()

#### Tabela `sugestao_remanejamento`
- `id`: Integer, Primary Key, Autoincrement
- `horario_id`: Integer, ForeignKey("horario.id", ondelete="CASCADE"), Not Null, Index
- `sala_atual_id`: Integer, ForeignKey("sala.id", ondelete="RESTRICT"), Not Null
- `sala_sugerida_id`: Integer, ForeignKey("sala.id", ondelete="RESTRICT"), Not Null
- `motivo`: Text, Not Null
- `status`: String(20), Default "pendente", Not Null (Valores: pendente, aprovado, rejeitado)
- `aprovado_por`: Integer, ForeignKey("usuario.id", ondelete="SET NULL"), Nullable
- `criado_em`: DateTime(timezone=True), Server Default now()
- `atualizado_em`: DateTime(timezone=True), Server Default now(), On Update now()

#### Tabela `log_alocacao` (Auditoria)
- `id`: Integer, Primary Key, Autoincrement
- `horario_id`: Integer, ForeignKey("horario.id", ondelete="CASCADE"), Not Null, Index
- `tipo_evento`: String(50), Not Null (Valores: criacao, remanejamento, cancelamento)
- `usuario_responsavel`: Integer, ForeignKey("usuario.id", ondelete="RESTRICT"), Not Null
- `detalhes`: Text, Nullable
- `timestamp`: DateTime(timezone=True), Server Default now(), Index

---

## 4. Estrutura de Arquivos e Modulos

```
backend/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── app/
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   └── models/
│       ├── __init__.py
│       ├── base.py
│       ├── campus.py
│       ├── usuario.py
│       ├── sala.py
│       ├── academico.py
│       ├── alocacao.py
│       └── ia.py
└── tests/
    └── test_models.py
scripts/
└── seed_db.py
```

---

## 5. Plano de Testes TDD (Fase RED)

### 5.1 Testes de Integridade Estrutural e Modelos
- [ ] `tests/test_models.py::test_create_tables`: Valida criacao de todas as 14 tabelas sem erros de definicao.
- [ ] `tests/test_models.py::test_campus_usuario_relationship`: Valida associacao 1-N entre Campus e Usuario.
- [ ] `tests/test_models.py::test_unique_email_constraint`: Valida rejeicao de emails duplicados em Usuario.
- [ ] `tests/test_models.py::test_unique_sala_constraint`: Valida restricao uq_sala_campus_bloco_numero.
- [ ] `tests/test_models.py::test_sala_equipamento_cascade`: Valida que remocao de sala remove associacoes mas preserva o equipamento.
- [ ] `tests/test_models.py::test_matricula_unique_constraint`: Valida restricao de unicidade aluno_id + turma_id.
- [ ] `tests/test_models.py::test_horario_conflict_constraint`: Valida conflito de horario para mesma sala no mesmo dia/hora.
- [ ] `tests/test_models.py::test_sugestao_remanejamento_status_default`: Valida status inicial pendente.

---

## 6. Decomposicao de Tarefas para o ClickUp

- [ ] [SDD] Definir schema relacional e contratos tecnicos das 14 tabelas
- [ ] [TDD] Criar suíte de testes de schema e relacionamentos em SQLite em memoria
- [ ] [Backend] Implementar classes DeclarativeBase e Mapped[T] em app/models/
- [ ] [Backend] Configurar SQLAlchemy Engine e sessionmaker em app/db/session.py
- [ ] [Backend] Configurar ambiente Alembic e gerar migration inicial 001_initial_schema.py
- [ ] [Backend] Implementar script de carga de dados iniciais scripts/seed_db.py
