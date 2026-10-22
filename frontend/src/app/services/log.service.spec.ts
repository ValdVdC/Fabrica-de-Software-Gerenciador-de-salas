import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { LogService, LogRead } from './log.service';

describe('LogService', () => {
  let service: LogService;
  let httpMock: HttpTestingController;

  const mockLogs: LogRead[] = [
    {
      id: 101,
      campus_id: 1,
      horario_id: 10,
      snapshot_evento: { entidade: 'sala', id: 5 },
      tipo_evento: 'remanejamento',
      usuario_responsavel: 3,
      detalhes: 'Remanejamento aprovado da sala A-101 para B-202',
      timestamp: '2026-10-20T14:30:00Z',
    },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [LogService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(LogService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('deve inicializar com lista vazia e sinais de carregamento falsos', () => {
    expect(service.logs()).toEqual([]);
    expect(service.isLoading()).toBeFalse();
    expect(service.isExporting()).toBeFalse();
    expect(service.errorMessage()).toBeNull();
  });

  it('deve listar logs com filtros combinados via GET /api/v1/logs', () => {
    service
      .listarLogs({
        campus_id: 1,
        tipo_evento: 'remanejamento',
        usuario_id: 3,
        horario_id: 10,
        data_inicio: '2026-10-01',
        data_fim: '2026-10-31',
        skip: 0,
        limit: 50,
      })
      .subscribe((res) => {
        expect(res).toEqual(mockLogs);
      });

    expect(service.isLoading()).toBeTrue();
    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/logs' &&
        r.params.get('campus_id') === '1' &&
        r.params.get('tipo_evento') === 'remanejamento' &&
        r.params.get('usuario_id') === '3' &&
        r.params.get('horario_id') === '10' &&
        r.params.get('data_inicio') === '2026-10-01' &&
        r.params.get('data_fim') === '2026-10-31' &&
        r.params.get('skip') === '0' &&
        r.params.get('limit') === '50',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockLogs);

    expect(service.logs()).toEqual(mockLogs);
    expect(service.isLoading()).toBeFalse();
  });

  it('deve exportar CSV de logs mantendo filtros ativos e controlando isExporting', () => {
    const spyCreateUrl = spyOn(window.URL, 'createObjectURL').and.returnValue('blob:logs-csv');
    const spyRevokeUrl = spyOn(window.URL, 'revokeObjectURL');
    const csvBlob = new Blob(['id,tipo_evento\n101,remanejamento'], {
      type: 'text/csv;charset=utf-8',
    });

    service
      .exportarLogsCsv({
        campus_id: 1,
        tipo_evento: 'remanejamento',
        usuario_id: 3,
      })
      .subscribe((blob) => {
        expect(blob).toBe(csvBlob);
      });

    expect(service.isExporting()).toBeTrue();
    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/logs' &&
        r.params.get('formato') === 'csv' &&
        r.params.get('campus_id') === '1' &&
        r.params.get('tipo_evento') === 'remanejamento' &&
        r.params.get('usuario_id') === '3',
    );
    expect(req.request.responseType).toBe('blob');
    req.flush(csvBlob);

    expect(service.isExporting()).toBeFalse();
    expect(spyCreateUrl).toHaveBeenCalledWith(csvBlob);
    expect(spyRevokeUrl).toHaveBeenCalledWith('blob:logs-csv');
  });

  it('deve capturar erro HTTP 422 e registrar em errorMessage', () => {
    service.listarLogs().subscribe({
      next: () => fail('Deveria falhar com 422'),
      error: (err) => expect(err.status).toBe(422),
    });

    const req = httpMock.expectOne('/api/v1/logs');
    req.flush(
      { detail: 'data_fim deve ser maior ou igual a data_inicio' },
      { status: 422, statusText: 'Unprocessable Entity' },
    );

    expect(service.errorMessage()).toBe('data_fim deve ser maior ou igual a data_inicio');
    expect(service.isLoading()).toBeFalse();
  });
});
