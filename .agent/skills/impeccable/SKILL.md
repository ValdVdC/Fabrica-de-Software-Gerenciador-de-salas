---
name: impeccable
description: >-
  Design director intelligence and craft floor for UI design, critique, visual hierarchy,
  spacing, depth, typography, cognitive load, and production-grade polish. Use when designing,
  refining, or reviewing any frontend component or view.
---

# Impeccable Design & Craft Floor

Approach every design task as an award-winning design director with an understanding of production-grade code, peak creativity, and craft.

## Core Principles

- **No Hedging or Shortcuts**: Deliverables must be complete and production-grade.
- **Bounded Passes**: Build fully, inspect once with a batched round (desktop and mobile together), fix everything in one batch, confirm with at most one more round, and stop. Avoid open-ended polish loops.
- **Refinement Preserves; Redesign Replaces**: Refinement keeps incumbent identity, behavior, and copy. Redesign keeps product truth and function, but replaces visual treatment deliberately.

## Craft Floor Verification

Verify built results across these dimensions:
- **Contrast**: Body and placeholder text >= 4.5:1, large text >= 3:1. On colored surfaces tint secondary text from that hue or foreground, never neutral gray.
- **Depth**: Shadows carry an intentional offset and soft blur. Zero-offset colored halos are banned.
- **Spacing Rhythm**: Tight logical groups, generous separation between sections, always more space above a heading than below it.
- **Typography Floor**: Body measure 65-75ch, display max 6rem, tracking floor -0.04em, balanced headings, obvious scale and weight steps. Test real copy at all breakpoints.
- **Motion**: One authored moment, not scattered effects. Exponential ease-out from an already-visible default. Use blur, clip-path, and shadow smoothly rather than ubiquitous card entrance fades.
- **States Matrix**: Complete definitions for default, hover, active, focus-visible, disabled, loading, error, and empty states.
- **Browser Surfaces**: Theme text selection, caret, custom scrollbars, and focus rings from the palette.

## Absolute Bans & Refusals

- **Same-Size Card Grids**: Same-size cards of icon plus heading plus text as the primary page scaffold are banned. Cards are lazy containers; nested cards are prohibited.
- **Hero-Metric Clichés**: Avoid the generic "big number + small label + supporting stat + gradient" template.
- **Eyebrows on Every Section**: Never place a tracked-out uppercase kicker above a heading. Let the heading carry its own weight.
- **Numbered Section Markers**: No 01 / 02 / 03 markers unless the content is genuinely a sequential process.
- **Modals by Reflex**: Do not use modals for tasks that require neither interruption nor protected focus.
- **Gradient Text**: Banned. Emphasis comes from typographic weight, size, or contrast.
- **Decorative Glassmorphism**: Blurs and translucent glass must have functional depth purposes, not mere decoration.
- **Side-Stripe Borders**: Thick colored left or right borders (> 1px) on cards or alerts are banned.
- **Hard Offset Shadows**: No `box-shadow: 4px 4px 0` unless the system is genuinely neobrutalist.
- **Unicode Glyphs / Emojis as Icons**: Strictly prohibited. All icons must come from an authored SVG or vetted icon library (e.g. Lucide Icons) with consistent stroke and weight.

## Reference Manuals Index

When tackling specific design tasks, consult the detailed guides in the `reference/` directory:

| Design Task | Reference File | Focus Area |
| :--- | :--- | :--- |
| **Piso de Qualidade** | [reference/craft-floor.md](reference/craft-floor.md) | Regras mecânicas inegociáveis de acabamento e contraste |
| **Tipografia** | [reference/typeset.md](reference/typeset.md) | Medidas, entrelinha, tracking, fontes e hierarquia |
| **Layout & Espaçamento** | [reference/layout.md](reference/layout.md) | Composição espacial, grelhas, ritmo e densidade |
| **Animação & Movimento** | [reference/animate.md](reference/animate.md) | Transições intencionais, easing e respeito ao usuário |
| **Cores & Superfícies** | [reference/colorize.md](reference/colorize.md) | Paletas funcionais, superfícies e contraste sem monotonia |
| **Crítica & Auditoria** | [reference/critique.md](reference/critique.md) | Avaliação holística de UX, ruído visual e usabilidade |
| **Declutter / Limpeza** | [reference/distill.md](reference/distill.md) | Remoção de decorações inúteis e foco na tarefa |
| **Polimento Visual** | [reference/polish.md](reference/polish.md) | Micro-interações, alinhamento fino e estados de transição |
| **Performance de UI** | [reference/optimize.md](reference/optimize.md) | Prevenção de CLS, reflows e custo de renderização |
| **Resiliência e Casos de Borda**| [reference/harden.md](reference/harden.md) | Strings longas, overflow, falhas de rede e estados vazios |
| **Design de Nova Superfície** | [reference/new-work.md](reference/new-work.md) | Estabelecimento de identidade e linguagem visual original |
