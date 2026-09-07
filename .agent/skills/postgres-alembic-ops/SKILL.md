---
name: postgres-alembic-ops
description: >-
  Relational database schema management with PostgreSQL and Alembic, zero-downtime migration
  safeguards, multi-campus tenant isolation, and composite index design for timetable queries.
  Use when creating models, writing Alembic migrations, or optimizing PostgreSQL queries.
---

# PostgreSQL & Alembic Operations Guide

Standards for database modeling, safe schema migrations, and multi-tenant isolation in SIGAAS.

## 1. Migration Safeguards & Idempotency

- **Rule 1: Always Pair Model Changes with an Alembic Migration**: Never commit changes to `SQLAlchemy` models without generating and verifying the corresponding migration script in `backend/alembic/versions/`.
- **Rule 2: Fully Reversible**: Both `upgrade()` and `downgrade()` must be implemented and tested with:
  ```bash
  alembic upgrade head && alembic downgrade -1 && alembic upgrade head
  ```
- **Rule 3: Non-Blocking Schema Changes**:
  - When adding columns to large tables, always provide a server default: `server_default=sa.text('...')` or allow `nullable=True`.
  - Avoid table rewrite locks in production migrations.

## 2. Multi-Campus Tenant Isolation (`campus_id`)

Every entity tied to physical or operational spaces must enforce multi-tenancy:
- Tables `Sala`, `Turma`, `Horario`, `Frequencia`, `SugestaoRemanejamento` must include `campus_id: int = Column(ForeignKey("campus.id", ondelete="CASCADE"), nullable=False)`.
- Enforce foreign keys with indexed columns to optimize joins and cascading checks.

## 3. Composite Indexes for Timetable Grid Queries

The allocation grid executes high-frequency queries filtering by day, time, and room:

```python
# Model Sala / Horario
__table_args__ = (
    Index("ix_horario_campus_dia_slot", "campus_id", "dia_semana", "horario_inicio"),
    Index("ix_horario_sala_conflito", "sala_id", "dia_semana", "horario_inicio", "horario_fim"),
    UniqueConstraint("sala_id", "dia_semana", "horario_inicio", name="uq_sala_horario_ocupado"),
)
```

- Use `EXPLAIN (ANALYZE, BUFFERS)` to verify query plans on complex schedule conflict detections.
