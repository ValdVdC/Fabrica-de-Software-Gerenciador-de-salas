import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import {
  provideRouter,
  Router,
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
} from '@angular/router';
import { DashboardComponent } from './dashboard.component';
import {
  DashboardService,
  DashboardResumoRead,
  DashboardOcupacaoRead,
} from '../../services/dashboard.service';
import { AuthService } from '../../services/auth.service';
import { ShellComponent } from '../../layout/shell/shell.component';
import { roleGuard } from '../../guards/role.guard';
import { routes } from '../../app.routes';

describe('DashboardComponent & Roteamento', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let httpMock: HttpTestingController;
  let authService: AuthService;
  let router: Router;

  const mockResumo: DashboardResumoRead = {
    salas_ativas: 14,
    turmas: 28,
    horarios: 56,
    sugestoes: {
      pendente: 3,
      aprovado: 7,
      rejeitado: 1,
      total: 11,
    },
    vagas_recuperadas: 95,
    eventos_recentes: [
      {
        id: 501,
        campus_id: 1,
        horario_id: 22,
        snapshot_evento: { entidade: 'horario' },
        tipo_evento: 'remanejamento',
        usuario_responsavel: 4,
        detalhes: 'Aprovacao de remanejamento para sala 102',
        timestamp: '2026-10-20T12:00:00Z',
      },
    ],
  };

  const mockOcupacao: DashboardOcupacaoRead = {
    por_dia_semana: [
      { dia_semana: 0, total_horarios: 12 },
      { dia_semana: 1, total_horarios: 16 },
      { dia_semana: 2, total_horarios: 10 },
      { dia_semana: 3, total_horarios: 8 },
      { dia_semana: 4, total_horarios: 6 },
      { dia_semana: 5, total_horarios: 4 },
      { dia_semana: 6, total_horarios: 0 },
    ],
    por_turno: [
      { turno: 'matutino', total_horarios: 20 },
      { turno: 'vespertino', total_horarios: 16 },
      { turno: 'noturno', total_horarios: 15 },
      { turno: 'integral', total_horarios: 5 },
    ],
  };

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [DashboardComponent, ShellComponent],
      providers: [
        DashboardService,
        AuthService,
        provideRouter(routes),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    authService = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  function flushDashboardData(
    resumo: DashboardResumoRead = mockResumo,
    ocupacao: DashboardOcupacaoRead = mockOcupacao,
  ): void {
    const reqResumo = httpMock.expectOne((r) => r.url === '/api/v1/dashboard/resumo');
    reqResumo.flush(resumo);
    const reqOcupacao = httpMock.expectOne((r) => r.url === '/api/v1/dashboard/ocupacao');
    reqOcupacao.flush(ocupacao);
    fixture.detectChanges();
  }

  it('deve renderizar indicadores consolidados e contagens de sugestoes por status', () => {
    authService.setRole('coordenador');
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    flushDashboardData();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('14');
    expect(text).toContain('28');
    expect(text).toContain('56');
    expect(text).toContain('95');
    expect(text).toContain('3');
    expect(text).toContain('7');
    expect(text).toContain('1');
    expect(text).toContain('11');
  });

  it('deve mapear estritamente o padrao ISO 8601 (0=Segunda-feira ate 6=Domingo) e os 4 turnos nos graficos SVG', () => {
    authService.setRole('secretaria');
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    flushDashboardData();

    const labelsDia = component.obterItensGraficoDia();
    expect(labelsDia.length).toBe(7);
    expect(labelsDia[0].rotulo).toBe('Segunda-feira');
    expect(labelsDia[0].total).toBe(12);
    expect(labelsDia[1].rotulo).toBe('Terca-feira');
    expect(labelsDia[5].rotulo).toBe('Sabado');
    expect(labelsDia[6].rotulo).toBe('Domingo');
    expect(labelsDia[6].percentual).toBe(0);

    const svgs = fixture.nativeElement.querySelectorAll('svg.bar-svg');
    expect(svgs.length).toBeGreaterThanOrEqual(11);
  });

  it('deve exibir seletor de filtro por campus apenas para perfil admin e recarregar dados', () => {
    authService.setRole('coordenador');
    fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    flushDashboardData();
    expect(fixture.nativeElement.querySelector('#filtro-campus')).toBeNull();

    authService.setRole('admin');
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    flushDashboardData();

    const selectEl = fixture.nativeElement.querySelector('#filtro-campus');
    expect(selectEl).not.toBeNull();

    component.selecionarCampus(2);
    const reqResumo = httpMock.expectOne(
      (r) => r.url === '/api/v1/dashboard/resumo' && r.params.get('campus_id') === '2',
    );
    reqResumo.flush(mockResumo);
    const reqOcup = httpMock.expectOne(
      (r) => r.url === '/api/v1/dashboard/ocupacao' && r.params.get('campus_id') === '2',
    );
    reqOcup.flush(mockOcupacao);
  });

  it('deve exibir estado vazio quando nao houver horarios alocados ou eventos recentes', () => {
    authService.setRole('admin');
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    flushDashboardData(
      {
        ...mockResumo,
        horarios: 0,
        eventos_recentes: [],
      },
      {
        por_dia_semana: [0, 1, 2, 3, 4, 5, 6].map((d) => ({ dia_semana: d, total_horarios: 0 })),
        por_turno: ['matutino', 'vespertino', 'noturno', 'integral'].map((t) => ({
          turno: t,
          total_horarios: 0,
        })),
      },
    );

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Nenhum evento de auditoria registrado no escopo selecionado.');
    expect(component.obterItensGraficoDia().every((i) => i.percentual === 0)).toBeTrue();
  });

  it('deve exibir alerta de erro quando a API retornar falha HTTP', () => {
    authService.setRole('admin');
    fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();

    const reqResumo = httpMock.expectOne('/api/v1/dashboard/resumo');
    reqResumo.flush(
      { detail: 'Falha ao consultar indicadores' },
      { status: 500, statusText: 'Internal Server Error' },
    );
    const reqOcupacao = httpMock.expectOne('/api/v1/dashboard/ocupacao');
    reqOcupacao.flush(mockOcupacao);
    fixture.detectChanges();

    const alertEl = fixture.nativeElement.querySelector('.alert-error');
    expect(alertEl).not.toBeNull();
    expect(alertEl.textContent).toContain('Falha ao consultar indicadores');
  });

  it('deve permitir acesso a rota /dashboard para admin, coordenador e secretaria e bloquear professor e aluno', () => {
    const dashboardRoute = routes
      .find((r) => r.path === '')
      ?.children?.find((c) => c.path === 'dashboard');
    expect(dashboardRoute).toBeDefined();

    const routeSnap = { data: dashboardRoute?.data ?? {} } as unknown as ActivatedRouteSnapshot;
    const stateSnap = { url: '/dashboard' } as RouterStateSnapshot;

    for (const allowedRole of ['admin', 'coordenador', 'secretaria'] as const) {
      authService.setRole(allowedRole);
      const res = TestBed.runInInjectionContext(() => roleGuard(routeSnap, stateSnap));
      expect(res).toBeTrue();
    }

    authService.setRole('professor');
    const resProf = TestBed.runInInjectionContext(() => roleGuard(routeSnap, stateSnap));
    expect(resProf).toEqual(router.createUrlTree(['/professor']));

    authService.setRole('aluno');
    const resAluno = TestBed.runInInjectionContext(() => roleGuard(routeSnap, stateSnap));
    expect(resAluno).toEqual(router.createUrlTree(['/aluno']));
  });

  it('deve exibir link Dashboard no ShellComponent apenas para admin, coordenador e secretaria', () => {
    const shellFixture = TestBed.createComponent(ShellComponent);

    for (const role of ['admin', 'coordenador', 'secretaria'] as const) {
      authService.setRole(role);
      shellFixture.detectChanges();
      const navText = shellFixture.nativeElement.querySelector('.header-nav')?.textContent ?? '';
      expect(navText).toContain('Dashboard');
    }

    for (const role of ['professor', 'aluno'] as const) {
      authService.setRole(role);
      shellFixture.detectChanges();
      const navText = shellFixture.nativeElement.querySelector('.header-nav')?.textContent ?? '';
      expect(navText).not.toContain('Dashboard');
    }
  });
});
