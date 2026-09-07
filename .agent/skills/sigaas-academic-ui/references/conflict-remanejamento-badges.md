# Badges de Conflito e Sugestões da IA - SIGAAS

Este documento padroniza a representação visual de alertas críticos no sistema, garantindo conformidade com WCAG 2.1 AA e estrita proibição de emojis.

## 1. Regra de Ouro de Acessibilidade: Nunca Usar Cor Isoladamente

Usuários com daltonismo (protanopia, deuteranopia) não conseguem distinguir vermelho de verde ou âmbar em pequenas áreas. Por isso, **todo indicador de estado deve possuir**:
1. Cor de fundo e texto contrastante (mínimo 4.5:1).
2. Ícone vetorial semântico (Lucide Icons).
3. Texto explicativo legível ou tag ARIA equivalente.

## 2. Padrões de Badges

### Conflito de Alocação (Sobreposição de Salas / Horários)
- **Cores**: `bg-rose-50 text-rose-800 border-rose-200`
- **Ícone**: `AlertTriangle` (`lucide-angular`, stroke 2px, 16px)
- **Texto**: `Conflito Detectado`
- **Comportamento**: Destaque prioritário no topo do painel da coordenação com botão direto de resolução.

### Sugestão Pendente da IA (Absenteísmo Previsto)
- **Cores**: `bg-amber-50 text-amber-800 border-amber-200`
- **Ícone**: `Sparkles` ou `Clock3` (`lucide-angular`, 16px)
- **Texto**: `Remanejamento Sugerido (Probabilidade: X%)`
- **Ações**: Botões de `Aprovar Troca` e `Recusar`, consumindo `PATCH /sugestoes/{id}`.

### Alocação Confirmada
- **Cores**: `bg-emerald-50 text-emerald-800 border-emerald-200`
- **Ícone**: `CheckCircle2` (`lucide-angular`, 16px)
- **Texto**: `Alocado`

## 3. Exemplo de Componente Angular Standalone

```typescript
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, AlertTriangle, CheckCircle2, Clock3 } from 'lucide-angular';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <span [ngClass]="badgeClass" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border">
      <i-lucide [name]="iconName" class="w-4 h-4"></i-lucide>
      <span>{{ label }}</span>
    </span>
  `
})
export class StatusBadgeComponent {
  @Input() status!: 'alocado' | 'conflito' | 'sugestao_pendente';
  // mapeamento de classes e icones
}
```
