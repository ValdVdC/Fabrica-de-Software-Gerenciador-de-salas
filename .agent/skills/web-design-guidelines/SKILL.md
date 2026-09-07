---
name: web-design-guidelines
description: >-
  Review UI code for Web Interface Guidelines compliance, accessibility (WCAG AA), focus states,
  forms, animations, typography punctuation, and performance. Use when auditing UI code or verifying
  front-end implementation quality.
---

# Web Interface Guidelines

Check frontend code against web standards, accessibility requirements, and interface guidelines.

## Rules Checklist

### Accessibility & Semantic Structure
- Icon-only buttons must have `aria-label`.
- Form controls must have `<label>` (with `for`/`id`) or `aria-label`.
- Interactive elements must handle keyboard events (`Enter` and `Space` for buttons).
- Use `<button>` for actions, `<a>` for navigation. Never `<div (click)>` or `<span (click)>`.
- Images must have `alt` attribute (or `alt=""` if strictly decorative).
- Decorative icons must have `aria-hidden="true"`.
- Async status updates (toasts, live validation) require `aria-live="polite"`.
- Use semantic HTML (`<main>`, `<nav>`, `<header>`, `<table>`) before custom ARIA roles.
- Hierarchical headings (`<h1>` to `<h6>`) without skipping levels.

### Focus States
- Interactive elements must provide visible focus: `focus-visible:ring-2` or equivalent.
- Never use `outline: none` without providing an explicit focus-visible replacement.
- Use `:focus-visible` instead of `:focus` to prevent focus rings on mouse click.
- Group focus with `:focus-within` for compound form controls.
- Sticky headers/toolbars must not obscure focused elements.

### Forms & Input Handling
- Inputs must have `autocomplete` and meaningful `name` attributes.
- Use appropriate input types (`email`, `tel`, `url`, `number`) and `inputmode`.
- Never block paste (`onPaste` with `preventDefault` is prohibited).
- Labels must be clickable and expand the hit target.
- Disable spellcheck on codes, emails, and identifiers (`spellcheck="false"`).
- Checkbox and radio inputs share a single hit target with their label.
- Submit buttons remain enabled until request starts; show spinner and disable during inflight request.
- Display validation errors inline next to the respective field; focus first errored field on submit.

### Animation & Motion
- Always honor `prefers-reduced-motion` with reduced variants or disabled transitions.
- Animate `transform` and `opacity` only (GPU compositor-friendly).
- Avoid `transition: all`; explicitly declare transitioned properties.
- Set appropriate `transform-origin` on scaling elements.

### Typography Nuances
- Ellipsis: use `…` instead of three periods `...`.
- Punctuation: use curly quotes where appropriate.
- Tabular figures: use `font-variant-numeric: tabular-nums` for numbers, clocks, and data columns.
- Heading balance: use `text-wrap: balance` on section headings to prevent single trailing words (widows).

### Layout & Performance
- Prevent Cumulative Layout Shift (CLS): provide explicit aspect ratios or dimensions on images/skeletons.
- Flexible text containers must handle overflow with `truncate`, `line-clamp-*`, or `break-words`.
- Flex children containing text need `min-w-0` to allow truncation.
- Empty states must be designed gracefully; never render broken or empty shells when collections are empty.
- Virtualize large lists (> 50 items) to prevent DOM bloat.

### Dark Mode & Theming
- Set `color-scheme: dark` or `light` on `<html>` to ensure native controls and scrollbars match.
- High contrast: ensure hover, active, and selected states exceed minimum WCAG AA contrast standards.
