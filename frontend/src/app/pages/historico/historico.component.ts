import { Component, OnInit, inject, signal, computed, DestroyRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subscription } from 'rxjs';
import { LogService } from '../../services/log.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-historico',
  standalone: true,
  imports: [FormsModule, DatePipe],
  // prettier-ignore
  template: `
    <div class="admin-container">
      <header class="admin-header">
        <div class="admin-header-title-row">
          <div>
            <h2>Historico de Operacoes e Auditoria</h2>
            <p>Consulta somente leitura da trilha de auditoria (LogAlocacao) com filtros por tipo de evento, responsavel e periodo.</p>
          </div>
          <div class="toolbar-actions">
            <button type="button" data-testid="btn-exportar-logs-csv" class="btn-secondary" (click)="exportarCsv()" [disabled]="logService.isExporting() || logService.isLoading()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              {{ logService.isExporting() ? 'Exportando CSV...' : 'Exportar CSV' }}
            </button>
          </div>
        </div>
      </header>

      @if (erroValidacao()) { <div class="alert alert-error">{{ erroValidacao() }}</div> }
      @if (logService.errorMessage()) { <div class="alert alert-error">{{ logService.errorMessage() }}</div> }

      <div class="panel-card">
        <div class="form-row" style="align-items: flex-end;">
          @if (isAdmin()) {
            <div class="form-group"><label class="input-label" for="fCampusLog">Campus ID</label><input id="fCampusLog" type="number" min="1" [(ngModel)]="filtroCampusId" placeholder="Todos" class="form-input tabular-nums" style="max-width: 105px;" /></div>
          }
          <div class="form-group">
            <label class="input-label" for="fTipoEvento">Tipo de Evento</label>
            <select id="fTipoEvento" [(ngModel)]="filtroTipoEvento" class="form-input form-select" style="max-width: 165px;">
              <option value="">Todos os eventos</option><option value="criacao">Criacao</option><option value="alteracao">Alteracao</option><option value="remanejamento">Remanejamento</option><option value="cancelamento">Cancelamento</option>
            </select>
          </div>
          <div class="form-group"><label class="input-label" for="fUsuarioLog">Usuario ID</label><input id="fUsuarioLog" type="number" min="1" [(ngModel)]="filtroUsuarioId" placeholder="Ex: 1" class="form-input tabular-nums" style="max-width: 115px;" /></div>
          <div class="form-group"><label class="input-label" for="fHorarioLog">Horario ID</label><input id="fHorarioLog" type="number" min="1" [(ngModel)]="filtroHorarioId" placeholder="Ex: 10" class="form-input tabular-nums" style="max-width: 115px;" /></div>
          <div class="form-group"><label class="input-label" for="fDataIniLog">Data Inicial</label><input id="fDataIniLog" type="date" [(ngModel)]="filtroDataInicio" class="form-input tabular-nums" /></div>
          <div class="form-group"><label class="input-label" for="fDataFimLog">Data Final</label><input id="fDataFimLog" type="date" [(ngModel)]="filtroDataFim" class="form-input tabular-nums" /></div>
          <button type="button" class="btn-primary" (click)="aplicarFiltros()" [disabled]="logService.isLoading()">Filtrar</button>
          <button type="button" class="btn-secondary" (click)="limparFiltros()" [disabled]="logService.isLoading()">Limpar</button>
        </div>
      </div>

      <div class="table-card">
        <table class="data-table">
          <thead><tr><th>ID</th><th>Data / Hora</th><th>Tipo de Evento</th><th>Responsavel</th><th>Horario</th><th>Detalhes da Operacao</th></tr></thead>
          <tbody>
            @for (item of logService.logs(); track item.id) {
              <tr>
                <td class="tabular-nums font-bold">#{{ item.id }}</td><td class="tabular-nums">{{ item.timestamp | date:'short' }}</td>
                <td><span class="badge" [class.badge-success]="item.tipo_evento === 'criacao'" [class.badge-pending]="item.tipo_evento === 'remanejamento' || item.tipo_evento === 'alteracao'" [class.badge-danger]="item.tipo_evento === 'cancelamento'">{{ item.tipo_evento }}</span></td>
                <td class="tabular-nums">Usuario #{{ item.usuario_responsavel }}</td><td class="tabular-nums">{{ item.horario_id ? ('#' + item.horario_id) : '-' }}</td><td>{{ item.detalhes || '-' }}</td>
              </tr>
            } @empty {
              <tr><td colspan="6" class="empty-msg">{{ logService.isLoading() ? 'Carregando trilha de auditoria...' : 'Nenhum evento registrado para os filtros informados.' }}</td></tr>
            }
          </tbody>
        </table>
      </div>

      <div class="pagination-bar">
        <span class="pagination-info tabular-nums">Exibindo a partir do registro {{ skip() + 1 }} (limite {{ limit }})</span>
        <div class="toolbar-actions">
          <button type="button" class="btn-secondary" (click)="paginaAnterior()" [disabled]="skip() === 0 || logService.isLoading()">Anterior</button>
          <button type="button" class="btn-secondary" (click)="proximaPagina()" [disabled]="!temProximaPagina() || logService.isLoading()">Proxima</button>
        </div>
      </div>
    </div>
  `,
})
export class HistoricoComponent implements OnInit {
  readonly logService = inject(LogService);
  private readonly authService = inject(AuthService);
  private readonly destroyRef = inject(DestroyRef);
  private reqSub?: Subscription;

  readonly erroValidacao = signal<string | null>(null);
  readonly skip = signal<number>(0);
  readonly limit = 50;

  filtroCampusId: number | null = null;
  filtroTipoEvento = '';
  filtroUsuarioId: number | null = null;
  filtroHorarioId: number | null = null;
  filtroDataInicio = '';
  filtroDataFim = '';

  readonly isAdmin = computed(() => this.authService.currentRole() === 'admin');
  readonly temProximaPagina = computed(() => this.logService.logs().length >= this.limit);

  // prettier-ignore
  ngOnInit(): void { this.carregarDados(); }
  // prettier-ignore
  aplicarFiltros(): void { if (!this.validarPeriodo()) return; this.skip.set(0); this.carregarDados(); }
  // prettier-ignore
  limparFiltros(): void {
    this.filtroCampusId = null; this.filtroTipoEvento = ''; this.filtroUsuarioId = null; this.filtroHorarioId = null; this.filtroDataInicio = ''; this.filtroDataFim = '';
    this.erroValidacao.set(null); this.skip.set(0); this.carregarDados();
  }
  // prettier-ignore
  paginaAnterior(): void { if (this.skip() === 0) return; this.skip.update((s) => Math.max(0, s - this.limit)); this.carregarDados(); }
  // prettier-ignore
  proximaPagina(): void { this.skip.update((s) => s + this.limit); this.carregarDados(); }
  // prettier-ignore
  exportarCsv(): void {
    if (!this.validarPeriodo()) return;
    this.logService.exportarLogsCsv(this.montarFiltro(false)).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ error: () => {} });
  }
  // prettier-ignore
  private validarPeriodo(): boolean {
    if (this.filtroDataInicio && this.filtroDataFim && this.filtroDataFim < this.filtroDataInicio) {
      this.erroValidacao.set('A data final deve ser maior ou igual a data inicial.');
      return false;
    }
    this.erroValidacao.set(null); return true;
  }
  // prettier-ignore
  private montarFiltro(incluirPaginacao: boolean) {
    const campus_id = this.isAdmin() && this.filtroCampusId && this.filtroCampusId > 0 ? Number(this.filtroCampusId) : undefined;
    const usuario_id = this.filtroUsuarioId && this.filtroUsuarioId > 0 ? Number(this.filtroUsuarioId) : undefined;
    const horario_id = this.filtroHorarioId && this.filtroHorarioId > 0 ? Number(this.filtroHorarioId) : undefined;
    return { campus_id, tipo_evento: this.filtroTipoEvento, usuario_id, horario_id, data_inicio: this.filtroDataInicio, data_fim: this.filtroDataFim, ...(incluirPaginacao ? { skip: this.skip(), limit: this.limit } : {}) };
  }
  // prettier-ignore
  private carregarDados(): void {
    this.reqSub?.unsubscribe();
    this.reqSub = this.logService.listarLogs(this.montarFiltro(true)).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ error: () => {} });
  }
}
