---
name: fastapi-domain-patterns
description: >-
  Clean architecture for FastAPI, layered separation (Routers -> Services -> Repositories),
  strict Pydantic v2 schemas, asynchronous dependency injection, and N+1 query prevention.
  Use when designing, scaffolding, or refactoring backend routes and business services.
---

# FastAPI Domain Patterns & Clean Architecture

Architectural guidelines for modular, maintainable, and type-safe backend services in SIGAAS.

## 1. Layered Domain Architecture

Maintain strict directional dependencies:

```text
HTTP Clients (Angular / Tests)
       ↓
Routers (`backend/app/routers/`): Request parsing, status codes, OpenAPI doc
       ↓
Services (`backend/app/services/`): Business orchestration, validations, engine calls
       ↓
Repositories / Models (`backend/app/models/`): Database access via async SQLAlchemy
```

- **Routers never execute raw queries**: Routers only call Services or Repositories injected via `Depends()`.
- **Services never handle HTTP objects**: Services deal exclusively with domain models, primitives, and Pydantic schemas; they do not manipulate `Request` or `Response` directly.

## 2. Pydantic v2 Validation Standards

- Use `model_config = ConfigDict(from_attributes=True)` on read schemas.
- Provide explicit field constraints using `Field(...)` with descriptions, examples, and bounds.
- Separate schemas into functional variants:
  - `<Entity>Create`: Required fields for creation.
  - `<Entity>Update`: All fields optional (`None`) for PATCH semantics.
  - `<Entity>Read`: Response payload including primary keys and timestamps.

```python
from pydantic import BaseModel, Field, ConfigDict

class CampusBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, description="Nome do campus")
    sigla: str = Field(..., min_length=2, max_length=10, description="Sigla institucional")

class CampusCreate(CampusBase):
    pass

class CampusRead(CampusBase):
    id: int
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
```

## 3. Asynchronous Database Sessions & N+1 Prevention

- Always yield sessions using `async_sessionmaker`:
  ```python
  async def get_db() -> AsyncGenerator[AsyncSession, None]:
      async with async_session() as session:
          yield session
  ```
- **Prevent N+1 Queries**: When loading relationships (e.g. `Turma.sala` or `Horario.disciplina`), always use eager loading via `selectinload()` or `joinedload()`.
- Enforce tenant boundary on every query: `select(Model).where(Model.campus_id == current_tenant_id)`.
