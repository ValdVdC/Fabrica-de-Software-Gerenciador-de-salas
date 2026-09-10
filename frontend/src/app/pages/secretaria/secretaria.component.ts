import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import {
  SecretariaService,
  CursoCreate,
  DisciplinaCreate,
  TurmaCreate,
  MatriculaCreate,
  TurnoType,
} from '../../services/secretaria.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-secretaria',
  standalone: true,
  imports: [FormsModule, DatePipe],
  // prettier-ignore
  template: `
    <div class="sec-container">
      <header class="sec-header"><h2>Gestao Academica e Secretaria</h2><p>Administracao de cursos, catalogo de disciplinas, turmas e matriculas discentes.</p></header>
      <nav class="tabs-nav" aria-label="Abas">
        <button type="button" [class.active]="abaAtiva() === 'cursos'" (click)="selecionarAba('cursos')">Cursos</button>
        <button type="button" [class.active]="abaAtiva() === 'disciplinas'" (click)="selecionarAba('disciplinas')">Disciplinas</button>
        <button type="button" [class.active]="abaAtiva() === 'turmas'" (click)="selecionarAba('turmas')">Turmas</button>
        <button type="button" [class.active]="abaAtiva() === 'matriculas'" (click)="selecionarAba('matriculas')">Matriculas</button>
        <button type="button" [class.active]="abaAtiva() === 'resumo'" (click)="selecionarAba('resumo')">Metricas</button>
      </nav>
      @if (campusId <= 0) { <div class="alert alert-error">Campus nao identificado para o usuario autenticado.</div> }
      @if (secretariaService.errorMessage()) { <div class="alert alert-error">{{ secretariaService.errorMessage() }}</div> }
      @if (mensagemSucesso()) { <div class="alert alert-success">{{ mensagemSucesso() }}</div> }

      @if (abaAtiva() === 'cursos') {
        <div class="panel-card"><h3>Cadastrar Novo Curso</h3>
          <form (ngSubmit)="cadastrarCurso()" class="form-row">
            <input type="text" [(ngModel)]="formCursoNome" name="cursoNome" required maxlength="100" placeholder="Nome do Curso (Ex: Engenharia)" class="form-input flex-2" />
            <input type="text" [(ngModel)]="formCursoCodigo" name="cursoCodigo" required maxlength="20" placeholder="Codigo (Ex: ENG)" class="form-input" />
            <button type="submit" [disabled]="secretariaService.isLoading() || campusId <= 0 || !formCursoNome.trim() || !formCursoCodigo.trim()" class="btn-primary">Salvar Curso</button>
          </form>
        </div>
        <div class="table-card"><table class="data-table">
          <thead><tr><th>ID</th><th>Nome do Curso</th><th>Codigo</th></tr></thead>
          <tbody>
            @for (c of secretariaService.cursos(); track c.id) {
              <tr><td class="tabular-nums">#{{ c.id }}</td><td class="font-bold">{{ c.nome }}</td><td><span class="badge">{{ c.codigo }}</span></td></tr>
            } @empty { <tr><td colspan="3" class="empty-msg">Nenhum curso cadastrado neste campus.</td></tr> }
          </tbody>
        </table></div>
      }

      @if (abaAtiva() === 'disciplinas') {
        <div class="panel-card"><h3>Nova Disciplina</h3>
          <form (ngSubmit)="cadastrarDisciplina()" class="form-row">
            <select [(ngModel)]="formDiscCursoId" name="discCurso" required class="form-input">
              <option [ngValue]="null" disabled>Selecione o Curso</option>
              @for (c of secretariaService.cursos(); track c.id) { <option [ngValue]="c.id">{{ c.nome }} ({{ c.codigo }})</option> }
            </select>
            <input type="text" [(ngModel)]="formDiscNome" name="discNome" required maxlength="100" placeholder="Nome (Ex: Algoritmos)" class="form-input flex-2" />
            <input type="text" [(ngModel)]="formDiscCodigo" name="discCodigo" required maxlength="20" placeholder="Codigo (Ex: ALG1)" class="form-input" />
            <input type="number" [(ngModel)]="formDiscCarga" name="discCarga" min="1" max="1000" placeholder="Carga Horaria (h)" class="form-input tabular-nums" />
            <button type="submit" [disabled]="secretariaService.isLoading() || campusId <= 0 || !formDiscCursoId || !formDiscNome.trim() || !formDiscCodigo.trim()" class="btn-primary">Salvar Disciplina</button>
          </form>
        </div>
        <div class="table-card"><table class="data-table">
          <thead><tr><th>ID</th><th>Disciplina</th><th>Codigo</th><th>Carga Horaria</th><th>Curso</th></tr></thead>
          <tbody>
            @for (d of secretariaService.disciplinas(); track d.id) {
              <tr><td class="tabular-nums">#{{ d.id }}</td><td class="font-bold">{{ d.nome }}</td><td><span class="badge">{{ d.codigo }}</span></td><td class="tabular-nums">{{ d.carga_horaria }}h</td><td>Curso #{{ d.curso_id }}</td></tr>
            } @empty { <tr><td colspan="5" class="empty-msg">Nenhuma disciplina cadastrada.</td></tr> }
          </tbody>
        </table></div>
      }

      @if (abaAtiva() === 'turmas') {
        <div class="panel-card"><h3>Nova Turma Semestral</h3>
          <form (ngSubmit)="cadastrarTurma()" class="form-row">
            <select [(ngModel)]="formTurmaDiscId" name="turmaDisc" required class="form-input">
              <option [ngValue]="null" disabled>Selecione a Disciplina</option>
              @for (d of secretariaService.disciplinas(); track d.id) { <option [ngValue]="d.id">{{ d.nome }} ({{ d.codigo }})</option> }
            </select>
            <input type="text" [(ngModel)]="formTurmaPeriodo" name="turmaPeriodo" required maxlength="10" placeholder="Periodo (Ex: 2026.1)" class="form-input" />
            <select [(ngModel)]="formTurmaTurno" name="turmaTurno" class="form-input">
              <option value="matutino">Matutino</option><option value="vespertino">Vespertino</option><option value="noturno">Noturno</option><option value="integral">Integral</option>
            </select>
            <input type="number" [(ngModel)]="formTurmaProfId" name="turmaProf" placeholder="ID Professor (opcional)" class="form-input tabular-nums" />
            <button type="submit" [disabled]="secretariaService.isLoading() || campusId <= 0 || !formTurmaDiscId || !formTurmaPeriodo.trim()" class="btn-primary">Criar Turma</button>
          </form>
        </div>
        <div class="table-card"><table class="data-table">
          <thead><tr><th>ID</th><th>Disciplina</th><th>Periodo</th><th>Turno</th><th>Matriculados</th><th>Docente</th></tr></thead>
          <tbody>
            @for (t of secretariaService.turmas(); track t.id) {
              <tr><td class="tabular-nums">#{{ t.id }}</td><td class="font-bold">Disciplina #{{ t.disciplina_id }}</td><td class="tabular-nums">{{ t.periodo_letivo }}</td><td><span class="badge">{{ t.turno_preferido }}</span></td><td class="tabular-nums font-bold">{{ t.num_matriculados }}</td><td>{{ t.professor_id ? 'Prof. #' + t.professor_id : 'Nao atribuido' }}</td></tr>
            } @empty { <tr><td colspan="6" class="empty-msg">Nenhuma turma cadastrada neste campus.</td></tr> }
          </tbody>
        </table></div>
      }

      @if (abaAtiva() === 'matriculas') {
        <div class="panel-card"><h3>Matricular Aluno em Turma</h3>
          <form (ngSubmit)="matricularAluno()" class="form-row">
            <select [(ngModel)]="formMatTurmaId" name="matTurma" required class="form-input">
              <option [ngValue]="null" disabled>Selecione a Turma</option>
              @for (t of secretariaService.turmas(); track t.id) { <option [ngValue]="t.id">Turma #{{ t.id }} ({{ t.periodo_letivo }} - {{ t.turno_preferido }})</option> }
            </select>
            <input type="number" [(ngModel)]="formMatAlunoId" name="matAluno" required min="1" placeholder="ID do Aluno (Ex: 5)" class="form-input tabular-nums" />
            <button type="submit" [disabled]="secretariaService.isLoading() || campusId <= 0 || !formMatTurmaId || !formMatAlunoId" class="btn-primary">Confirmar Matricula</button>
          </form>
        </div>
        <div class="table-card"><table class="data-table">
          <thead><tr><th>ID</th><th>Aluno</th><th>Turma</th><th>Status</th><th>Data</th></tr></thead>
          <tbody>
            @for (m of secretariaService.matriculas(); track m.id) {
              <tr><td class="tabular-nums">#{{ m.id }}</td><td class="tabular-nums">Aluno #{{ m.aluno_id }}</td><td class="tabular-nums">Turma #{{ m.turma_id }}</td><td><span class="badge">{{ m.status }}</span></td><td class="tabular-nums">{{ m.data_matricula | date:'shortDate' }}</td></tr>
            } @empty { <tr><td colspan="5" class="empty-msg">Nenhuma matricula registrada.</td></tr> }
          </tbody>
        </table></div>
      }

      @if (abaAtiva() === 'resumo') {
        <div class="stats-grid">
          <div class="stat-card"><span class="stat-label">Total de Cursos</span><span class="stat-value tabular-nums">{{ totalCursos() }}</span><small>Ofertas ativas no campus</small></div>
          <div class="stat-card"><span class="stat-label">Disciplinas Cadastradas</span><span class="stat-value tabular-nums">{{ totalDisciplinas() }}</span><small>Componentes curriculares</small></div>
          <div class="stat-card"><span class="stat-label">Turmas Abertas</span><span class="stat-value tabular-nums">{{ totalTurmas() }}</span><small>Turmas do periodo</small></div>
          <div class="stat-card"><span class="stat-label">Matriculas Efetivadas</span><span class="stat-value tabular-nums">{{ totalMatriculas() }}</span><small>Inscricoes em turmas</small></div>
        </div>
      }
    </div>
  `,
  // prettier-ignore
  styles: [`
    .sec-container { display: flex; flex-direction: column; gap: 1.25rem; }
    .sec-header h2 { margin: 0; font-size: 1.5rem; font-weight: 700; color: #0f172a; } .sec-header p { margin: 0.25rem 0 0; font-size: 0.875rem; color: #64748b; }
    .tabs-nav { display: flex; gap: 0.5rem; border-bottom: 1px solid #e2e8f0; } .tabs-nav button { background: none; border: none; padding: 0.5rem 1rem; font-size: 0.875rem; font-weight: 500; color: #64748b; cursor: pointer; border-bottom: 2px solid transparent; } .tabs-nav button.active { color: #0f172a; font-weight: 700; border-bottom-color: #0f172a; }
    .alert { padding: 0.75rem; border-radius: 4px; font-size: 0.8125rem; } .alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; } .alert-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
    .panel-card, .table-card, .stat-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 1rem; } .panel-card h3 { margin: 0 0 0.75rem; font-size: 1rem; color: #0f172a; font-weight: 600; }
    .form-row { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; } .form-input { padding: 0.5rem 0.75rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 0.875rem; color: #1e293b; background: #fff; } .form-input.flex-2 { flex: 2; min-width: 180px; }
    .btn-primary { background: #0f172a; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 4px; font-size: 0.875rem; font-weight: 500; cursor: pointer; } .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; text-align: left; } .data-table th, .data-table td { padding: 0.75rem; border-bottom: 1px solid #f1f5f9; color: #334155; } .data-table th { background: #f8fafc; border-bottom-color: #e2e8f0; color: #475569; font-weight: 600; }
    .font-bold { font-weight: 600; color: #0f172a; } .badge { display: inline-block; padding: 0.125rem 0.375rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; background: #f1f5f9; color: #334155; text-transform: uppercase; }
    .empty-msg { text-align: center; color: #94a3b8; padding: 2rem 1rem; } .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
    .stat-card { display: flex; flex-direction: column; gap: 0.25rem; } .stat-label { font-size: 0.8125rem; color: #64748b; font-weight: 500; } .stat-value { font-size: 1.75rem; font-weight: 700; color: #0f172a; } .stat-card small { font-size: 0.75rem; color: #94a3b8; }
    .tabular-nums { font-variant-numeric: tabular-nums; }
  `],
})
export class SecretariaComponent implements OnInit {
  readonly secretariaService = inject(SecretariaService);
  private readonly authService = inject(AuthService);

  campusId = 0;
  // prettier-ignore
  readonly abaAtiva = signal<'cursos' | 'disciplinas' | 'turmas' | 'matriculas' | 'resumo'>('cursos');
  readonly mensagemSucesso = signal<string | null>(null);

  // prettier-ignore
  formCursoNome = '';
  formCursoCodigo = '';
  formDiscCursoId: number | null = null;
  formDiscNome = '';
  formDiscCodigo = '';
  // prettier-ignore
  formDiscCarga: number | null = 60;
  formTurmaDiscId: number | null = null;
  formTurmaProfId: number | null = null;
  // prettier-ignore
  formTurmaPeriodo = '2026.1';
  formTurmaTurno: TurnoType = 'matutino';
  formMatTurmaId: number | null = null;
  formMatAlunoId: number | null = null;

  // prettier-ignore
  readonly totalCursos = computed(() => this.secretariaService.cursos().length);
  // prettier-ignore
  readonly totalDisciplinas = computed(() => this.secretariaService.disciplinas().length);
  // prettier-ignore
  readonly totalTurmas = computed(() => this.secretariaService.turmas().length);
  // prettier-ignore
  readonly totalMatriculas = computed(() => this.secretariaService.matriculas().length);

  // prettier-ignore
  ngOnInit(): void {
    this.campusId = this.authService.currentUser()?.campus_id ?? 0;
    if (this.campusId > 0) {
      this.secretariaService.listarCursos(this.campusId).subscribe({ error: () => {} });
      this.secretariaService.listarDisciplinas(undefined, this.campusId).subscribe({ error: () => {} });
      this.secretariaService.listarTurmas(undefined, this.campusId).subscribe({ error: () => {} });
      this.secretariaService.listarMatriculas().subscribe({ error: () => {} });
    }
  }

  // prettier-ignore
  selecionarAba(aba: 'cursos' | 'disciplinas' | 'turmas' | 'matriculas' | 'resumo'): void {
    this.abaAtiva.set(aba); this.mensagemSucesso.set(null); this.secretariaService.limparErro();
  }

  // prettier-ignore
  cadastrarCurso(): void {
    if (this.campusId <= 0 || !this.formCursoNome.trim() || !this.formCursoCodigo.trim()) return;
    this.secretariaService.limparErro(); this.mensagemSucesso.set(null);
    const payload: CursoCreate = { campus_id: this.campusId, nome: this.formCursoNome.trim(), codigo: this.formCursoCodigo.trim().toUpperCase() };
    this.secretariaService.criarCurso(payload).subscribe({
      next: () => { this.mensagemSucesso.set(`Curso ${payload.nome} cadastrado com sucesso.`); this.formCursoNome = ''; this.formCursoCodigo = ''; },
      error: () => {},
    });
  }

  // prettier-ignore
  cadastrarDisciplina(): void {
    if (this.campusId <= 0 || !this.formDiscCursoId || !this.formDiscNome.trim() || !this.formDiscCodigo.trim()) return;
    const carga = Number(this.formDiscCarga);
    this.secretariaService.limparErro(); this.mensagemSucesso.set(null);
    const payload: DisciplinaCreate = { curso_id: this.formDiscCursoId, nome: this.formDiscNome.trim(), codigo: this.formDiscCodigo.trim().toUpperCase(), carga_horaria: Number.isInteger(carga) && carga > 0 ? carga : 60 };
    this.secretariaService.criarDisciplina(payload).subscribe({
      next: () => { this.mensagemSucesso.set(`Disciplina ${payload.nome} cadastrada com sucesso.`); this.formDiscNome = ''; this.formDiscCodigo = ''; this.formDiscCarga = 60; },
      error: () => {},
    });
  }

  // prettier-ignore
  cadastrarTurma(): void {
    if (this.campusId <= 0 || !this.formTurmaDiscId || !this.formTurmaPeriodo.trim()) return;
    let profId: number | null = null;
    if (this.formTurmaProfId !== null && this.formTurmaProfId !== undefined && String(this.formTurmaProfId).trim() !== '') {
      const p = Number(this.formTurmaProfId); if (!Number.isInteger(p) || p <= 0) return; profId = p;
    }
    this.secretariaService.limparErro(); this.mensagemSucesso.set(null);
    const payload: TurmaCreate = { disciplina_id: this.formTurmaDiscId, professor_id: profId, periodo_letivo: this.formTurmaPeriodo.trim(), turno_preferido: this.formTurmaTurno };
    this.secretariaService.criarTurma(payload).subscribe({
      next: (t) => { this.mensagemSucesso.set(`Turma #${t.id} criada com sucesso.`); this.formTurmaDiscId = null; this.formTurmaProfId = null; },
      error: () => {},
    });
  }

  // prettier-ignore
  matricularAluno(): void {
    if (this.campusId <= 0 || !this.formMatTurmaId) return;
    const alunoId = Number(this.formMatAlunoId);
    if (!Number.isInteger(alunoId) || alunoId <= 0) return;
    this.secretariaService.limparErro(); this.mensagemSucesso.set(null);
    const payload: MatriculaCreate = { aluno_id: alunoId, turma_id: this.formMatTurmaId };
    this.secretariaService.matricularAluno(payload).subscribe({
      next: () => { this.mensagemSucesso.set(`Matricula do aluno #${payload.aluno_id} confirmada.`); this.formMatAlunoId = null; },
      error: () => {},
    });
  }
}
