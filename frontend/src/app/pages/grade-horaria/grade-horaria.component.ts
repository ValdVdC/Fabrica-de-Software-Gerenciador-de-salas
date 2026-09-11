import { Component, OnInit, inject, input, computed, DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { HorarioService, HorarioMeu, DIAS_SEMANA_LABELS } from '../../services/horario.service';

@Component({
  selector: 'app-grade-horaria',
  standalone: true,
  // prettier-ignore
  template: `
    <div class="grade-container">
      <header class="grade-header">
        <div><h2>{{ titulo() }}</h2><p class="desc">{{ subtitulo() }}</p></div>
        <div class="grade-actions"><button type="button" class="btn-secondary" (click)="recarregar()" [disabled]="horarioService.isLoading()">{{ horarioService.isLoading() ? 'Carregando...' : 'Recarregar Grade' }}</button></div>
      </header>
      <div class="metrics-bar">
        <div class="metric-item"><span class="metric-label">Total de Aulas</span><span class="metric-value tabular-nums">{{ horarioService.totalAulas() }}</span></div>
        <div class="metric-item"><span class="metric-label">Disciplinas</span><span class="metric-value tabular-nums">{{ horarioService.disciplinasDistintas().length }}</span></div>
        <div class="metric-item"><span class="metric-label">Perfil Ativo</span><span class="metric-value">{{ perfil() === 'professor' ? 'Docente' : 'Discente' }}</span></div>
      </div>
      @if (horarioService.errorMessage()) { <div class="alert alert-error"><span>{{ horarioService.errorMessage() }}</span><button type="button" class="btn-retry" (click)="recarregar()" [disabled]="horarioService.isLoading()">{{ horarioService.isLoading() ? 'Carregando...' : 'Tentar novamente' }}</button></div> }
      @if (horarioService.isLoading() && horarioService.totalAulas() === 0) { <div class="loading-box"><p>Carregando grade horaria...</p></div> }
      @else if (!horarioService.errorMessage() && horarioService.totalAulas() === 0) { <div class="empty-box"><p>Nenhum horario alocado para esta grade semanal.</p></div> }
      @else if (horarioService.totalAulas() > 0) {
        <div class="timetable-grid">
          @for (col of diasSemanaData(); track col.dia) {
            <div class="dia-coluna">
              <div class="dia-header"><h3>{{ col.label }}</h3></div>
              <div class="dia-corpo">
                @if (col.aulas.length === 0) { <div class="sem-aula">Sem aulas</div> }
                @else {
                  @for (aula of col.aulas; track aula.id) {
                    <div class="aula-card">
                      <div class="aula-horario tabular-nums">{{ formatarIntervalo(aula.hora_inicio, aula.hora_fim) }}</div>
                      <div class="aula-disciplina"><strong>{{ aula.disciplina_codigo }}</strong><span class="disciplina-nome" [title]="aula.disciplina_nome">{{ aula.disciplina_nome }}</span></div>
                      <div class="aula-local"><span class="badge-sala">{{ aula.sala_bloco }} - {{ aula.sala_numero }}</span><span class="badge-tipo">{{ aula.sala_tipo }}</span></div>
                      <div class="aula-detalhe">
                        @if (perfil() === 'aluno') { <span class="prof-label">Docente: {{ aula.professor_nome || 'A definir' }}</span> }
                        @else if (perfil() === 'professor') { <span class="turma-label">Periodo: {{ aula.periodo_letivo }} ({{ aula.turno }})</span> }
                      </div>
                    </div>
                  }
                }
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
  // prettier-ignore
  styles: [`
    .grade-container { display: flex; flex-direction: column; gap: 1rem; }
    .grade-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.75rem; }
    .grade-actions .btn-secondary { background: #f1f5f9; border: 1px solid #cbd5e1; padding: 0.4rem 0.8rem; border-radius: 4px; font-size: 0.8125rem; cursor: pointer; }
    .grade-actions .btn-secondary:hover:not(:disabled) { background: #e2e8f0; }
    .btn-secondary:disabled, .btn-retry:disabled { opacity: 0.6; cursor: not-allowed; }
    .metrics-bar { display: flex; gap: 1.5rem; background: #fff; padding: 0.75rem 1rem; border-radius: 6px; border: 1px solid #e2e8f0; }
    .metric-item { display: flex; flex-direction: column; } .metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.125rem; font-weight: 700; color: #0f172a; } .tabular-nums { font-variant-numeric: tabular-nums; }
    .alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 0.75rem 1rem; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }
    .btn-retry { background: #991b1b; color: #fff; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; cursor: pointer; }
    .loading-box, .empty-box { background: #fff; border: 1px dashed #cbd5e1; padding: 2.5rem; text-align: center; border-radius: 6px; color: #64748b; font-size: 0.875rem; }
    .timetable-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.75rem; align-items: start; }
    @media (max-width: 640px) { .timetable-grid { grid-template-columns: 1fr; } }
    .dia-coluna { background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; display: flex; flex-direction: column; overflow: hidden; }
    .dia-header { background: #0f172a; color: #fff; padding: 0.5rem; text-align: center; }
    .dia-header h3 { font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin: 0; }
    .dia-corpo { padding: 0.5rem; display: flex; flex-direction: column; gap: 0.5rem; min-height: 120px; }
    .sem-aula { color: #94a3b8; font-size: 0.75rem; text-align: center; margin: auto 0; font-style: italic; }
    .aula-card { background: #f8fafc; border: 1px solid #cbd5e1; border-left: 3px solid #0284c7; padding: 0.5rem; border-radius: 4px; display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.75rem; }
    .aula-horario { font-weight: 700; color: #0284c7; } .aula-disciplina { display: flex; flex-direction: column; }
    .disciplina-nome { color: #334155; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .aula-local { display: flex; gap: 0.25rem; align-items: center; margin-top: 0.125rem; }
    .badge-sala { background: #e0f2fe; color: #0369a1; padding: 0.125rem 0.375rem; border-radius: 3px; font-weight: 600; font-size: 0.6875rem; }
    .badge-tipo { background: #f1f5f9; color: #475569; padding: 0.125rem 0.25rem; border-radius: 3px; font-size: 0.625rem; text-transform: uppercase; }
    .aula-detalhe { font-size: 0.6875rem; color: #64748b; margin-top: 0.125rem; }
  `],
})
export class GradeHorariaComponent implements OnInit {
  readonly horarioService = inject(HorarioService);
  private readonly destroyRef = inject(DestroyRef);

  readonly titulo = input<string>('Grade Semanal');
  readonly subtitulo = input<string>('Horarios e salas alocadas');
  readonly perfil = input<'professor' | 'aluno'>('aluno');

  readonly labelsDias = DIAS_SEMANA_LABELS;

  readonly diasSemanaData = computed(() => {
    const temDomingo = this.horarioService.horarios().some((h) => h.dia_semana === 6);
    const dias = temDomingo ? [0, 1, 2, 3, 4, 5, 6] : [0, 1, 2, 3, 4, 5];
    return dias.map((dia) => ({
      dia,
      label: this.labelsDias[dia] || `Dia ${dia}`,
      aulas: this.horarioService.obterHorariosDoDia(dia),
    }));
  });

  ngOnInit(): void {
    this.horarioService
      .carregarMeusHorarios()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ error: () => {} });
  }

  recarregar(): void {
    this.horarioService
      .carregarMeusHorarios()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ error: () => {} });
  }

  formatarIntervalo(inicio?: string | null, fim?: string | null): string {
    const i = this.formatarHora(inicio);
    const f = this.formatarHora(fim);
    if (i && f) return `${i} - ${f}`;
    if (i) return `A partir de ${i}`;
    if (f) return `Ate ${f}`;
    return 'Horario a definir';
  }

  formatarHora(h?: string | null): string {
    if (!h) return '';
    const trimmed = h.trim();
    if (!trimmed) return '';
    const partes = trimmed.split(':');
    if (partes.length >= 2) {
      return `${partes[0].padStart(2, '0')}:${partes[1].padStart(2, '0')}`;
    }
    return trimmed.padStart(5, '0');
  }

  formatarHorario(h?: string | null): string {
    return this.formatarHora(h);
  }
}
