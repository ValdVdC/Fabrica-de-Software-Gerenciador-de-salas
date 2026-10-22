import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { Subscription } from 'rxjs';
import { DashboardService } from '../../services/dashboard.service';
import { AuthService } from '../../services/auth.service';

export interface ItemGraficoBarra {
  chave: string | number;
  rotulo: string;
  total: number;
  percentual: number;
}

const DIAS_ISO_8601: ReadonlyArray<{ dia: number; rotulo: string }> = [
  { dia: 0, rotulo: 'Segunda-feira' },
  { dia: 1, rotulo: 'Terca-feira' },
  { dia: 2, rotulo: 'Quarta-feira' },
  { dia: 3, rotulo: 'Quinta-feira' },
  { dia: 4, rotulo: 'Sexta-feira' },
  { dia: 5, rotulo: 'Sabado' },
  { dia: 6, rotulo: 'Domingo' },
];

const TURNOS_PADRAO: ReadonlyArray<{ turno: string; rotulo: string }> = [
  { turno: 'matutino', rotulo: 'Matutino' },
  { turno: 'vespertino', rotulo: 'Vespertino' },
  { turno: 'noturno', rotulo: 'Noturno' },
  { turno: 'integral', rotulo: 'Integral' },
];

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [FormsModule, DatePipe],
  // prettier-ignore
  template: `
    <div class="dashboard-container">
      <header class="dashboard-header">
        <div>
          <h2>Painel Consolidado de Indicadores</h2>
          <p class="section-desc">Monitoramento institucional de salas, ocupacao semanal, remanejamentos e auditoria.</p>
        </div>
        @if (isAdmin()) {
          <div class="dashboard-filter">
            <label for="filtro-campus" class="filter-label">Escopo de Campus:</label>
            <select id="filtro-campus" class="form-input form-select" [ngModel]="campusFiltro()" (ngModelChange)="selecionarCampus($event)">
              <option [ngValue]="null">Todos os Campi</option>
              <option [ngValue]="1">Campus #1</option>
              <option [ngValue]="2">Campus #2</option>
              <option [ngValue]="3">Campus #3</option>
            </select>
          </div>
        }
      </header>

      @if (dashboardService.errorMessage(); as erro) {
        <div class="alert alert-error" role="alert">{{ erro }}</div>
      }

      @if (dashboardService.isLoading()) {
        <div class="panel-card loading-state" role="status">Carregando indicadores consolidados...</div>
      }

      @if (dashboardService.resumo(); as dados) {
        <section class="kpi-grid" aria-label="Indicadores Principais">
          <article class="panel-card kpi-card">
            <span class="kpi-label">Salas Ativas</span>
            <strong class="kpi-value tabular-nums">{{ dados.salas_ativas }}</strong>
          </article>
          <article class="panel-card kpi-card">
            <span class="kpi-label">Turmas Ofertadas</span>
            <strong class="kpi-value tabular-nums">{{ dados.turmas }}</strong>
          </article>
          <article class="panel-card kpi-card">
            <span class="kpi-label">Horarios Alocados</span>
            <strong class="kpi-value tabular-nums">{{ dados.horarios }}</strong>
          </article>
          <article class="panel-card kpi-card">
            <span class="kpi-label">Vagas Recuperadas</span>
            <strong class="kpi-value tabular-nums">{{ dados.vagas_recuperadas }}</strong>
          </article>
        </section>

        <section class="panel-card sugestoes-summary" aria-label="Resumo de Sugestoes">
          <h3>Sugestoes de Remanejamento por Status</h3>
          <div class="status-badges-row tabular-nums">
            <span class="badge badge-pending">Pendentes: {{ dados.sugestoes.pendente }}</span>
            <span class="badge badge-success">Aprovadas: {{ dados.sugestoes.aprovado }}</span>
            <span class="badge badge-danger">Rejeitadas: {{ dados.sugestoes.rejeitado }}</span>
            <span class="badge">Total Geral: {{ dados.sugestoes.total }}</span>
          </div>
        </section>
      }

      <section class="charts-grid" aria-label="Graficos de Ocupacao">
        <article class="panel-card chart-card">
          <h3>Ocupacao por Dia da Semana (ISO 8601)</h3>
          <div class="bar-list">
            @for (item of obterItensGraficoDia(); track item.chave) {
              <div class="bar-row">
                <span class="bar-label">{{ item.rotulo }}</span>
                <svg class="bar-svg" viewBox="0 0 200 14" preserveAspectRatio="none" role="img" [attr.aria-label]="item.rotulo + ': ' + item.total">
                  <rect x="0" y="0" width="200" height="14" rx="3" class="bar-track"></rect>
                  <rect x="0" y="0" [attr.width]="item.percentual * 2" height="14" rx="3" class="bar-fill"></rect>
                </svg>
                <span class="bar-count tabular-nums">{{ item.total }}</span>
              </div>
            }
          </div>
        </article>

        <article class="panel-card chart-card">
          <h3>Ocupacao por Turno Academico</h3>
          <div class="bar-list">
            @for (item of obterItensGraficoTurno(); track item.chave) {
              <div class="bar-row">
                <span class="bar-label">{{ item.rotulo }}</span>
                <svg class="bar-svg" viewBox="0 0 200 14" preserveAspectRatio="none" role="img" [attr.aria-label]="item.rotulo + ': ' + item.total">
                  <rect x="0" y="0" width="200" height="14" rx="3" class="bar-track"></rect>
                  <rect x="0" y="0" [attr.width]="item.percentual * 2" height="14" rx="3" class="bar-fill"></rect>
                </svg>
                <span class="bar-count tabular-nums">{{ item.total }}</span>
              </div>
            }
          </div>
        </article>
      </section>

      <section class="table-card" aria-label="Eventos Recentes de Auditoria">
        <div class="table-card-header">
          <h3>Ultimos Eventos de Auditoria</h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Evento</th>
              <th>Usuario</th>
              <th>Campus</th>
              <th>Detalhes</th>
              <th>Data/Hora</th>
            </tr>
          </thead>
          <tbody>
            @for (ev of eventosRecentes(); track ev.id) {
              <tr>
                <td class="tabular-nums">#{{ ev.id }}</td>
                <td><span class="badge">{{ ev.tipo_evento }}</span></td>
                <td class="tabular-nums">Usuario #{{ ev.usuario_responsavel }}</td>
                <td class="tabular-nums">{{ ev.campus_id ? 'Campus #' + ev.campus_id : '-' }}</td>
                <td>{{ ev.detalhes || 'Sem detalhes adicionais' }}</td>
                <td class="tabular-nums">{{ ev.timestamp | date: 'dd/MM/yyyy HH:mm' }}</td>
              </tr>
            } @empty {
              <tr>
                <td colspan="6" class="empty-msg">Nenhum evento de auditoria registrado no escopo selecionado.</td>
              </tr>
            }
          </tbody>
        </table>
      </section>
    </div>
  `,
})
export class DashboardComponent implements OnInit, OnDestroy {
  readonly dashboardService = inject(DashboardService);
  readonly authService = inject(AuthService);

  private requisicoesAtivas = new Subscription();

  readonly campusFiltro = signal<number | null>(null);
  readonly isAdmin = computed(() => this.authService.currentRole() === 'admin');
  readonly eventosRecentes = computed(
    () => this.dashboardService.resumo()?.eventos_recentes?.slice(0, 10) ?? [],
  );

  ngOnInit(): void {
    this.carregarDados(this.campusFiltro());
  }

  ngOnDestroy(): void {
    this.requisicoesAtivas.unsubscribe();
  }

  selecionarCampus(novoCampus: number | string | null): void {
    const parsed =
      novoCampus === null || novoCampus === '' || novoCampus === 'null' ? null : Number(novoCampus);
    const idValido = parsed !== null && !Number.isNaN(parsed) && parsed > 0 ? parsed : null;
    this.campusFiltro.set(idValido);
    this.carregarDados(idValido);
  }

  carregarDados(campusId: number | null): void {
    this.requisicoesAtivas.unsubscribe();
    this.requisicoesAtivas = new Subscription();
    this.requisicoesAtivas.add(
      this.dashboardService.obterResumo(campusId).subscribe({ error: () => {} }),
    );
    this.requisicoesAtivas.add(
      this.dashboardService.obterOcupacao(campusId).subscribe({ error: () => {} }),
    );
  }

  obterItensGraficoDia(): ItemGraficoBarra[] {
    const lista = this.dashboardService.ocupacao()?.por_dia_semana ?? [];
    const mapa = new Map<number, number>(lista.map((d) => [d.dia_semana, d.total_horarios]));
    const max = Math.max(0, ...DIAS_ISO_8601.map((d) => mapa.get(d.dia) ?? 0));
    return DIAS_ISO_8601.map((d) => {
      const total = mapa.get(d.dia) ?? 0;
      return {
        chave: d.dia,
        rotulo: d.rotulo,
        total,
        percentual: max > 0 ? Math.round((total / max) * 100) : 0,
      };
    });
  }

  obterItensGraficoTurno(): ItemGraficoBarra[] {
    const lista = this.dashboardService.ocupacao()?.por_turno ?? [];
    const mapa = new Map<string, number>(
      lista.map((t) => [t.turno.toLowerCase(), t.total_horarios]),
    );
    const max = Math.max(0, ...TURNOS_PADRAO.map((t) => mapa.get(t.turno) ?? 0));
    return TURNOS_PADRAO.map((t) => {
      const total = mapa.get(t.turno) ?? 0;
      return {
        chave: t.turno,
        rotulo: t.rotulo,
        total,
        percentual: max > 0 ? Math.round((total / max) * 100) : 0,
      };
    });
  }
}
