---
name: doc-drift-sync
description: >-
  Preventing documentation drift, synchronizing architectural specs (docs/specs/),
  database schemas, AGENTS.md, and OpenAPI documentation with active codebase implementations.
  Use when closing a sprint, modifying schemas, or refactoring architectural components.
---

# Doc Drift & Schema Sync Protocol

Procedures to maintain absolute synchronization between the living codebase, architectural specifications, database schemas, and normative repository guidelines.

## 1. The Threat of Documentation Drift

In fast-paced multi-agent workflows, code often evolves faster than documentation:
- Database columns are added without updating the architecture markdown.
- Endpoints are renamed, but specs in `docs/specs/` still reference deprecated paths.
- Rules in `AGENTS.md` fall out of lockstep with real CI scripts.

This drift causes subsequent agent sessions to hallucinate obsolete structures.

## 2. Sync Verification Checklist

Whenever a PR alters database models, API routes, or squad conventions, verify:

1. **Spec Alignment (`docs/specs/<sprint>-*.md`)**:
   - Are all implemented endpoints listed in the spec?
   - Do the Gherkin scenarios match the actual Pytest test names and assertions?
2. **Database Architecture (`docs/projeto-gestao-salas-escalas.md`)**:
   - If a table or foreign key was added via Alembic, update the Mermaid ER diagram and the schema table list.
3. **API Contract Verification**:
   - Check that OpenAPI docs (`http://localhost:8000/docs`) accurately reflect query parameters, path variables, and status codes.
4. **Handoff & Sprint Changelog (`docs/handoff-guide.md`)**:
   - Document merged PRs, active branch state, and open questions before handing off to the next sprint.

## 3. Atomic Updates

- **Never postpone documentation to a future sprint**: Update the corresponding documentation in the same PR or in an immediate follow-up `docs(...)` PR.
- Because `docs/**` and `*.md` files are exempt from the 400-line diff limit in `scripts/check_pr_size.py`, keeping docs fresh never penalizes the developer's diff budget.
