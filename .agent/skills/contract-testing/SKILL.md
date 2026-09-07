---
name: contract-testing
description: >-
  Validating API contracts between FastAPI OpenAPI schemas and Angular frontend HTTP services,
  preventing silent payload drift, schema mismatch, and type desynchronization. Use when exposing
  new API endpoints or creating Angular services.
---

# Contract Testing: OpenAPI ↔ Angular Sync

Methodology for ensuring strong typing, schema fidelity, and zero payload breakage between the FastAPI backend and Angular client.

## 1. Single Source of Truth: OpenAPI Schema

FastAPI automatically generates the OpenAPI v3 specification from Pydantic models. This schema defines the exact wire contract:
- Field names and types (e.g. `snake_case` vs `camelCase`).
- Nullability, optionality, and default values.
- HTTP status codes (200, 201, 400, 401, 403, 404, 422).

## 2. Generating TypeScript Interfaces

To avoid manual, error-prone TypeScript interface definitions in Angular, validate or generate models using `openapi-typescript`:

```bash
# Export schema from FastAPI app
python -c "import json; from app.main import app; print(json.dumps(app.openapi()))" > openapi.json

# Generate TypeScript types
npx openapi-typescript openapi.json -o frontend/src/app/core/models/api-contracts.ts
```

## 3. Angular Service Contract Guidelines

- **Typed HTTP Calls**: Never use `HttpClient.get<any>()`. Always bind to the generated interface:
  ```typescript
  getCampi(): Observable<CampusRead[]> {
    return this.http.get<CampusRead[]>(`${this.apiUrl}/campi`);
  }
  ```
- **Error Response Handling**: Handle standardized FastAPI error envelopes (`detail: string` or `detail: ValidationError[]`) uniformly in an HTTP interceptor.
- **Contract Verification Test**: Add integration tests asserting that the backend response payload deserializes cleanly into the Angular model without missing required properties.
