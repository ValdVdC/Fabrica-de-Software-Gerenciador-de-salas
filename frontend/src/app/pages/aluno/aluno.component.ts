import { Component, OnInit, inject, signal, DestroyRef } from '@angular/core';
import { DatePipe } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { GradeHorariaComponent } from '../grade-horaria/grade-horaria.component';
import { SecretariaService, Matricula } from '../../services/secretaria.service';
import { HorarioService } from '../../services/horario.service';

@Component({
  selector: 'app-aluno',
  standalone: true,
  imports: [GradeHorariaComponent, DatePipe],
  // prettier-ignore
  template: `
    <div class="aluno-wrapper">
      <app-grade-horaria titulo="Painel do Discente" subtitulo="Grade horaria semanal individual e localizacao de salas" perfil="aluno" />
      <section class="matriculas-section" aria-label="Minhas Matriculas">
        <header class="section-header"><h3>Minhas Matriculas</h3><p>Acompanhamento de vinculos discentes e cancelamento de matricula ativa.</p></header>
        @if (secretariaService.errorMessage(); as erro) { <div class="alert alert-error" role="alert">{{ erro }}</div> }
        @if (mensagemSucesso(); as msg) { <div class="alert alert-success" role="status">{{ msg }}</div> }
        <div class="table-card"><table class="data-table">
          <thead><tr><th>ID</th><th>Turma</th><th>Status</th><th>Data</th><th>Acoes</th></tr></thead>
          <tbody>
            @for (m of secretariaService.matriculas(); track m.id) {
              <tr>
                <td class="tabular-nums">#{{ m.id }}</td><td class="tabular-nums font-bold">Turma #{{ m.turma_id }}</td>
                <td><span class="badge" [class.badge-success]="m.status === 'ativa'" [class.badge-danger]="m.status === 'cancelada'">{{ m.status }}</span></td>
                <td class="tabular-nums">{{ m.data_matricula | date:'shortDate' }}</td>
                <td>@if (m.status === 'ativa') { <button type="button" [attr.data-testid]="'btn-aluno-cancelar-matricula-' + m.id" class="btn-danger-sm" [disabled]="secretariaService.isLoading()" (click)="cancelarMatricula(m)"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg> Cancelar Matricula</button> } @else { <span>-</span> }</td>
              </tr>
            } @empty { <tr><td colspan="5" class="empty-msg">Nenhuma matricula vinculada ao discente.</td></tr> }
          </tbody>
        </table></div>
      </section>
    </div>
  `,
  // prettier-ignore
  styles: [`
    .aluno-wrapper { display: flex; flex-direction: column; gap: 1.5rem; } .matriculas-section { display: flex; flex-direction: column; gap: 0.75rem; }
    .section-header h3 { margin: 0; font-size: 1.125rem; font-weight: 700; color: #0f172a; } .section-header p { margin: 0.15rem 0 0; font-size: 0.8125rem; color: #64748b; }
    .alert { padding: 0.75rem; border-radius: 4px; font-size: 0.8125rem; } .alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; } .alert-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
    .table-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 1rem; } .data-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; text-align: left; }
    .data-table th, .data-table td { padding: 0.75rem; border-bottom: 1px solid #f1f5f9; color: #334155; } .data-table th { background: #f8fafc; border-bottom-color: #e2e8f0; color: #475569; font-weight: 600; }
    .font-bold { font-weight: 600; color: #0f172a; } .tabular-nums { font-variant-numeric: tabular-nums; }
    .badge { display: inline-block; padding: 0.125rem 0.375rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; background: #f1f5f9; color: #334155; text-transform: uppercase; } .badge-success { background: #dcfce7; color: #15803d; } .badge-danger { background: #fee2e2; color: #b91c1c; }
    .btn-danger-sm { display: inline-flex; align-items: center; gap: 0.25rem; background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; cursor: pointer; } .btn-danger-sm:disabled { opacity: 0.5; cursor: not-allowed; }
    .empty-msg { text-align: center; color: #94a3b8; padding: 1.5rem 1rem; }
  `],
})
export class AlunoComponent implements OnInit {
  readonly secretariaService = inject(SecretariaService);
  private readonly horarioService = inject(HorarioService);
  private readonly destroyRef = inject(DestroyRef);
  readonly mensagemSucesso = signal<string | null>(null);

  // prettier-ignore
  ngOnInit(): void {
    this.secretariaService.listarMatriculas().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ error: () => {} });
  }

  // prettier-ignore
  cancelarMatricula(m: Matricula): void {
    if (m.status !== 'ativa' || this.secretariaService.isLoading()) return;
    this.secretariaService.limparErro(); this.mensagemSucesso.set(null);
    this.secretariaService.cancelarMatricula(m.id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.mensagemSucesso.set(`Matricula #${m.id} cancelada com sucesso.`);
        this.horarioService.carregarMeusHorarios().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ error: () => {} });
      },
      error: () => {},
    });
  }
}
