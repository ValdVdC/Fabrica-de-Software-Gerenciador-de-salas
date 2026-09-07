---
name: frontend-design
description: >-
  Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one.
  Helps with aesthetic direction, typography, palette curation, and avoiding templated AI design patterns.
---

# Frontend Design

Approach this as the design lead at a design studio known for giving every client a distinct visual identity that is not mistaken for anyone else. Deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, taking aesthetic risk if justified.

## Ground Designs in the Subject Matter

If the brief does not identify what the product or subject matter is, identify it yourself before designing, and confirm with the client. The subject's industry, audience, materials, and vernacular are where distinctive visual choices come from. A dashboard for academic scheduling will be aesthetically different from a consumer streaming app or a financial terminal. Build with the brief's real content and subject matter throughout.

## Design Principles

- **Hero / Header**: Open with the most characteristic thing in the subject's world, in the form that is most appropriate. A big number with a small label and gradient accent is the generic default; only use it if that is truly the best option.
- **Typography**: Typography carries the personality of the page. You do not need a different typeface for display or headline text and body content: use one family or two, and if two, make them clearly distinct. Choose typefaces deliberately, not default system fallbacks. Set a clear type scale following The Elements of Typographic Style with intentional weights, widths, and spacing.
- **Line Length**: Default to line lengths of less than 80 characters. Serif typefaces can have slightly longer line lengths; give serif body text slightly more line-height than a sans-serif.
- **Avoid Default Typographic Tells**:
  - Accenting just a single word or phrase in a headline (e.g. putting one word in italic/bold or a different color).
  - Using all-caps for labels.
  - Adding unnecessary typographic labels above content (eyebrows).
- **Visual Structure Is Information**: Structural devices like outlines, borders, numbering, dividers, and labels encode useful information about the content rather than decorate it. Numbered markers (01 / 02 / 03) are only appropriate if the content actually is a sequence (like a stepped process or a timeline).
- **Restrained Motion**: Use non-user-triggered motion sparingly and deliberately, only to draw attention. A single orchestrated moment lands better than scattered effects; fade-and-slide-up entrances on each section and hover transitions on every card are generic defaults and read as AI-generated. Motion that answers a person's action (opening, expanding, confirming) is welcome when it shows what changed.

## Process: Plan, Review Against the Brief, Build, Critique

Common AI-generated design traits to actively avoid:
1. Warm cream background (near #F4F1EA) with high-contrast serif display and terracotta/warm-clay accent (#D97757).
2. Near-black background with a single bright acid-green or vermilion accent.
3. Broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns.
4. The SaaS-card kit: content chopped into identical rounded cards, one border-radius on everything regardless of hierarchy, the same soft grey shadow (rgba(0,0,0,.1)) under each, and gradient washes as decoration.
5. Template chrome: tracked-out ALL-CAPS eyebrow label above every heading; meta strings joined with middle dots ('A · B · C'); labels built as 'WORD - fragment' with a spaced em dash; tinted near-black (#0B0B0B, #111) standing in for black; monospace face for small data labels; an arrow appended to link and button text.

Work in two passes:
1. Brainstorm a short design plan: create a compact token system with color (4-6 named hex values), type, layout concept (ASCII wireframe or one-sentence prose descriptions), and principles.
2. Review that plan against the brief before building: if any part reads like the generic default produced for any similar page, revise it before writing code.

## Restraint and Self-Critique

Spend boldness in one place. Let one element be the memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Build to a quality floor without announcing it: responsive down to mobile, visible keyboard focus, reduced motion respected, visually accessible, harmonious color palettes.

## UX Copywriting

- Words appear in a design for one reason: to make it easier to understand and use.
- Write from the end user's perspective. Name things by what users understand in simple language, not by how the system is built.
- Use active voice as default: "Save changes" instead of "Submit".
- Treat failure and emptiness as moments for direction, not mood. Errors explain what went wrong and how to fix it without apologizing. An empty screen is an invitation to act.
