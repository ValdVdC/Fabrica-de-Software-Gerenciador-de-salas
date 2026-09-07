---
name: adversarial-code-reviewer
description: >-
  Adversarial review protocol for multi-agent committees, searching for concurrency deadlocks,
  edge cases, null input crashes, and boundary condition violations before opening PRs.
  Use when performing pre-PR dialectical reviews or auditing candidate code.
---

# Adversarial Code Reviewer Playbook

Systematic methodology for subagents acting as the adversarial red team to identify defects, edge cases, and hidden assumptions in candidate pull requests.

## 1. Persona Attack Angles

When conducting an adversarial review, attack the code across four specialized dimensions:

### A. The Breaker (`adversary-breaker`)
- **Boundary Conditions**: Zero capacity, negative values, empty lists, maximum integer limits.
- **Null / None Inputs**: Missing keys in JSON, nullable database fields accessed without guards.
- **Concurrency & Race Conditions**: Two requests booking the same room simultaneously; async tasks modifying shared state without locks.
- **Clock & Time Drift**: Date/time zone mismatches, midnight edge cases, leap years.

### B. The Security Assailant (`adversary-security`)
- **Tenant Isolation**: Can user from Campus A inject Campus B's ID?
- **Auth Bypasses**: Are route decorators correctly ordered? Does `Depends(get_current_user)` actually block unauthenticated requests?
- **SQL / Command Injection**: Are all queries parameterized? Does any C call use unescaped string formatting?

### C. The Compliance Auditor (`adversary-compliance`)
- **10 Inviolable Rules**: Zero business logic in Angular, zero direct DB access in C, migrations present, zero emojis.
- **Diff Ceiling**: Production code changes must not exceed 400 lines.

## 2. Review Protocol & Verdict Formulation

Reviewers must format findings concisely and conclude with an unequivocal verdict:

```markdown
## Adversarial Audit Report

### Critical Vulnerabilities / Edge Cases Found
1. `backend/app/routers/salas.py:45` - Missing `campus_id` filter allows horizontal privilege escalation.
2. `backend/motor_alocacao/motor.c:112` - Buffer overflow risk if `total_turmas > 1024`.

### Verification Tests
- [Code snippet demonstrating the exploit or failing test case]

### Formal Verdict
- [VETO BLOQUEANTE / CONCESSAO COM RESSALVA / APROVADO]
```

- Any **VETO BLOQUEANTE** immediately halts PR creation and routes the task back to the developer for remediation.
