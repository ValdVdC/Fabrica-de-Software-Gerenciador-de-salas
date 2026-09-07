# Padrões de Layout da Grade de Horários e Matriz de Salas - SIGAAS

Este documento detalha as diretrizes de UX e implementação para a tela central do sistema: a Grade Matricial de Alocação de Salas e Horários.

## 1. Estrutura Dimensional

A grade acadêmica opera em duas dimensões principais:
1. **Eixo Temporal (Linhas ou Colunas)**:
   - Manhã: M1 (07:00 - 07:50), M2 (07:50 - 08:40), M3 (08:55 - 09:45), M4 (09:45 - 10:35), M5 (10:50 - 11:40)
   - Tarde: T1 (13:00 - 13:50), T2 (13:50 - 14:40), T3 (14:55 - 15:45), T4 (15:45 - 16:35), T5 (16:50 - 17:40)
   - Noite: N1 (18:30 - 19:20), N2 (19:20 - 20:10), N3 (20:20 - 21:10), N4 (21:10 - 22:00)
2. **Eixo Espacial (Salas / Laboratórios)**:
   - Identificação do Prédio, Bloco, Número da Sala e Tipo (Sala de Aula, Laboratório de Informática, Auditório).

## 2. Cabeçalhos Fixos (Sticky Headers)

```html
<div class="relative max-h-[calc(100vh-12rem)] overflow-auto border border-slate-200 rounded-lg shadow-sm">
  <table class="w-full text-left border-collapse">
    <thead class="sticky top-0 z-20 bg-slate-100 border-b border-slate-200">
      <!-- Horarios -->
    </thead>
    <tbody>
      <!-- Linhas com primeira coluna fixa: sticky left-0 z-10 bg-white -->
    </tbody>
  </table>
</div>
```

## 3. Estados de Célula e Anatomia Visual

Cada célula deve exibir com máxima clareza:
- **Disciplina**: Código formal + nome abreviado (ex.: `SIN101 - Algoritmos`).
- **Professor**: Nome do docente com badge de departamento.
- **Capacidade**: `Ocupação / Capacidade Máxima` com números tabulares (`tabular-nums`).
- **Ações de Célula**:
  - Clique simples: Abre drawer lateral de detalhes de alocação (sem modal intrusivo).
  - Hover: Realce da linha e coluna correspondentes para facilitar rastreamento visual.

## 4. Responsividade e Telas Menores

- Em desktops (>= 1280px): Visualização matricial completa (salas x horários).
- Em tablets e mobile (< 1024px): Alternância automática para visualização em Lista Cronológica por Sala ou por Dia, evitando compressão ilegível de colunas.
