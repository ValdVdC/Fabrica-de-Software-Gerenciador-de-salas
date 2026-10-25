import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { DashboardService, DashboardResumoRead, DashboardOcupacaoRead } from './dashboard.service';

describe('DashboardService', () => {
  let service: DashboardService;
  let httpMock: HttpTestingController;

  const mockResumo: DashboardResumoRead = {
    salas_ativas: 12,
    turmas: 34,
    horarios: 68,
    sugestoes: {
      pendente: 4,
      aprovado: 9,
      rejeitado: 2,
      total: 15,
    },
    vagas_recuperadas: 120,
    eventos_recentes: [
      {
        id: 101,
        campus_id: 1,
        horario_id: 10,
        snapshot_evento: { entidade: 'sala', id: 5 },
        tipo_evento: 'remanejamento',
        usuario_responsavel: 1,
        detalhes: 'Remanejamento aprovado da sala 101 para 202',
        timestamp: '2026-10-20T14:30:00Z',
      },
    ],
  };

  const mockOcupacao: DashboardOcupacaoRead = {
    por_dia_semana: [
      { dia_semana: 0, total_horarios: 15 },
      { dia_semana: 1, total_horarios: 18 },
      { dia_semana: 2, total_horarios: 14 },
      { dia_semana: 3, total_horarios: 12 },
      { dia_semana: 4, total_horarios: 9 },
      { dia_semana: 5, total_horarios: 0 },
      { dia_semana: 6, total_horarios: 0 },
    ],
    por_turno: [
      { turno: 'matutino', total_horarios: 25 },
      { turno: 'vespertino', total_horarios: 18 },
      { turno: 'noturno', total_horarios: 20 },
      { turno: 'integral', total_horarios: 5 },
    ],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [DashboardService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(DashboardService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('deve inicializar com signals nulos e isLoading falso', () => {
    expect(service.resumo()).toBeNull();
    expect(service.ocupacao()).toBeNull();
    expect(service.isLoading()).toBeFalse();
    expect(service.errorMessage()).toBeNull();
  });

  it('deve buscar resumo via GET /api/v1/dashboard/resumo sem parametro quando campusId for omitido', () => {
    service.obterResumo().subscribe((res) => {
      expect(res).toEqual(mockResumo);
    });

    expect(service.isLoading()).toBeTrue();
    const req = httpMock.expectOne('/api/v1/dashboard/resumo');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush(mockResumo);

    expect(service.resumo()).toEqual(mockResumo);
    expect(service.isLoading()).toBeFalse();
    expect(service.errorMessage()).toBeNull();
  });

  it('deve buscar resumo via GET /api/v1/dashboard/resumo?campus_id=2 quando campusId for informado', () => {
    service.obterResumo(2).subscribe((res) => {
      expect(res.salas_ativas).toBe(12);
    });

    const req = httpMock.expectOne(
      (r) => r.url === '/api/v1/dashboard/resumo' && r.params.get('campus_id') === '2',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockResumo);

    expect(service.resumo()?.vagas_recuperadas).toBe(120);
    expect(service.isLoading()).toBeFalse();
  });

  it('deve ignorar campusId invalido (<= 0 ou null) na chamada de resumo', () => {
    service.obterResumo(0).subscribe();
    const req = httpMock.expectOne('/api/v1/dashboard/resumo');
    expect(req.request.params.has('campus_id')).toBeFalse();
    req.flush(mockResumo);
  });

  it('deve buscar ocupacao via GET /api/v1/dashboard/ocupacao com e sem campus_id', () => {
    service.obterOcupacao(3).subscribe((res) => {
      expect(res.por_dia_semana.length).toBe(7);
      expect(res.por_turno.length).toBe(4);
    });

    const req = httpMock.expectOne(
      (r) => r.url === '/api/v1/dashboard/ocupacao' && r.params.get('campus_id') === '3',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockOcupacao);

    expect(service.ocupacao()).toEqual(mockOcupacao);
    expect(service.isLoading()).toBeFalse();
  });

  it('deve capturar erro HTTP em obterResumo e popular errorMessage', () => {
    service.obterResumo().subscribe({
      next: () => fail('Deveria ter falhado com 403'),
      error: (err) => expect(err.status).toBe(403),
    });

    const req = httpMock.expectOne('/api/v1/dashboard/resumo');
    req.flush(
      { detail: 'Acesso negado para este perfil' },
      { status: 403, statusText: 'Forbidden' },
    );

    expect(service.errorMessage()).toBe('Acesso negado para este perfil');
    expect(service.isLoading()).toBeFalse();
  });

  it('deve capturar erro HTTP em obterOcupacao com mensagem padrao quando detail nao for string', () => {
    service.obterOcupacao().subscribe({
      next: () => fail('Deveria ter falhado com 500'),
      error: (err) => expect(err.status).toBe(500),
    });

    const req = httpMock.expectOne('/api/v1/dashboard/ocupacao');
    req.flush({}, { status: 500, statusText: 'Server Error' });

    expect(service.errorMessage()).toBe('Erro ao carregar indicadores de ocupacao do dashboard.');
    expect(service.isLoading()).toBeFalse();
  });

  it('deve limpar mensagem de erro ao invocar limparErro()', () => {
    service.obterResumo().subscribe({ error: () => {} });
    const req = httpMock.expectOne('/api/v1/dashboard/resumo');
    req.flush({ detail: 'Erro temporario' }, { status: 500, statusText: 'Error' });
    expect(service.errorMessage()).toBe('Erro temporario');

    service.limparErro();
    expect(service.errorMessage()).toBeNull();
  });
});
