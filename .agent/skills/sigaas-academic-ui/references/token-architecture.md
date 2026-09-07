# Arquitetura de Tokens e Tema Tailwind CSS - SIGAAS

Este documento estabelece o sistema de tokens em 3 camadas do SIGAAS, alinhando Angular 18+, Tailwind CSS e acessibilidade institucional.

## 1. Estrutura em 3 Camadas

```text
Primitivos (Valores brutos de cor, espaco e fonte)
       ↓
Semânticos (Função no sistema: surface, text-primary, border-subtle, status-conflict)
       ↓
Componentes (Tokens específicos: timetable-cell-bg, sidebar-nav-item-active)
```

## 2. Tokens Primitivos (CSS Variables em `src/styles.css`)

```css
:root {
  /* Neutros Institucionais (Slate) */
  --slate-50: #f8fafc;
  --slate-100: #f1f5f9;
  --slate-200: #e2e8f0;
  --slate-300: #cbd5e1;
  --slate-400: #94a3b8;
  --slate-500: #64748b;
  --slate-600: #475569;
  --slate-700: #334155;
  --slate-800: #1e293b;
  --slate-900: #0f172a;
  --slate-950: #020617;

  /* Identidade Acadêmica (Navy) */
  --navy-500: #1e3a8a;
  --navy-600: #172554;
  --navy-700: #0f172a;

  /* Estados Funcionais */
  --emerald-500: #10b981;
  --emerald-700: #047857;
  --amber-500: #f59e0b;
  --amber-700: #b45309;
  --rose-500: #f43f5e;
  --rose-700: #be123c;
}
```

## 3. Tokens Semânticos

| Token Semântico | Valor Base | Uso no SIGAAS |
| :--- | :--- | :--- |
| `--bg-app` | `var(--slate-50)` | Fundo da aplicação |
| `--surface-card` | `#ffffff` | Painéis e superfícies operacionais |
| `--surface-sidebar` | `var(--slate-900)` | Shell de navegação lateral fixa |
| `--text-primary` | `var(--slate-900)` | Títulos e texto com alto contraste (12.6:1) |
| `--text-secondary` | `var(--slate-600)` | Metadados, subtítulos e labels auxiliares (4.8:1) |
| `--border-subtle` | `var(--slate-200)` | Divisores de grade e contornos limpos |
| `--status-free-bg` | `var(--emerald-50)` | Célula de sala livre |
| `--status-free-text`| `var(--emerald-700)` | Texto indicador de disponibilidade |
| `--status-conflict-bg` | `var(--rose-50)` | Alerta de sobreposição de salas |
| `--status-conflict-text` | `var(--rose-700)` | Texto de conflito com ícone AlertTriangle |
| `--status-pending-bg` | `var(--amber-50)` | Sugestão de remanejamento da IA |
| `--status-pending-text` | `var(--amber-700)`| Texto de sugestão com probabilidade |

## 4. Integração no `tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      colors: {
        academic: {
          navy: {
            500: "var(--navy-500)",
            600: "var(--navy-600)",
            700: "var(--navy-700)",
          },
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
```
