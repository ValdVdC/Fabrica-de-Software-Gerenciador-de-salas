import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { routes } from '../app.routes';
import { ShellComponent } from '../layout/shell/shell.component';
import { LoginComponent } from './login/login.component';
import { AdminComponent } from './admin/admin.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { RelatoriosComponent } from './relatorios/relatorios.component';
import { HistoricoComponent } from './historico/historico.component';
import { SecretariaComponent } from './secretaria/secretaria.component';
import { ProfessorComponent } from './professor/professor.component';
import { AlunoComponent } from './aluno/aluno.component';
import { GradeHorariaComponent } from './grade-horaria/grade-horaria.component';
import { AuthService, UserRole } from '../services/auth.service';
import { HorarioMeu } from '../services/horario.service';
import { SugestaoRemanejamento } from '../services/ia.service';

// prettier-ignore
describe('Sprint 09 - Integracao E2E (Golden Path), Isolamento de Perfis e Coerencia de Metricas', () => {
  let httpMock: HttpTestingController, auth: AuthService, router: Router;

  const aulaOriginal: HorarioMeu = {
    id: 10, campus_id: 1, turma_id: 5, disciplina_nome: 'Algoritmos I', disciplina_codigo: 'CC101',
    periodo_letivo: '2026.1', turno: 'matutino', dia_semana: 0, hora_inicio: '08:00:00', hora_fim: '10:00:00',
    sala_id: 101, sala_bloco: 'A', sala_numero: '101', sala_tipo: 'regular', professor_id: 2, professor_nome: 'Docente Titular',
  };
  const sugestaoIA: SugestaoRemanejamento = {
    id: 50, horario_id: 10, sala_atual_id: 101, sala_sugerida_id: 202, motivo: 'Absenteismo previsto de 45%',
    justificativa: null, status: 'pendente', aprovado_por: null, criado_em: '2026-10-20T10:00:00Z',
    atualizado_em: '2026-10-20T10:00:00Z', prob_ausencia: 0.45, turma_id: 5, disciplina_codigo: 'CC101',
    disciplina_nome: 'Algoritmos I', sala_atual_bloco: 'A', sala_atual_numero: '101', sala_atual_capacidade: 60,
    sala_sugerida_bloco: 'B', sala_sugerida_numero: '202', sala_sugerida_capacidade: 30,
    dia_semana: 0, hora_inicio: '08:00', hora_fim: '10:00', campus_id: 1,
  };

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [
        LoginComponent, AdminComponent, DashboardComponent, RelatoriosComponent,
        HistoricoComponent, SecretariaComponent, ProfessorComponent, AlunoComponent,
        GradeHorariaComponent, ShellComponent,
      ],
      providers: [provideRouter(routes), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
  });

  afterEach(() => { httpMock.verify(); localStorage.clear(); });

  it('Cenario 3.1 e 3.2: deve executar o Golden Path completo (Login -> Grade -> Alocacao OpenMP -> Notificacao IA -> Aprovacao Humana pela Coordenacao -> Reflexo na Grade Docente/Discente e Dashboard)', () => {
    // 1. Login como Coordenador e redirecionamento para /admin
    const loginComp = TestBed.createComponent(LoginComponent).componentInstance;
    const navSpy = spyOn(router, 'navigate').and.returnValue(Promise.resolve(true));
    loginComp.email = 'coord@sigaas.edu'; loginComp.senha = 'SenhaCoord123';
    loginComp.onSubmit();

    httpMock.expectOne('/api/v1/auth/login').flush({
      access_token: 'jwt_coord_token', token_type: 'bearer',
      usuario: { id: 2, nome: 'Coordenador Campus 1', email: 'coord@sigaas.edu', perfil: 'coordenador', campus_id: 1 },
    });
    expect(auth.isAuthenticated()).toBeTrue();
    expect(navSpy).toHaveBeenCalledWith(['/admin']);

    // 2. Visualizacao inicial da Grade (Docente e Discente na Sala A - 101)
    const profFixture = TestBed.createComponent(ProfessorComponent);
    profFixture.detectChanges();
    httpMock.expectOne('/api/v1/horarios/meus').flush([aulaOriginal]);
    profFixture.detectChanges();
    expect(profFixture.nativeElement.textContent).toContain('A - 101');

    // 3. Alocacao Automatica OpenMP e Coerencia Visual dos Cards de Speedup
    const adminFixture = TestBed.createComponent(AdminComponent);
    const adminComp = adminFixture.componentInstance;
    adminFixture.detectChanges();

    httpMock.expectOne((r) => r.url === '/api/v1/salas').flush([
      { id: 101, campus_id: 1, bloco: 'A', numero: '101', tipo: 'regular', capacidade: 60, turnos_disponiveis: ['matutino'], ativo: true },
      { id: 202, campus_id: 1, bloco: 'B', numero: '202', tipo: 'regular', capacidade: 30, turnos_disponiveis: ['matutino'], ativo: true },
    ]);
    httpMock.expectOne((r) => r.url === '/api/v1/sugestoes').flush([sugestaoIA]);
    httpMock.expectOne('/api/v1/equipamentos').flush([]);
    adminFixture.detectChanges();

    expect(adminFixture.nativeElement.querySelector('[data-testid="remanejamento-badge"]')?.textContent?.trim()).toBe('1');

    adminComp.selecionarAba('alocacao');
    adminFixture.detectChanges();
    expect(adminFixture.nativeElement.querySelector('.empty-msg')?.textContent).toContain('Nenhuma execucao de alocacao');

    adminComp.formSalvarNoBanco = false;
    adminComp.executarAlocacao();
    adminFixture.detectChanges();
    expect(adminFixture.nativeElement.querySelector('.loading-state')?.textContent).toContain('Processando alocacao inteligente');

    httpMock.expectOne('/api/v1/alocacao/otimizar').flush({
      sucesso: true, mensagem: 'Alocacao OpenMP concluida.',
      metricas: { tempo_sequencial_ms: 14.5, tempo_paralelo_ms: 4.2, speedup: 3.45, eficiencia_pct: 86.3, fracao_amdahl: 0.9467, threads: 4, total_turmas: 12, alocadas: 12, conflitos: 0 },
      alocacoes: [{ turma_id: 5, disciplina_codigo: 'CC101', disciplina_nome: 'Algoritmos I', sala_id: 101, sala_bloco: 'A', sala_numero: '101', dia_semana: 0, hora_inicio: '08:00', hora_fim: '10:00', score_desperdicio: 30 }],
    });
    adminFixture.detectChanges();

    const alocText = adminFixture.nativeElement.textContent as string;
    for (const token of ['3.45x', '86.3%', '0.9467', '4.20 ms', 'Sequencial: 14.50 ms', '12/12']) expect(alocText).toContain(token);

    // 4. Notificacao de Remanejamento IA e Coerencia Cruzada na aba Resumo
    adminComp.selecionarAba('remanejamento');
    adminFixture.detectChanges();
    const remText = adminFixture.nativeElement.textContent as string;
    for (const token of ['45%', '+30 vagas', 'A - Sala 101', 'B - Sala 202', 'pendente']) expect(remText).toContain(token);

    adminComp.selecionarAba('resumo');
    adminFixture.detectChanges();
    const resumoText = adminFixture.nativeElement.textContent as string;
    for (const token of ['3.45x', '12/12 turmas alocadas', 'Risco medio: 45%', '+30']) expect(resumoText).toContain(token);

    // 5. Aprovacao Humana pela Coordenacao (Human-in-the-Loop) e atualizacao de badges sem cache stale
    adminComp.selecionarAba('remanejamento');
    adminComp.justificativas[50] = 'Homologado pela coordenacao';
    adminComp.aprovarSugestao(sugestaoIA);

    const reqPatch = httpMock.expectOne('/api/v1/sugestoes/50');
    expect(reqPatch.request.body).toEqual({ status: 'aprovado', justificativa: 'Homologado pela coordenacao' });
    reqPatch.flush({ ...sugestaoIA, status: 'aprovado', justificativa: 'Homologado pela coordenacao', aprovado_por: 2 });
    adminFixture.detectChanges();

    expect(adminComp.sugestoesPendentesCount()).toBe(0);
    expect(adminFixture.nativeElement.querySelector('[data-testid="remanejamento-badge"]')).toBeNull();
    expect(adminFixture.nativeElement.querySelector('.card-aprovado')).not.toBeNull();
    expect(adminFixture.nativeElement.textContent).toContain('Sugestao #50 aprovada com sucesso.');

    // 6. Reflexo da troca na Grade do Docente, do Discente e nos indicadores do Dashboard
    const aulaRemanejada: HorarioMeu = { ...aulaOriginal, sala_id: 202, sala_bloco: 'B', sala_numero: '202' };
    const alunoFixture = TestBed.createComponent(AlunoComponent);
    alunoFixture.detectChanges();
    httpMock.expectOne('/api/v1/horarios/meus').flush([aulaRemanejada]);
    httpMock.expectOne('/api/v1/matriculas').flush([{ id: 1, aluno_id: 10, turma_id: 5, data_matricula: '2026-09-01', status: 'ativa' }]);
    alunoFixture.detectChanges();
    expect(alunoFixture.nativeElement.textContent).toContain('B - 202');
    expect(alunoFixture.nativeElement.textContent).not.toContain('A - 101');

    const dashFixture = TestBed.createComponent(DashboardComponent);
    dashFixture.detectChanges();
    httpMock.expectOne('/api/v1/dashboard/resumo').flush({
      salas_ativas: 2, turmas: 12, horarios: 12,
      sugestoes: { pendente: 0, aprovado: 1, rejeitado: 0, total: 1 },
      vagas_recuperadas: 30, eventos_recentes: [],
    });
    httpMock.expectOne('/api/v1/dashboard/ocupacao').flush({ por_dia_semana: [{ dia_semana: 0, total_horarios: 1 }], por_turno: [{ turno: 'matutino', total_horarios: 1 }] });
    dashFixture.detectChanges();
    for (const token of ['Pendentes: 0', 'Aprovadas: 1', '30']) expect(dashFixture.nativeElement.textContent).toContain(token);
  });

  it('deve validar navegacao isolada, bloqueio de rotas, redirecionamento e banner de acesso restrito para os 5 perfis', async () => {
    const shellFixture = TestBed.createComponent(ShellComponent);
    const matrizPerfis: Array<{ role: UserRole; permitidas: string[]; bloqueadas: string[]; home: string }> = [
      { role: 'admin', permitidas: ['/admin', '/dashboard', '/relatorios', '/historico'], bloqueadas: ['/professor', '/aluno'], home: '/admin' },
      { role: 'coordenador', permitidas: ['/admin', '/dashboard', '/relatorios', '/historico'], bloqueadas: ['/secretaria', '/professor', '/aluno'], home: '/admin' },
      { role: 'secretaria', permitidas: ['/secretaria', '/dashboard', '/relatorios'], bloqueadas: ['/admin', '/historico', '/professor', '/aluno'], home: '/secretaria' },
      { role: 'professor', permitidas: ['/professor'], bloqueadas: ['/admin', '/secretaria', '/dashboard', '/relatorios', '/historico', '/aluno'], home: '/professor' },
      { role: 'aluno', permitidas: ['/aluno'], bloqueadas: ['/admin', '/secretaria', '/dashboard', '/relatorios', '/historico', '/professor'], home: '/aluno' },
    ];

    for (const c of matrizPerfis) {
      auth.setRole(c.role);
      for (const rotaOk of c.permitidas) {
        auth.clearAccessDenied();
        await router.navigateByUrl(rotaOk);
        expect(router.url).toBe(rotaOk);
        expect(auth.accessDeniedMessage()).toBeNull();
        httpMock.match(() => true).forEach((req) => req.flush([]));
      }
      for (const rotaNegada of c.bloqueadas) {
        auth.clearAccessDenied();
        await router.navigateByUrl(rotaNegada);
        shellFixture.detectChanges();
        expect(router.url).toBe(c.home);
        expect(shellFixture.nativeElement.querySelector('[data-testid="access-denied-banner"]')?.textContent).toContain('Acesso restrito');
        httpMock.match(() => true).forEach((req) => req.flush([]));
      }
    }
  });

  it('deve validar estados vazios (empty states) e feedback visual de loading/erro em todas as abas do sistema', () => {
    auth.login({ email: 'admin@sigaas.edu', senha: '123' }).subscribe();
    httpMock.expectOne('/api/v1/auth/login').flush({
      access_token: 'tok', token_type: 'bearer',
      usuario: { id: 1, nome: 'Admin', email: 'admin@sigaas.edu', perfil: 'admin', campus_id: 1 },
    });

    // Admin (salas, equipamentos, alocacao, remanejamento)
    const adminFixture = TestBed.createComponent(AdminComponent);
    const adminComp = adminFixture.componentInstance;
    adminFixture.detectChanges();
    httpMock.expectOne((r) => r.url === '/api/v1/salas').flush([]);
    httpMock.expectOne((r) => r.url === '/api/v1/sugestoes').flush([]);
    httpMock.expectOne('/api/v1/equipamentos').flush([]);
    adminFixture.detectChanges();
    expect(adminFixture.nativeElement.querySelector('.empty-msg')?.textContent).toContain('Nenhuma sala cadastrada');

    adminComp.selecionarAba('equipamentos');
    adminFixture.detectChanges();
    expect(adminFixture.nativeElement.querySelector('.empty-msg')?.textContent).toContain('Nenhum equipamento cadastrado');

    adminComp.selecionarAba('alocacao');
    adminFixture.detectChanges();
    expect(adminFixture.nativeElement.querySelector('.empty-msg')?.textContent).toContain('Nenhuma execucao de alocacao');
    adminComp.executarAlocacao();
    httpMock.expectOne('/api/v1/alocacao/otimizar').flush({ detail: 'Falha no motor OpenMP' }, { status: 500, statusText: 'Error' });
    adminFixture.detectChanges();
    expect(adminFixture.nativeElement.querySelector('.alert-error')?.textContent).toContain('Falha no motor OpenMP');

    adminComp.selecionarAba('remanejamento');
    httpMock.expectOne((r) => r.url === '/api/v1/sugestoes').flush([]);
    adminFixture.detectChanges();
    expect(adminFixture.nativeElement.querySelector('.empty-title')?.textContent).toContain('Nenhuma sugestao de remanejamento');

    // Secretaria (cursos, disciplinas, turmas, matriculas)
    const secFixture = TestBed.createComponent(SecretariaComponent);
    const secComp = secFixture.componentInstance;
    secFixture.detectChanges();
    for (const url of ['/api/v1/cursos', '/api/v1/disciplinas', '/api/v1/turmas', '/api/v1/matriculas']) {
      httpMock.expectOne((r) => r.url === url).flush([]);
    }
    for (const [aba, msg] of [
      ['cursos', 'Nenhum curso cadastrado'],
      ['disciplinas', 'Nenhuma disciplina cadastrada'],
      ['turmas', 'Nenhuma turma cadastrada'],
      ['matriculas', 'Nenhuma matricula registrada'],
    ] as const) {
      secComp.selecionarAba(aba);
      secFixture.detectChanges();
      expect(secFixture.nativeElement.querySelector('.empty-msg')?.textContent).toContain(msg);
    }

    // Relatorios (ocupacao e remanejamentos) e Historico
    const relFixture = TestBed.createComponent(RelatoriosComponent);
    relFixture.detectChanges();
    expect(relFixture.nativeElement.querySelector('.empty-msg')?.textContent).toContain('Carregando relatorio de ocupacao');
    httpMock.expectOne((r) => r.url === '/api/v1/relatorios/ocupacao-salas').flush([]);
    relFixture.detectChanges();
    expect(relFixture.nativeElement.querySelector('.empty-msg')?.textContent).toContain('Nenhum registro encontrado');

    relFixture.componentInstance.selecionarAba('remanejamentos');
    httpMock.expectOne((r) => r.url === '/api/v1/relatorios/remanejamentos').flush([]);
    relFixture.detectChanges();
    expect(relFixture.nativeElement.querySelector('.empty-msg')?.textContent).toContain('Nenhum remanejamento encontrado');

    const histFixture = TestBed.createComponent(HistoricoComponent);
    histFixture.detectChanges();
    httpMock.expectOne((r) => r.url === '/api/v1/logs').flush([]);
    histFixture.detectChanges();
    expect(histFixture.nativeElement.querySelector('.empty-msg')?.textContent).toContain('Nenhum evento registrado');
  });
});
