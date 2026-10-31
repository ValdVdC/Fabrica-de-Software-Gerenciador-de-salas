import { Component, OnInit, inject, signal, computed, DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import {
  AdminService,
  Sala,
  SalaCreate,
  SalaUpdate,
  EquipamentoCreate,
} from '../../services/admin.service';
import { AuthService } from '../../services/auth.service';
import { AlocacaoService } from '../../services/alocacao.service';
import { IaService, SugestaoRemanejamento } from '../../services/ia.service';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [FormsModule, DatePipe],
  // prettier-ignore
  template: `
    <div class="admin-container">
      <header class="admin-header">
        <h2>Gestao de Infraestrutura e Espacos</h2>
        <p>Painel operacional de salas academicas, recursos materiais e alocacao com IA (Human-in-the-Loop).</p>
      </header>

      <nav class="tabs-nav" aria-label="Abas">
        <button type="button" [class.active]="abaAtiva() === 'salas'" (click)="selecionarAba('salas')">Salas &amp; Espacos</button>
        <button type="button" [class.active]="abaAtiva() === 'equipamentos'" (click)="selecionarAba('equipamentos')">Equipamentos</button>
        <button type="button" [class.active]="abaAtiva() === 'alocacao'" (click)="selecionarAba('alocacao')">Alocacao Inteligente</button>
        <button type="button" [class.active]="abaAtiva() === 'remanejamento'" (click)="selecionarAba('remanejamento')">
          Remanejamento IA
          @if (iaService.sugestoes().length > 0) {
            <span class="tab-badge">{{ iaService.sugestoes().length }}</span>
          }
        </button>
        <button type="button" [class.active]="abaAtiva() === 'resumo'" (click)="selecionarAba('resumo')">Resumo &amp; Metricas</button>
      </nav>

      @if (campusId <= 0) { <div class="alert alert-error">Campus nao identificado para o usuario autenticado.</div> }
      @if (adminService.errorMessage()) { <div class="alert alert-error">{{ adminService.errorMessage() }}</div> }
      @if (alocacaoService.errorMessage()) { <div class="alert alert-error">{{ alocacaoService.errorMessage() }}</div> }
      @if (iaService.errorMessage()) { <div class="alert alert-error">{{ iaService.errorMessage() }}</div> }
      @if (mensagemSucesso()) { <div class="alert alert-success">{{ mensagemSucesso() }}</div> }
      @if (alocacaoService.sucessoMessage()) { <div class="alert alert-success">{{ alocacaoService.sucessoMessage() }}</div> }
      @if (iaService.sucessoMessage()) { <div class="alert alert-success">{{ iaService.sucessoMessage() }}</div> }

      @if (abaAtiva() === 'salas') {
        @if (podeGerenciar()) {
        @if (salaEmEdicao(); as editando) {
          <div class="panel-card edit-card">
            <h3>Editar Sala {{ editando.bloco }} - {{ editando.numero }}</h3>
            <form (ngSubmit)="salvarEdicao()" class="form-row">
              <input type="text" [(ngModel)]="formEditBloco" name="editBloco" required maxlength="50" placeholder="Bloco (Ex: A)" class="form-input" />
              <input type="text" [(ngModel)]="formEditNumero" name="editNumero" required maxlength="50" placeholder="Numero (Ex: 101)" class="form-input" />
              <select [(ngModel)]="formEditTipo" name="editTipo" class="form-input form-select">
                <option value="regular">Regular</option>
                <option value="laboratorio">Laboratorio</option>
                <option value="auditorio">Auditorio</option>
                <option value="reuniao">Reuniao</option>
              </select>
              <input type="number" [(ngModel)]="formEditCapacidade" name="editCapacidade" min="1" max="5000" placeholder="Capacidade" class="form-input tabular-nums" />
              <button type="submit" [disabled]="adminService.isLoading()" class="btn-primary">Atualizar Sala</button>
              <button type="button" (click)="cancelarEdicao()" class="btn-secondary">Cancelar</button>
            </form>
          </div>
        } @else {
          <div class="panel-card">
            <h3>Cadastrar Nova Sala</h3>
            <form (ngSubmit)="cadastrarSala()" class="form-row">
              <input type="text" [(ngModel)]="formBloco" name="bloco" required maxlength="50" placeholder="Bloco (Ex: A)" class="form-input" />
              <input type="text" [(ngModel)]="formNumero" name="numero" required maxlength="50" placeholder="Numero (Ex: 101)" class="form-input" />
              <select [(ngModel)]="formTipo" name="tipo" class="form-input form-select"><option value="regular">Regular</option><option value="laboratorio">Laboratorio</option><option value="auditorio">Auditorio</option><option value="reuniao">Reuniao</option></select>
              <input type="number" [(ngModel)]="formCapacidade" name="capacidade" min="1" max="5000" placeholder="Capacidade" class="form-input tabular-nums" />
              <button type="submit" [disabled]="adminService.isLoading() || campusId <= 0" class="btn-primary">Salvar Sala</button>
            </form>
          </div>
        }
        }

        <div class="panel-card"><div class="form-row"><input type="text" data-testid="busca-salas-input" [(ngModel)]="buscaSalas" (ngModelChange)="aoDigitarBuscaSalas($event)" name="buscaSalas" maxlength="100" placeholder="Pesquisar sala por bloco ou numero..." class="form-input flex-2" /></div></div>

        <div class="table-card">
          <table class="data-table">
            <thead><tr><th>Bloco / Sala</th><th>Tipo</th><th>Capacidade</th><th>Turnos</th><th>Acoes</th></tr></thead>
            <tbody>
              @for (sala of adminService.salas(); track sala.id) {
                <tr>
                  <td class="font-bold">{{ sala.bloco }} - Sala {{ sala.numero }}</td>
                  <td><span class="badge">{{ sala.tipo }}</span></td>
                  <td class="tabular-nums">{{ sala.capacidade }} alunos</td>
                  <td>{{ (sala.turnos_disponiveis || []).join(', ') || 'Nenhum' }}</td>
                  <td>
                    @if (podeGerenciar()) {
                    <div class="actions-cell">
                      <button type="button" class="btn-action btn-edit" (click)="iniciarEdicao(sala)" [disabled]="adminService.isLoading()">Editar</button>
                      <button type="button" class="btn-action btn-delete" (click)="excluirSala(sala)" [disabled]="adminService.isLoading()">Excluir</button>
                    </div>
                    } @else { <span>-</span> }
                  </td>
                </tr>
              } @empty {
                <tr><td colspan="5" class="empty-msg">Nenhuma sala cadastrada neste campus.</td></tr>
              }
            </tbody>
          </table>
        </div>
      }

      @if (abaAtiva() === 'equipamentos') {
        @if (podeGerenciar()) {
        <div class="panel-card">
          <h3>Novo Equipamento no Catalogo</h3>
          <form (ngSubmit)="cadastrarEquipamento()" class="form-row">
            <input type="text" [(ngModel)]="formEquipNome" name="equipNome" required minlength="2" maxlength="100" placeholder="Nome (Ex: Projetor)" class="form-input flex-2" />
            <input type="text" [(ngModel)]="formEquipDesc" name="equipDesc" maxlength="255" placeholder="Descricao (opcional)" class="form-input flex-2" />
            <button type="submit" [disabled]="adminService.isLoading()" class="btn-primary">Cadastrar Item</button>
          </form>
        </div>

        <div class="panel-card">
          <h3>Vincular Equipamento a Sala</h3>
          <form (ngSubmit)="vincularEquipamento()" class="form-row">
            <select [(ngModel)]="formAssocSalaId" name="assocSala" required class="form-input form-select">
              <option [ngValue]="null" disabled>Selecione a Sala</option>
              @for (s of adminService.salas(); track s.id) { <option [ngValue]="s.id">{{ s.bloco }} - Sala {{ s.numero }}</option> }
            </select>
            <select [(ngModel)]="formAssocEquipId" name="assocEquip" required class="form-input form-select">
              <option [ngValue]="null" disabled>Selecione o Equipamento</option>
              @for (eq of adminService.equipamentos(); track eq.id) { <option [ngValue]="eq.id">{{ eq.nome }}</option> }
            </select>
            <input type="number" [(ngModel)]="formAssocQtd" name="assocQtd" min="1" max="1000" placeholder="Qtd" class="form-input tabular-nums" style="max-width: 90px;" />
            <button type="submit" [disabled]="adminService.isLoading() || !formAssocSalaId || !formAssocEquipId" class="btn-primary">Vincular</button>
          </form>
        </div>
        }

        <div class="table-card">
          <table class="data-table">
            <thead><tr><th>ID</th><th>Equipamento</th><th>Descricao</th><th>Data</th></tr></thead>
            <tbody>
              @for (eq of adminService.equipamentos(); track eq.id) {
                <tr><td class="tabular-nums">#{{ eq.id }}</td><td class="font-bold">{{ eq.nome }}</td><td>{{ eq.descricao || 'Sem descricao' }}</td><td class="tabular-nums">{{ eq.created_at | date:'shortDate' }}</td></tr>
              } @empty {
                <tr><td colspan="4" class="empty-msg">Nenhum equipamento cadastrado.</td></tr>
              }
            </tbody>
          </table>
        </div>
      }

      @if (abaAtiva() === 'alocacao') {
        @if (podeGerenciar()) {
        <div class="panel-card">
          <h3>Motor de Alocacao Paralelo OpenMP (Sprint 05)</h3>
          <p class="section-desc">Otimizacao combinatoria de salas com heuristica Best-Fit, medicao cientifica de Speedup e persistencia de horarios.</p>
          <div class="form-row" style="margin-top: 0.85rem; align-items: flex-end;">
            <div class="form-group">
              <label class="input-label" for="periodoLetivoInput">Periodo Letivo</label>
              <input id="periodoLetivoInput" type="text" [(ngModel)]="formPeriodoLetivo" name="periodoLetivo" required placeholder="Ex: 2026.1" class="form-input" style="max-width: 130px;" />
            </div>
            <div class="form-group">
              <label class="input-label" for="maxThreadsSelect">Threads OpenMP</label>
              <select id="maxThreadsSelect" [(ngModel)]="formMaxThreads" name="maxThreads" class="form-input form-select" style="max-width: 140px;">
                <option [ngValue]="1">1 Thread (Seq)</option>
                <option [ngValue]="2">2 Threads</option>
                <option [ngValue]="4">4 Threads</option>
                <option [ngValue]="8">8 Threads</option>
              </select>
            </div>
            <div class="form-group form-check">
              <label class="check-label">
                <input type="checkbox" [(ngModel)]="formSalvarNoBanco" name="salvarNoBanco" />
                Persistir no PostgreSQL
              </label>
            </div>
            <button type="button" (click)="executarAlocacao()" [disabled]="alocacaoService.isLoading() || campusId <= 0" class="btn-primary">
              {{ alocacaoService.isLoading() ? 'Processando...' : 'Executar Alocacao Inteligente' }}
            </button>
            <button type="button" (click)="executarBenchmark('medio')" [disabled]="alocacaoService.isLoading()" class="btn-secondary">
              Benchmark Cientifico
            </button>
          </div>
        </div>
        }

        @if (alocacaoService.errorMessage()) { <div class="alert alert-error">{{ alocacaoService.errorMessage() }}</div> }
        @if (alocacaoService.sucessoMessage()) { <div class="alert alert-success">{{ alocacaoService.sucessoMessage() }}</div> }

        @if (alocacaoService.metricas(); as m) {
          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-label">Speedup OpenMP</span>
              <span class="stat-value tabular-nums">{{ m.speedup.toFixed(2) }}x</span>
              <small>{{ m.threads }} threads utilizadas</small>
            </div>
            <div class="stat-card">
              <span class="stat-label">Eficiencia Computacional</span>
              <span class="stat-value tabular-nums">{{ m.eficiencia_pct.toFixed(1) }}%</span>
              <small>Speedup / {{ m.threads }} threads</small>
            </div>
            <div class="stat-card">
              <span class="stat-label">Fracao Amdahl (f)</span>
              <span class="stat-value tabular-nums">{{ m.fracao_amdahl.toFixed(4) }}</span>
              <small>Parametro f teorico</small>
            </div>
            <div class="stat-card">
              <span class="stat-label">Tempos de Execucao</span>
              <span class="stat-value tabular-nums" style="font-size: 1.25rem;">{{ m.tempo_paralelo_ms.toFixed(2) }} ms</span>
              <small>Sequencial: {{ m.tempo_sequencial_ms.toFixed(2) }} ms</small>
            </div>
            <div class="stat-card">
              <span class="stat-label">Alocacoes Concluidas</span>
              <span class="stat-value tabular-nums">{{ m.alocadas }}/{{ m.total_turmas }}</span>
              <small>{{ m.conflitos }} turmas sem vaga</small>
            </div>
          </div>
        }

        @if (alocacaoService.alocacoes().length > 0) {
        <div class="table-card">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Turma</th>
                  <th>Disciplina</th>
                  <th>Sala Alocada</th>
                  <th>Dia da Semana</th>
                  <th>Horario</th>
                  <th>Ociosidade</th>
                </tr>
              </thead>
              <tbody>
                @for (item of alocacaoService.alocacoes(); track item.turma_id) {
                  <tr>
                    <td class="tabular-nums font-bold">#{{ item.turma_id }}</td>
                    <td>{{ item.disciplina_codigo }} - {{ item.disciplina_nome }}</td>
                    <td>
                      <span class="badge" [class.badge-success]="item.sala_id > 0" [class.badge-danger]="item.sala_id <= 0">
                        {{ item.sala_id > 0 ? (item.sala_bloco + ' - Sala ' + item.sala_numero) : 'Sem Sala Disponivel' }}
                      </span>
                    </td>
                    <td>{{ formatarDiaSemana(item.dia_semana) }}</td>
                    <td class="tabular-nums">{{ item.hora_inicio }} - {{ item.hora_fim }}</td>
                    <td class="tabular-nums">{{ item.score_desperdicio !== undefined && item.score_desperdicio >= 0 ? (item.score_desperdicio + ' vagas') : '-' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      }

      @if (abaAtiva() === 'remanejamento') {
        <div class="panel-card remanejamento-hero">
          <div class="remanejamento-toolbar">
            <div class="toolbar-title-group">
              <h3>Remanejamento Inteligente de Salas</h3>
              <p class="section-desc">Identificacao automatica de ociosidade por absenteismo discente com proposta de realocacao para salas menores com liberacao de espaco fisico (Human-in-the-Loop).</p>
            </div>
            <div class="toolbar-actions">
              <select [(ngModel)]="filtroStatusRemanejamento" (change)="carregarSugestoes()" class="form-input form-select" style="max-width: 140px;">
                <option value="pendente">Pendentes</option>
                <option value="aprovado">Aprovadas</option>
                <option value="rejeitado">Rejeitadas</option>
                <option value="">Todas</option>
              </select>
              @if (podeGerenciar()) {
              <button type="button" (click)="executarAnaliseIA()" [disabled]="iaService.isLoading() || campusId <= 0" class="btn-secondary">
                {{ iaService.isLoading() ? 'Processando...' : 'Executar Analise IA' }}
              </button>
              }
              <button type="button" (click)="carregarSugestoes()" [disabled]="iaService.isLoading()" class="btn-secondary">
                Atualizar Lista
              </button>
            </div>
          </div>

          @if (iaService.sugestoes().length > 0) {
            <div class="remanejamento-kpis">
              <div class="kpi-card">
                <span class="kpi-val tabular-nums">{{ sugestoesPendentesCount() }}</span>
                <span class="kpi-label">Sugestoes Pendentes</span>
              </div>
              <div class="kpi-card">
                <span class="kpi-val tabular-nums">{{ riscoMedioAbsenteismo() }}%</span>
                <span class="kpi-label">Risco Medio de Ausencia</span>
              </div>
              <div class="kpi-card">
                <span class="kpi-val kpi-val-green tabular-nums">+{{ totalVagasOtimizadas() }} vagas</span>
                <span class="kpi-label">Potencial de Vagas Liberadas</span>
              </div>
            </div>
          }
        </div>

        @if (iaService.errorMessage()) { <div class="alert alert-error">{{ iaService.errorMessage() }}</div> }
        @if (iaService.sucessoMessage()) { <div class="alert alert-success">{{ iaService.sucessoMessage() }}</div> }

        <div class="sugestoes-grid">
          @for (sug of iaService.sugestoes(); track sug.id) {
            <div class="sugestao-card" [class.card-pendente]="sug.status === 'pendente'" [class.card-aprovado]="sug.status === 'aprovado'" [class.card-rejeitado]="sug.status === 'rejeitado'">
              <div class="sugestao-header">
                <div class="header-main">
                  <span class="code-badge">{{ sug.disciplina_codigo }}</span>
                  <strong class="discipline-title">{{ sug.disciplina_nome || 'Turma Sem Nome' }}</strong>
                  <span class="meta-pill">Turma #{{ sug.turma_id }}</span>
                </div>
                <div class="badges-row">
                  <span class="badge badge-pending">
                    {{ ((sug.prob_ausencia || 0) * 100).toFixed(0) }}% risco absenteismo
                  </span>
                  <span class="badge" [class.badge-pending]="sug.status === 'pendente'" [class.badge-success]="sug.status === 'aprovado'" [class.badge-danger]="sug.status === 'rejeitado'">
                    {{ sug.status }}
                  </span>
                </div>
              </div>

              <div class="sugestao-schedule-bar">
                <div class="schedule-item">
                  <span class="schedule-label">Horario:</span>
                  <span class="schedule-val font-semibold">
                    {{ formatarDiaSemana(sug.dia_semana) }}, {{ sug.hora_inicio || '--:--' }} - {{ sug.hora_fim || '--:--' }}
                  </span>
                </div>
                <div class="schedule-item">
                  <span class="schedule-label">Motivo IA:</span>
                  <span class="schedule-val">
                    {{ sug.motivo }}
                  </span>
                </div>
              </div>

              <div class="comparativo-grid">
                <div class="comparativo-box current-box">
                  <div class="comp-header">
                    <span class="comp-label">Sala Atual (Alocada)</span>
                  </div>
                  <strong class="comp-title">{{ sug.sala_atual_bloco }} - Sala {{ sug.sala_atual_numero }}</strong>
                  <small class="tabular-nums comp-detail">Capacidade Instalada: <strong>{{ sug.sala_atual_capacidade }}</strong> postos</small>
                </div>
                <div class="comparativo-box destaque-box">
                  <div class="comp-header">
                    <span class="comp-label label-destaque">Sala Recomendada (IA)</span>
                  </div>
                  <strong class="comp-title title-destaque">{{ sug.sala_sugerida_bloco }} - Sala {{ sug.sala_sugerida_numero }}</strong>
                  <small class="tabular-nums comp-detail">Capacidade Adequada: <strong>{{ sug.sala_sugerida_capacidade }}</strong> postos</small>
                </div>
                <div class="comparativo-box economia-box">
                  <div class="comp-header">
                    <span class="comp-label label-economia">Otimizacao de Espaco</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
                  </div>
                  <strong class="comp-title title-economia tabular-nums">+{{ calcularEconomiaVagas(sug) }} vagas</strong>
                  <small class="comp-detail detail-sub">Liberadas para alocacao no campus</small>
                </div>
              </div>

              @if (sug.status === 'pendente' && podeGerenciar()) {
                <div class="sugestao-decisao">
                  <div class="input-container">
                    <label class="decision-label" [for]="'justificativa-' + sug.id">Parecer da Gestao Academica (Aprovacao Humana):</label>
                    <input [id]="'justificativa-' + sug.id" type="text" [(ngModel)]="justificativas[sug.id]" placeholder="Justificativa da decisao (obrigatoria em caso de rejeicao)..." class="form-input decision-input" maxlength="500" [disabled]="iaService.isLoading()" />
                  </div>
                  <div class="sugestao-actions">
                    <button type="button" class="btn-primary" (click)="aprovarSugestao(sug)" [disabled]="iaService.isLoading()">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>
                      Aprovar Troca
                    </button>
                    <button type="button" class="btn-outline-danger" (click)="rejeitarSugestao(sug)" [disabled]="iaService.isLoading() || !justificativas[sug.id]?.trim()">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                      Rejeitar
                    </button>
                  </div>
                </div>
              } @else if (sug.status !== 'pendente') {
                <div class="sugestao-finalizada">
                  <span class="finalized-label">Decisao homologada por gestor academico:</span>
                  <span class="finalized-text">Justificativa: {{ sug.justificativa || 'Nenhuma informada.' }}</span>
                </div>
              }
            </div>
          } @empty {
            <div class="panel-card empty-msg">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              <p class="empty-title">Nenhuma sugestao de remanejamento encontrada com o filtro selecionado.</p>
              <p class="empty-desc">Utilize o botao 'Executar Analise IA' acima para rodar a predicao sobre as turmas do periodo letivo ativo ou altere o filtro de status.</p>
            </div>
          }
        </div>
      }

      @if (abaAtiva() === 'resumo') {
        <div class="stats-grid">
          <div class="stat-card"><span class="stat-label">Total de Salas</span><span class="stat-value tabular-nums">{{ totalSalas() }}</span><small>Espacos fisicos ativos</small></div>
          <div class="stat-card"><span class="stat-label">Capacidade Instalada</span><span class="stat-value tabular-nums">{{ capacidadeTotal() }}</span><small>Postos academicos</small></div>
          <div class="stat-card"><span class="stat-label">Itens no Catalogo</span><span class="stat-value tabular-nums">{{ totalEquipamentos() }}</span><small>Equipamentos cadastrados</small></div>
        </div>
      }
    </div>
  `,
  styles: [],
})
export class AdminComponent implements OnInit {
  readonly adminService = inject(AdminService);
  readonly authService = inject(AuthService);
  readonly alocacaoService = inject(AlocacaoService);
  readonly iaService = inject(IaService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly buscaSalas$ = new Subject<string>();
  buscaSalas = '';

  readonly abaAtiva = signal<'salas' | 'equipamentos' | 'alocacao' | 'remanejamento' | 'resumo'>(
    'salas',
  );
  readonly mensagemSucesso = signal<string | null>(null);
  readonly podeGerenciar = computed(() => this.authService.hasRole('admin'));

  campusId = 0;
  formBloco = '';
  formNumero = '';
  formTipo: 'regular' | 'laboratorio' | 'auditorio' | 'reuniao' = 'regular';
  formCapacidade = 40;

  readonly salaEmEdicao = signal<Sala | null>(null);
  formEditBloco = '';
  formEditNumero = '';
  formEditTipo: 'regular' | 'laboratorio' | 'auditorio' | 'reuniao' = 'regular';
  formEditCapacidade = 40;

  formAssocSalaId: number | null = null;
  formAssocEquipId: number | null = null;
  formAssocQtd = 1;

  formEquipNome = '';
  formEquipDesc = '';

  // Formulario da aba de Alocacao Inteligente
  formPeriodoLetivo = '2026.1';
  formMaxThreads = 4;
  formSalvarNoBanco = true;

  // Formulario e estado da aba de Remanejamento IA
  filtroStatusRemanejamento = 'pendente';
  justificativas: Record<number, string> = {};

  readonly totalSalas = computed(() => this.adminService.salas().length);
  readonly capacidadeTotal = computed(() =>
    this.adminService.salas().reduce((acc, s) => acc + s.capacidade, 0),
  );
  readonly totalEquipamentos = computed(() => this.adminService.equipamentos().length);

  readonly sugestoesPendentesCount = computed(
    () => this.iaService.sugestoes().filter((s) => s.status === 'pendente').length,
  );
  readonly riscoMedioAbsenteismo = computed(() => {
    const list = this.iaService.sugestoes();
    if (list.length === 0) return 0;
    const soma = list.reduce((acc, s) => acc + (s.prob_ausencia || 0), 0);
    return Math.round((soma / list.length) * 100);
  });
  readonly totalVagasOtimizadas = computed(() => {
    return this.iaService.sugestoes().reduce((acc, s) => acc + this.calcularEconomiaVagas(s), 0);
  });

  ngOnInit(): void {
    const user = this.authService.currentUser();
    this.campusId = user?.campus_id && user.campus_id > 0 ? user.campus_id : 0;
    this.buscaSalas$
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe((q) => {
        if (this.campusId > 0)
          this.adminService.listarSalas(this.campusId, q).subscribe({ error: () => {} });
      });
    if (this.campusId > 0) {
      this.adminService.listarSalas(this.campusId).subscribe({ error: () => {} });
      this.iaService.obterSugestoes('pendente', this.campusId).subscribe({ error: () => {} });
    }
    this.adminService.listarEquipamentos().subscribe({ error: () => {} });
  }

  // prettier-ignore
  aoDigitarBuscaSalas(termo: string): void { this.buscaSalas$.next(termo); }

  selecionarAba(aba: 'salas' | 'equipamentos' | 'alocacao' | 'remanejamento' | 'resumo'): void {
    this.abaAtiva.set(aba);
    this.mensagemSucesso.set(null);
    this.iaService.limparMensagens();
    this.alocacaoService.limparMensagens();
    this.cancelarEdicao();
    if (aba === 'remanejamento' && this.campusId > 0 && this.iaService.sugestoes().length === 0) {
      this.carregarSugestoes();
    }
  }

  carregarSugestoes(): void {
    const statusFiltro = this.filtroStatusRemanejamento || undefined;
    const campus = this.campusId > 0 ? this.campusId : undefined;
    this.iaService.obterSugestoes(statusFiltro, campus).subscribe({ error: () => {} });
  }

  executarAnaliseIA(): void {
    if (!this.podeGerenciar() || this.campusId <= 0 || this.iaService.isLoading()) return;
    this.iaService.dispararAnalise(this.campusId, this.formPeriodoLetivo, 0.4).subscribe({
      next: () => {
        this.filtroStatusRemanejamento = 'pendente';
        this.carregarSugestoes();
      },
      error: () => {},
    });
  }

  aprovarSugestao(sug: SugestaoRemanejamento): void {
    if (!this.podeGerenciar() || this.iaService.isLoading()) return;
    const just = this.justificativas[sug.id];
    this.iaService.aprovarSugestao(sug.id, just).subscribe({
      next: () => {
        delete this.justificativas[sug.id];
      },
      error: () => {},
    });
  }

  rejeitarSugestao(sug: SugestaoRemanejamento): void {
    if (!this.podeGerenciar() || this.iaService.isLoading()) return;
    const just = this.justificativas[sug.id]?.trim();
    if (!just) {
      this.iaService.definirErro('Justificativa e obrigatoria para rejeitar a sugestao.');
      return;
    }
    this.iaService.rejeitarSugestao(sug.id, just).subscribe({
      next: () => {
        delete this.justificativas[sug.id];
      },
      error: () => {},
    });
  }

  calcularEconomiaVagas(sug: SugestaoRemanejamento): number {
    const atual = sug.sala_atual_capacidade || 0;
    const sugerida = sug.sala_sugerida_capacidade || 0;
    return Math.max(0, atual - sugerida);
  }

  iniciarEdicao(sala: Sala): void {
    if (!this.podeGerenciar()) return;
    this.salaEmEdicao.set(sala);
    this.formEditBloco = sala.bloco;
    this.formEditNumero = sala.numero;
    this.formEditTipo = sala.tipo;
    this.formEditCapacidade = sala.capacidade;
    this.mensagemSucesso.set(null);
  }

  cancelarEdicao(): void {
    this.salaEmEdicao.set(null);
  }

  salvarEdicao(): void {
    const salaAtual = this.salaEmEdicao();
    if (!this.podeGerenciar() || !salaAtual || this.adminService.isLoading()) return;

    const bloco = this.formEditBloco.trim();
    const numero = this.formEditNumero.trim();
    if (!bloco || !numero) return;

    const capNum = Math.floor(Number(this.formEditCapacidade));
    if (isNaN(capNum) || capNum < 1 || capNum > 5000) return;

    const payload: SalaUpdate = {
      bloco,
      numero,
      tipo: this.formEditTipo,
      capacidade: capNum,
    };

    this.adminService.atualizarSala(salaAtual.id, payload).subscribe({
      next: () => {
        this.mensagemSucesso.set(`Sala ${bloco} - ${numero} atualizada com sucesso.`);
        this.cancelarEdicao();
      },
      error: () => {},
    });
  }

  cadastrarSala(): void {
    if (!this.podeGerenciar() || this.adminService.isLoading() || this.campusId <= 0) return;

    const bloco = this.formBloco.trim();
    const numero = this.formNumero.trim();
    if (!bloco || !numero) return;

    const capNum = Math.floor(Number(this.formCapacidade));
    if (isNaN(capNum) || capNum < 1 || capNum > 5000) return;

    const payload: SalaCreate = {
      campus_id: this.campusId,
      bloco,
      numero,
      tipo: this.formTipo,
      capacidade: capNum,
      turnos_disponiveis: ['matutino', 'vespertino', 'noturno'],
    };

    this.adminService.criarSala(payload).subscribe({
      next: (novaSala) => {
        this.mensagemSucesso.set(
          `Sala ${novaSala.bloco} - ${novaSala.numero} cadastrada com sucesso.`,
        );
        this.formBloco = '';
        this.formNumero = '';
        this.formCapacidade = 40;
        this.formTipo = 'regular';
      },
      error: () => {},
    });
  }

  excluirSala(sala: Sala): void {
    if (!this.podeGerenciar() || this.adminService.isLoading()) return;
    this.adminService.excluirSala(sala.id).subscribe({
      next: () => {
        this.mensagemSucesso.set(`Sala ${sala.bloco} - ${sala.numero} excluida com sucesso.`);
        if (this.salaEmEdicao()?.id === sala.id) {
          this.cancelarEdicao();
        }
      },
      error: () => {},
    });
  }

  cadastrarEquipamento(): void {
    if (!this.podeGerenciar() || this.adminService.isLoading()) return;

    const nome = this.formEquipNome.trim();
    if (!nome) return;

    const payload: EquipamentoCreate = {
      nome,
      descricao: this.formEquipDesc.trim() || undefined,
    };

    this.adminService.criarEquipamento(payload).subscribe({
      next: (novo) => {
        this.mensagemSucesso.set(`Equipamento '${novo.nome}' cadastrado com sucesso.`);
        this.formEquipNome = '';
        this.formEquipDesc = '';
      },
      error: () => {},
    });
  }

  vincularEquipamento(): void {
    if (
      !this.podeGerenciar() ||
      this.adminService.isLoading() ||
      !this.formAssocSalaId ||
      !this.formAssocEquipId
    )
      return;

    const qtdNum = Math.floor(Number(this.formAssocQtd));
    if (isNaN(qtdNum) || qtdNum < 1 || qtdNum > 1000) return;

    this.adminService
      .associarEquipamento(this.formAssocSalaId, {
        equipamento_id: this.formAssocEquipId,
        quantidade: qtdNum,
      })
      .subscribe({
        next: () => {
          this.mensagemSucesso.set('Equipamento vinculado a sala com sucesso.');
          this.formAssocSalaId = null;
          this.formAssocEquipId = null;
          this.formAssocQtd = 1;
        },
        error: () => {},
      });
  }

  formatarDiaSemana(dia: number | null | undefined): string {
    if (dia === null || dia === undefined) {
      return 'Dia a definir';
    }
    const dias = [
      'Segunda-feira',
      'Terca-feira',
      'Quarta-feira',
      'Quinta-feira',
      'Sexta-feira',
      'Sabado',
      'Domingo',
    ];
    return dias[dia] ?? `Dia ${dia}`;
  }

  executarAlocacao(): void {
    if (!this.podeGerenciar() || this.campusId <= 0 || this.alocacaoService.isLoading()) return;
    this.alocacaoService
      .otimizarAlocacao({
        periodo_letivo: this.formPeriodoLetivo.trim() || '2026.1',
        campus_id: this.campusId,
        max_threads: Number(this.formMaxThreads) || 4,
        salvar_no_banco: this.formSalvarNoBanco,
      })
      .subscribe({
        next: () => {
          if (this.formSalvarNoBanco) {
            this.adminService.listarSalas(this.campusId).subscribe({ error: () => {} });
          }
        },
        error: () => {},
      });
  }

  executarBenchmark(cenario: string = 'medio'): void {
    if (!this.podeGerenciar() || this.alocacaoService.isLoading()) return;
    this.alocacaoService
      .executarBenchmark({
        cenario,
        threads: Number(this.formMaxThreads) || 4,
      })
      .subscribe({ error: () => {} });
  }
}
