import { Component, OnInit, inject, signal, computed, DestroyRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, Subscription } from 'rxjs';
import { RelatorioService } from '../../services/relatorio.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-relatorios',
  standalone: true,
  imports: [FormsModule, DatePipe],
  // prettier-ignore
  template: `
    <div class="admin-container">
      <header class="admin-header">
        <div class="admin-header-title-row">
          <div>
            <h2>Relatorios Consolidados</h2>
            <p>Acompanhamento de ocupacao semanal de espacos fisicos, historico de remanejamentos e exportacao tabular.</p>
          </div>
          <div class="toolbar-actions">
            <button type="button" data-testid="btn-exportar-csv" class="btn-secondary" (click)="exportarCsv()" [disabled]="relatorioService.isExporting() || relatorioService.isLoading()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              {{ relatorioService.isExporting() ? 'Exportando CSV...' : 'Exportar CSV' }}
            </button>
          </div>
        </div>
      </header>

      <nav class="tabs-nav" aria-label="Abas de Relatorios">
        <button type="button" [class.active]="abaAtiva() === 'ocupacao'" (click)="selecionarAba('ocupacao')">Ocupacao de Salas</button>
        <button type="button" [class.active]="abaAtiva() === 'remanejamentos'" (click)="selecionarAba('remanejamentos')">Remanejamentos</button>
      </nav>

      @if (erroValidacao()) { <div class="alert alert-error">{{ erroValidacao() }}</div> }
      @if (relatorioService.errorMessage()) { <div class="alert alert-error">{{ relatorioService.errorMessage() }}</div> }

      @if (abaAtiva() === 'ocupacao') {
        <div class="panel-card">
          <div class="form-row" style="align-items: flex-end;">
            @if (isAdmin()) {
              <div class="form-group"><label class="input-label" for="fCampusOcup">Campus ID</label><input id="fCampusOcup" type="number" min="1" [(ngModel)]="filtroCampusId" placeholder="Todos" class="form-input tabular-nums" style="max-width: 110px;" /></div>
            }
            <div class="form-group"><label class="input-label" for="fBloco">Bloco</label><input id="fBloco" type="text" [(ngModel)]="filtroBloco" maxlength="50" placeholder="Ex: A" class="form-input" style="max-width: 140px;" /></div>
            <div class="form-group">
              <label class="input-label" for="fTipoSala">Tipo de Espaco</label>
              <select id="fTipoSala" [(ngModel)]="filtroTipoSala" class="form-input form-select" style="max-width: 170px;">
                <option value="">Todos os tipos</option><option value="regular">Regular</option><option value="laboratorio">Laboratorio</option><option value="auditorio">Auditorio</option><option value="reuniao">Reuniao</option>
              </select>
            </div>
            <button type="button" class="btn-primary" (click)="aplicarFiltros()" [disabled]="relatorioService.isLoading()">Filtrar</button>
            <button type="button" class="btn-secondary" (click)="limparFiltros()" [disabled]="relatorioService.isLoading()">Limpar</button>
          </div>
        </div>

        <div class="table-card">
          <table class="data-table">
            <thead><tr><th>Sala</th><th>Bloco</th><th>Tipo</th><th>Capacidade</th><th>Horarios Alocados</th><th>Taxa de Ocupacao Semanal</th></tr></thead>
            <tbody>
              @for (item of relatorioService.ocupacaoSalas(); track item.sala_id) {
                <tr>
                  <td class="font-bold">{{ item.sala }}</td><td>Bloco {{ item.bloco }}</td><td><span class="badge">{{ item.tipo }}</span></td>
                  <td class="tabular-nums">{{ item.capacidade }} postos</td><td class="tabular-nums font-semibold">{{ item.quantidade_horarios }}</td>
                  <td class="tabular-nums"><div class="ocupacao-bar-wrap"><div class="ocupacao-bar-track"><div class="ocupacao-bar-fill" [style.width.%]="item.taxa_ocupacao_semanal > 100 ? 100 : item.taxa_ocupacao_semanal"></div></div><span class="font-bold">{{ item.taxa_ocupacao_semanal }}%</span></div></td>
                </tr>
              } @empty {
                <tr><td colspan="6" class="empty-msg">{{ relatorioService.isLoading() ? 'Carregando relatorio de ocupacao...' : 'Nenhum registro encontrado para os filtros informados.' }}</td></tr>
              }
            </tbody>
          </table>
        </div>
      }

      @if (abaAtiva() === 'remanejamentos') {
        <div class="panel-card">
          <div class="form-row" style="align-items: flex-end;">
            @if (isAdmin()) {
              <div class="form-group"><label class="input-label" for="fCampusRem">Campus ID</label><input id="fCampusRem" type="number" min="1" [(ngModel)]="filtroCampusId" placeholder="Todos" class="form-input tabular-nums" style="max-width: 110px;" /></div>
            }
            <div class="form-group">
              <label class="input-label" for="fStatusRem">Status</label>
              <select id="fStatusRem" [(ngModel)]="filtroStatus" class="form-input form-select" style="max-width: 160px;">
                <option value="">Todos</option><option value="pendente">Pendente</option><option value="aprovado">Aprovado</option><option value="rejeitado">Rejeitado</option>
              </select>
            </div>
            <div class="form-group"><label class="input-label" for="fDataInicio">Data Inicial</label><input id="fDataInicio" type="date" [(ngModel)]="filtroDataInicio" class="form-input tabular-nums" /></div>
            <div class="form-group"><label class="input-label" for="fDataFim">Data Final</label><input id="fDataFim" type="date" [(ngModel)]="filtroDataFim" class="form-input tabular-nums" /></div>
            <button type="button" class="btn-primary" (click)="aplicarFiltros()" [disabled]="relatorioService.isLoading()">Filtrar</button>
            <button type="button" class="btn-secondary" (click)="limparFiltros()" [disabled]="relatorioService.isLoading()">Limpar</button>
          </div>
        </div>

        <div class="table-card">
          <table class="data-table">
            <thead><tr><th>ID</th><th>Sala Origem</th><th>Sala Destino</th><th>Status</th><th>Decisor</th><th>Motivo / Justificativa</th><th>Data</th></tr></thead>
            <tbody>
              @for (rem of relatorioService.remanejamentos(); track rem.id) {
                <tr>
                  <td class="tabular-nums font-bold">#{{ rem.id }}</td>
                  <td class="tabular-nums">{{ rem.sala_origem }} ({{ rem.sala_origem_capacidade }}p)</td>
                  <td class="tabular-nums font-semibold">{{ rem.sala_destino }} ({{ rem.sala_destino_capacidade }}p)</td>
                  <td><span class="badge" [class.badge-pending]="rem.status === 'pendente'" [class.badge-success]="rem.status === 'aprovado'" [class.badge-danger]="rem.status === 'rejeitado'">{{ rem.status }}</span></td>
                  <td>{{ rem.decisor || 'Pendente' }}</td><td>{{ rem.justificativa || rem.motivo }}</td>
                  <td class="tabular-nums">{{ rem.atualizado_em | date:'shortDate' }}</td>
                </tr>
              } @empty {
                <tr><td colspan="7" class="empty-msg">{{ relatorioService.isLoading() ? 'Carregando relatorio de remanejamentos...' : 'Nenhum remanejamento encontrado no periodo.' }}</td></tr>
              }
            </tbody>
          </table>
        </div>
      }

      <div class="pagination-bar">
        <span class="pagination-info tabular-nums">Exibindo a partir do registro {{ skip() + 1 }} (limite {{ limit }})</span>
        <div class="toolbar-actions">
          <button type="button" class="btn-secondary" (click)="paginaAnterior()" [disabled]="skip() === 0 || relatorioService.isLoading()">Anterior</button>
          <button type="button" class="btn-secondary" (click)="proximaPagina()" [disabled]="!temProximaPagina() || relatorioService.isLoading()">Proxima</button>
        </div>
      </div>
    </div>
  `,
})
export class RelatoriosComponent implements OnInit {
  readonly relatorioService = inject(RelatorioService);
  private readonly authService = inject(AuthService);
  private readonly destroyRef = inject(DestroyRef);
  private reqSub?: Subscription;

  readonly abaAtiva = signal<'ocupacao' | 'remanejamentos'>('ocupacao');
  readonly erroValidacao = signal<string | null>(null);
  readonly skip = signal<number>(0);
  readonly limit = 50;

  filtroCampusId: number | null = null;
  filtroBloco = '';
  filtroTipoSala = '';
  filtroStatus = '';
  filtroDataInicio = '';
  filtroDataFim = '';

  readonly isAdmin = computed(() => this.authService.currentRole() === 'admin');
  // prettier-ignore
  readonly temProximaPagina = computed(() => {
    const l = this.abaAtiva() === 'ocupacao' ? this.relatorioService.ocupacaoSalas() : this.relatorioService.remanejamentos();
    return l.length >= this.limit;
  });

  // prettier-ignore
  ngOnInit(): void { this.carregarDados(); }

  // prettier-ignore
  selecionarAba(aba: 'ocupacao' | 'remanejamentos'): void {
    if (this.abaAtiva() === aba) return;
    this.abaAtiva.set(aba); this.skip.set(0); this.erroValidacao.set(null); this.relatorioService.limparErro(); this.carregarDados();
  }

  // prettier-ignore
  aplicarFiltros(): void { if (!this.validarPeriodo()) return; this.skip.set(0); this.carregarDados(); }

  // prettier-ignore
  limparFiltros(): void {
    this.filtroCampusId = null; this.filtroBloco = ''; this.filtroTipoSala = ''; this.filtroStatus = ''; this.filtroDataInicio = ''; this.filtroDataFim = '';
    this.erroValidacao.set(null); this.skip.set(0); this.carregarDados();
  }

  // prettier-ignore
  paginaAnterior(): void { if (this.skip() === 0) return; this.skip.update((s) => Math.max(0, s - this.limit)); this.carregarDados(); }

  // prettier-ignore
  proximaPagina(): void { this.skip.update((s) => s + this.limit); this.carregarDados(); }

  // prettier-ignore
  exportarCsv(): void {
    if (!this.validarPeriodo()) return;
    const campus_id = this.obterCampusFiltro();
    const obs$: Observable<Blob> = this.abaAtiva() === 'ocupacao'
      ? this.relatorioService.exportarOcupacaoCsv({ campus_id, bloco: this.filtroBloco, tipo: this.filtroTipoSala })
      : this.relatorioService.exportarRemanejamentosCsv({ campus_id, status: this.filtroStatus, data_inicio: this.filtroDataInicio, data_fim: this.filtroDataFim });
    obs$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ error: () => {} });
  }

  // prettier-ignore
  private validarPeriodo(): boolean {
    if (this.abaAtiva() === 'remanejamentos' && this.filtroDataInicio && this.filtroDataFim && this.filtroDataFim < this.filtroDataInicio) {
      this.erroValidacao.set('A data final deve ser maior ou igual a data inicial.');
      return false;
    }
    this.erroValidacao.set(null); return true;
  }

  // prettier-ignore
  private obterCampusFiltro(): number | undefined {
    return this.isAdmin() && this.filtroCampusId && this.filtroCampusId > 0 ? Number(this.filtroCampusId) : undefined;
  }

  // prettier-ignore
  private carregarDados(): void {
    this.reqSub?.unsubscribe();
    const campus_id = this.obterCampusFiltro();
    const obs$: Observable<unknown> = this.abaAtiva() === 'ocupacao'
      ? this.relatorioService.obterOcupacaoSalas({ campus_id, bloco: this.filtroBloco, tipo: this.filtroTipoSala, skip: this.skip(), limit: this.limit })
      : this.relatorioService.obterRemanejamentos({ campus_id, status: this.filtroStatus, data_inicio: this.filtroDataInicio, data_fim: this.filtroDataFim, skip: this.skip(), limit: this.limit });
    this.reqSub = obs$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ error: () => {} });
  }
}
