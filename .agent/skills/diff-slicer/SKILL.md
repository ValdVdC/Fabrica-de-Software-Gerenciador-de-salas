---
name: diff-slicer
description: >-
  Strategies for atomic feature slicing and managing pull request diff limits (<= 300 to 400 lines
  of code) without breaking compilation, contracts, or test suites. Use when decomposing complex specs
  or preparing PRs under strict size governance.
---

# Diff Slicer: Atomic PR Decomposition

Operational playbook to partition complex functional requirements into independent, incrementally testable pull requests respecting the 300-400 line code limit.

## 1. Principles of Atomic Slicing

- **Self-Contained Deliverables**: Every PR must compile, pass all linting, pass all unit tests, and avoid leaving broken states in `main`.
- **Dependency Inversion Ordering**: Implement the deepest dependency layers first, moving outward toward controllers and UI.
- **Exemptions vs Enforced Lines**: Remember that documentation (`docs/`), specs, database migrations, lockfiles, and `.agent/` rule files are exempt from the 400-line code limit. The limit applies strictly to production logic (`.py`, `.c`, `.h`, `.ts`, `.html`).

## 2. Canonical Slicing Playbook for Full-Stack Features

When a user story exceeds ~350 lines of implementation, partition into 3 distinct PRs:

```text
PR 1: Models & Schemas (Backend Data Foundation)
  ├── SQLAlchemy / SQLModel models
  ├── Alembic migration (exempt from size)
  ├── Pydantic v2 validation schemas
  └── TDD Unit tests for schema validation

PR 2: Core Domain Logic & Services (Backend Logic & Endpoints)
  ├── Domain service classes & repository functions
  ├── Modular FastAPI routers with dependencies
  └── TDD Integration tests with test database

PR 3: Presentation & Client Consumption (Frontend SPA)
  ├── Angular standalone components & templates
  ├── HTTP service consuming backend endpoints
  └── Component unit tests & route guards
```

## 3. Pre-PR Diff Verification Command

Before opening any pull request, always verify production code line count:

```bash
python scripts/check_pr_size.py origin/main 400
```

If the audit fails:
1. Identify non-essential helper functions and move them to a subsequent PR.
2. Remove dead boilerplate or redundant code.
3. If necessary, split the router into two distinct domain modules.
