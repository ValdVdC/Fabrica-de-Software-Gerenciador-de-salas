---
name: owasp-api-security
description: >-
  Security auditing for REST APIs covering OWASP API Security Top 10, Broken Object Level
  Authorization (BOLA/IDOR), Broken Function Level Authorization (BFLA), JWT best practices,
  and multi-tenant data leak prevention. Use when reviewing endpoints or auditing security.
---

# OWASP API Security Top 10 Checklist

Audit protocol to ensure bulletproof security across all FastAPI endpoints in SIGAAS.

## 1. Top Vulnerabilities & Defenses

### API1:2023 Broken Object Level Authorization (BOLA / IDOR)
- **Threat**: User alters `/api/v1/salas/15` to `/api/v1/salas/16` to access or modify a room belonging to another campus.
- **Defense**: Always filter by the authenticated user's `campus_id` directly in database queries, never trusting IDs supplied in path or query parameters alone.
  ```python
  sala = await session.execute(
      select(Sala).where(Sala.id == sala_id, Sala.campus_id == current_user.campus_id)
  )
  ```

### API2:2023 Broken Authentication (JWT Security)
- **Threat**: Weak secret keys, lack of expiration, algorithm confusion (`none`), or sensitive tokens exposed in URLs.
- **Defense**:
  - Sign JWTs using `HS256` or `RS256` with strong environment secret keys (minimum 256 bits).
  - Enforce short expiration (`exp` <= 60 minutes) and explicit audience (`aud`) and issuer (`iss`) checks.
  - Store tokens in memory or HTTP-only cookies; never log tokens in request bodies or query strings.

### API5:2023 Broken Function Level Authorization (BFLA)
- **Threat**: Regular teachers or students invoking administrative endpoints (e.g. `POST /api/v1/motor/alocar` or `PATCH /api/v1/sugestoes/{id}`).
- **Defense**: Guard every administrative router with explicit role-based dependencies:
  ```python
  async def require_admin(user: Usuario = Depends(get_current_user)):
      if user.perfil not in ["admin", "coordenador"]:
          raise HTTPException(status_code=403, detail="Acesso restrito a coordenacao")
  ```

### API3:2023 Broken Object Property Level Authorization (Mass Assignment)
- **Threat**: Attacker sends `{"ativo": true, "is_admin": true}` in a user update payload.
- **Defense**: Use strict Pydantic schemas with only the allowed mutable fields declared. Never use `db_model(**request_dict)`.

## 2. Automated Security Audit Commands

Before submitting code for review, run automated static analysis:

```bash
# Bandit AST security scanner
bandit -r backend/app -ll

# Ruff security and bug linter
ruff check backend/app --select=S,B,E,F
```
