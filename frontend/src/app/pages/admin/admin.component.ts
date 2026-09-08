import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { AdminService, SalaCreate, EquipamentoCreate } from '../../services/admin.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [FormsModule, DatePipe],
  // prettier-ignore
  template: `
    <div class="admin-container">
      <header class="admin-header">
        <h2>Gestao de Infraestrutura e Espacos</h2>
        <p>Painel operacional de salas academicas, recursos materiais e controle institucional.</p>
      </header>

      <nav class="tabs-nav" aria-label="Abas">
        <button type="button" [class.active]="abaAtiva() === 'salas'" (click)="selecionarAba('salas')">Salas &amp; Espacos</button>
        <button type="button" [class.active]="abaAtiva() === 'equipamentos'" (click)="selecionarAba('equipamentos')">Equipamentos</button>
        <button type="button" [class.active]="abaAtiva() === 'resumo'" (click)="selecionarAba('resumo')">Resumo &amp; Metricas</button>
      </nav>

      @if (campusId <= 0) { <div class="alert alert-error">Campus nao identificado para o usuario autenticado.</div> }
      @if (adminService.errorMessage()) { <div class="alert alert-error">{{ adminService.errorMessage() }}</div> }
      @if (mensagemSucesso()) { <div class="alert alert-success">{{ mensagemSucesso() }}</div> }

      @if (abaAtiva() === 'salas') {
        <div class="panel-card">
          <h3>Cadastrar Nova Sala</h3>
          <form (ngSubmit)="cadastrarSala()" class="form-row">
            <input type="text" [(ngModel)]="formBloco" name="bloco" required maxlength="50" placeholder="Bloco (Ex: A)" class="form-input" />
            <input type="text" [(ngModel)]="formNumero" name="numero" required maxlength="50" placeholder="Numero (Ex: 101)" class="form-input" />
            <select [(ngModel)]="formTipo" name="tipo" class="form-input"><option value="regular">Regular</option><option value="laboratorio">Laboratorio</option><option value="auditorio">Auditorio</option><option value="reuniao">Reuniao</option></select>
            <input type="number" [(ngModel)]="formCapacidade" name="capacidade" min="1" max="5000" placeholder="Capacidade" class="form-input tabular-nums" />
            <button type="submit" [disabled]="adminService.isLoading() || campusId <= 0" class="btn-primary">Salvar Sala</button>
          </form>
        </div>

        <div class="table-card">
          <table class="data-table">
            <thead><tr><th>Bloco / Sala</th><th>Tipo</th><th>Capacidade</th><th>Turnos</th></tr></thead>
            <tbody>
              @for (sala of adminService.salas(); track sala.id) {
                <tr><td class="font-bold">{{ sala.bloco }} - Sala {{ sala.numero }}</td><td><span class="badge">{{ sala.tipo }}</span></td><td class="tabular-nums">{{ sala.capacidade }} alunos</td><td>{{ (sala.turnos_disponiveis || []).join(', ') || 'Nenhum' }}</td></tr>
              } @empty {
                <tr><td colspan="4" class="empty-msg">Nenhuma sala cadastrada neste campus.</td></tr>
              }
            </tbody>
          </table>
        </div>
      }

      @if (abaAtiva() === 'equipamentos') {
        <div class="panel-card">
          <h3>Novo Equipamento no Catalogo</h3>
          <form (ngSubmit)="cadastrarEquipamento()" class="form-row">
            <input type="text" [(ngModel)]="formEquipNome" name="equipNome" required minlength="2" maxlength="100" placeholder="Nome (Ex: Projetor)" class="form-input flex-2" />
            <input type="text" [(ngModel)]="formEquipDesc" name="equipDesc" maxlength="255" placeholder="Descricao (opcional)" class="form-input flex-2" />
            <button type="submit" [disabled]="adminService.isLoading()" class="btn-primary">Cadastrar Item</button>
          </form>
        </div>

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

      @if (abaAtiva() === 'resumo') {
        <div class="stats-grid">
          <div class="stat-card"><span class="stat-label">Total de Salas</span><span class="stat-value tabular-nums">{{ totalSalas() }}</span><small>Espacos fisicos ativos</small></div>
          <div class="stat-card"><span class="stat-label">Capacidade Instalada</span><span class="stat-value tabular-nums">{{ capacidadeTotal() }}</span><small>Postos academicos</small></div>
          <div class="stat-card"><span class="stat-label">Itens no Catalogo</span><span class="stat-value tabular-nums">{{ totalEquipamentos() }}</span><small>Equipamentos cadastrados</small></div>
        </div>
      }
    </div>
  `,
  // prettier-ignore
  styles: [`
    .admin-container { display: flex; flex-direction: column; gap: 1.25rem; }
    .admin-header h2 { margin: 0; font-size: 1.5rem; font-weight: 700; color: #0f172a; }
    .admin-header p { margin: 0.25rem 0 0; font-size: 0.875rem; color: #64748b; }
    .tabs-nav { display: flex; gap: 0.5rem; border-bottom: 1px solid #e2e8f0; }
    .tabs-nav button { background: none; border: none; padding: 0.5rem 1rem; font-size: 0.875rem; font-weight: 500; color: #64748b; cursor: pointer; border-bottom: 2px solid transparent; }
    .tabs-nav button.active { color: #0f172a; font-weight: 700; border-bottom-color: #0f172a; }
    .alert { padding: 0.75rem; border-radius: 4px; font-size: 0.8125rem; }
    .alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; }
    .alert-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
    .panel-card, .table-card, .stat-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; }
    .panel-card { padding: 1rem; }
    .panel-card h3 { margin: 0 0 0.75rem; font-size: 0.9375rem; font-weight: 600; color: #0f172a; }
    .form-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .form-input { padding: 0.4rem 0.6rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 0.8125rem; flex: 1; min-width: 110px; }
    .flex-2 { flex: 2; }
    .btn-primary { background: #0f172a; color: #fff; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
    .table-card { overflow: hidden; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; text-align: left; }
    .data-table th, .data-table td { padding: 0.6rem 0.75rem; border-bottom: 1px solid #e2e8f0; }
    .data-table th { background: #f8fafc; color: #475569; font-weight: 600; }
    .data-table td { color: #334155; border-bottom-color: #f1f5f9; }
    .data-table tr:hover { background: #f8fafc; }
    .font-bold { font-weight: 600; color: #0f172a; }
    .badge { background: #f1f5f9; color: #334155; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.75rem; text-transform: capitalize; }
    .empty-msg { text-align: center; color: #94a3b8; padding: 1.5rem; }
    .tabular-nums { font-variant-numeric: tabular-nums; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
    .stat-card { padding: 1rem; display: flex; flex-direction: column; }
    .stat-label { font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 600; }
    .stat-value { font-size: 1.75rem; font-weight: 700; color: #0f172a; margin: 0.25rem 0; }
    .stat-card small { font-size: 0.75rem; color: #94a3b8; }
  `],
})
export class AdminComponent implements OnInit {
  readonly adminService = inject(AdminService);
  readonly authService = inject(AuthService);

  readonly abaAtiva = signal<'salas' | 'equipamentos' | 'resumo'>('salas');
  readonly mensagemSucesso = signal<string | null>(null);

  campusId = 0;
  formBloco = '';
  formNumero = '';
  formTipo: 'regular' | 'laboratorio' | 'auditorio' | 'reuniao' = 'regular';
  formCapacidade = 40;

  formEquipNome = '';
  formEquipDesc = '';

  readonly totalSalas = computed(() => this.adminService.salas().length);
  readonly capacidadeTotal = computed(() =>
    this.adminService.salas().reduce((acc, s) => acc + s.capacidade, 0),
  );
  readonly totalEquipamentos = computed(() => this.adminService.equipamentos().length);

  ngOnInit(): void {
    const user = this.authService.currentUser();
    this.campusId = user?.campus_id && user.campus_id > 0 ? user.campus_id : 0;
    if (this.campusId > 0) {
      this.adminService.listarSalas(this.campusId).subscribe({ error: () => {} });
    }
    this.adminService.listarEquipamentos().subscribe({ error: () => {} });
  }

  selecionarAba(aba: 'salas' | 'equipamentos' | 'resumo'): void {
    this.abaAtiva.set(aba);
    this.mensagemSucesso.set(null);
  }

  cadastrarSala(): void {
    this.mensagemSucesso.set(null);
    if (this.adminService.isLoading() || this.campusId <= 0) return;

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
      turnos_disponiveis: ['matutino', 'vespertino'],
    };

    this.adminService.criarSala(payload).subscribe({
      next: (s) => {
        this.mensagemSucesso.set(`Sala ${s.bloco}-${s.numero} cadastrada com sucesso!`);
        this.formBloco = '';
        this.formNumero = '';
        this.formTipo = 'regular';
        this.formCapacidade = 40;
      },
      error: () => {},
    });
  }

  cadastrarEquipamento(): void {
    this.mensagemSucesso.set(null);
    if (this.adminService.isLoading()) return;

    const nome = this.formEquipNome.trim();
    if (nome.length < 2) return;

    const desc = this.formEquipDesc.trim();
    const payload: EquipamentoCreate = {
      nome,
      descricao: desc.length > 0 ? desc : undefined,
    };

    this.adminService.criarEquipamento(payload).subscribe({
      next: (e) => {
        this.mensagemSucesso.set(`Equipamento '${e.nome}' adicionado ao catalogo!`);
        this.formEquipNome = '';
        this.formEquipDesc = '';
      },
      error: () => {},
    });
  }
}
