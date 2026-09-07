---
name: sigaas-academic-ui
description: >-
  Design system and UI architecture specifically tailored for SIGAAS Angular frontend.
  Covers high-density timetable scheduling, room allocation matrix, conflict visualization,
  profile-based navigation, Lucide icons, and Tailwind token architecture. Use whenever
  scaffolding, building, or styling Angular components in SIGAAS.
---

# SIGAAS Academic UI & Design System

Normative frontend design and token system for the SIGAAS Academic Room & Schedule Management platform.

## Architecture & Responsibilities

- **Pure Presentation**: The Angular SPA contains zero business logic, scheduling logic, or direct database access. All data is fetched from the FastAPI backend.
- **Iconography (Inviolable)**: Zero emojis allowed anywhere in UI or copy. Use exclusively Lucide Icons (`lucide-angular`) with uniform 16px/20px stroke and size.
- **Profiles**:
  - **Admin / Coordenacao**: Dense operational dashboard, multi-campus selector, engine trigger, conflict resolver, suggestions approval.
  - **Professor**: Personal schedule, assigned rooms, absence reporting, remanejamento tracking.
  - **Aluno**: Clean timetable view, room directions/locations, real-time change indicators.
  - **Secretaria**: Search, rapid room lookups, occupancy reports.

## High-Density Timetable & Room Matrix

Academic scheduling requires information density without cognitive overload:

1. **Grid Organization**:
   - Columns: Days of week (Segunda a Sabado) or Rooms (Salas 101-305).
   - Rows: Time slots (e.g. M1-M5: 07:00-11:40, T1-T5: 13:00-17:40, N1-N4: 18:30-22:00).
   - Sticky headers for both axes with non-colliding scroll containers.
2. **Cell States & Accessibility**:
   - **Livre (Available)**: Subtle neutral border, muted label, clear hover affordance.
   - **Alocado (Allocated)**: Solid surface, course code + professor abbreviation + room badge.
   - **Conflito (Conflict)**: Rose accent with alert icon (`AlertTriangle`). Never rely on color alone.
   - **Sugestao Pendente (Pending Remanejamento)**: Amber accent with clock icon (`Clock3`), badge showing predicted absenteeism rate.
3. **Tabular Numerals**:
   - Always apply `font-variant-numeric: tabular-nums` (`tabular-nums` in Tailwind) to all time spans, room numbers, and capacity counters.

## Token Architecture (Tailwind CSS)

### Three-Layer Structure

```text
Primitive (palette values)
       ↓
Semantic (purpose tokens: background, surface, text, border, status)
       ↓
Component (timetable-cell-conflict, timetable-header, profile-badge)
```

### Academic Color System

- **Neutrals**: Slate family (`slate-50` through `slate-950`) for crisp readability under varying monitor calibrations.
- **Primary / Identity**: Deep Navy (`#1E293B` to `#0F172A`) giving an authoritative, institutional feel.
- **Status Indicators**:
  - Success / Available: Emerald (`emerald-600` / `emerald-50`)
  - Info / Standard Allocation: Blue (`blue-600` / `blue-50`)
  - Warning / Pendente IA: Amber (`amber-600` / `amber-50`)
  - Danger / Conflito Alocacao: Rose (`rose-600` / `rose-50`)

## Component Specification Standard

| Component | Default State | Hover / Focus-Visible | Active / Selected |
| :--- | :--- | :--- | :--- |
| **Grid Cell** | Border `slate-200`, bg `white` | Border `slate-400`, ring-1 | Bg `slate-50`, ring-2 `navy-600` |
| **Conflict Badge** | Bg `rose-50`, text `rose-700`, icon | Scale-102, ring-1 `rose-300` | Opens conflict resolution drawer |
| **Remanejamento Card** | Bg `amber-50`, border `amber-200` | Border `amber-400`, shadow-sm | Displays approve/reject actions |
| **Action Button** | Bg `navy-800`, text `white`, rounded | Bg `navy-900`, ring-2 focus | Transform active:scale-98 |

## Anti-AI-Slop Rules for SIGAAS

1. No generic rounded SaaS cards with massive diffuse shadows. Use crisp 1px borders (`border-slate-200`) and subtle shadows (`shadow-sm`).
2. No unnecessary uppercase eyebrow labels. Section titles are clean sentence-case headings.
3. No decorative gradient text.
4. No emojis under any circumstance. Replace with Lucide icons (`Calendar`, `Clock`, `MapPin`, `Users`, `CheckCircle2`, `AlertTriangle`).
5. Design for real academic strings: accommodate long course names (e.g. "Algoritmos e Estruturas de Dados II") without clipping or layout breakage using `truncate` with full tooltip on hover.

## Detailed Reference Guides

Consult the dedicated manuals for deep implementation specifications:

| Manual | Reference File | Coverage |
| :--- | :--- | :--- |
| **Token System & Tailwind** | [references/token-architecture.md](references/token-architecture.md) | Variáveis CSS, mapeamento Tailwind e contraste WCAG |
| **Matriz e Grade Horária** | [references/timetable-matrix-patterns.md](references/timetable-matrix-patterns.md) | Dimensões M1-N4, sticky headers e responsividade |
| **Alertas & Remanejamento** | [references/conflict-remanejamento-badges.md](references/conflict-remanejamento-badges.md) | Badges de conflito, aprovação de IA e Lucide Icons |
