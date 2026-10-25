import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import {
  RelatorioService,
  RelatorioOcupacaoSalaRead,
  RelatorioRemanejamentoRead,
} from './relatorio.service';

describe('RelatorioService', () => {
  let service: RelatorioService;
  let httpMock: HttpTestingController;

  const mockOcupacao: RelatorioOcupacaoSalaRead[] = [
    {
      sala_id: 1,
      campus_id: 1,
      sala: 'A-101',
      bloco: 'A',
      numero: '101',
      tipo: 'laboratorio',
      capacidade: 40,
      quantidade_horarios: 6,
      taxa_ocupacao_semanal: 40.0,
    },
  ];

  const mockRemanejamentos: RelatorioRemanejamentoRead[] = [
    {
      id: 10,
      campus_id: 1,
      horario_id: 5,
      status: 'aprovado',
      sala_origem_id: 1,
      sala_origem: 'A-101',
      sala_origem_capacidade: 50,
      sala_destino_id: 2,
      sala_destino: 'B-202',
      sala_destino_capacidade: 30,
      decisor_id: 1,
      decisor: 'Coordenador Campus 1',
      motivo: 'Alta taxa de absenteismo',
      justificativa: 'Aprovado pela coordenacao',
      criado_em: '2026-10-15T10:00:00Z',
      atualizado_em: '2026-10-16T14:00:00Z',
    },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [RelatorioService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(RelatorioService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('deve inicializar com listas vazias e sinais de carregamento falsos', () => {
    expect(service.ocupacaoSalas()).toEqual([]);
    expect(service.remanejamentos()).toEqual([]);
    expect(service.isLoading()).toBeFalse();
    expect(service.isExporting()).toBeFalse();
    expect(service.errorMessage()).toBeNull();
  });

  it('deve consultar ocupacao de salas com filtros combinados', () => {
    service
      .obterOcupacaoSalas({
        campus_id: 1,
        bloco: 'A',
        tipo: 'laboratorio',
        skip: 0,
        limit: 25,
      })
      .subscribe((res) => {
        expect(res).toEqual(mockOcupacao);
      });

    expect(service.isLoading()).toBeTrue();
    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/relatorios/ocupacao-salas' &&
        r.params.get('campus_id') === '1' &&
        r.params.get('bloco') === 'A' &&
        r.params.get('tipo') === 'laboratorio' &&
        r.params.get('skip') === '0' &&
        r.params.get('limit') === '25',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockOcupacao);

    expect(service.ocupacaoSalas()).toEqual(mockOcupacao);
    expect(service.isLoading()).toBeFalse();
  });

  it('deve consultar remanejamentos com filtros de status e periodo', () => {
    service
      .obterRemanejamentos({
        campus_id: 1,
        status: 'aprovado',
        data_inicio: '2026-10-01',
        data_fim: '2026-10-31',
        skip: 10,
        limit: 50,
      })
      .subscribe((res) => {
        expect(res).toEqual(mockRemanejamentos);
      });

    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/relatorios/remanejamentos' &&
        r.params.get('campus_id') === '1' &&
        r.params.get('status') === 'aprovado' &&
        r.params.get('data_inicio') === '2026-10-01' &&
        r.params.get('data_fim') === '2026-10-31' &&
        r.params.get('skip') === '10' &&
        r.params.get('limit') === '50',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockRemanejamentos);

    expect(service.remanejamentos()).toEqual(mockRemanejamentos);
    expect(service.isLoading()).toBeFalse();
  });

  it('deve exportar CSV de ocupacao de salas mantendo filtros e controlando isExporting', () => {
    const spyCreateUrl = spyOn(window.URL, 'createObjectURL').and.returnValue('blob:mock-url');
    const spyRevokeUrl = spyOn(window.URL, 'revokeObjectURL');
    const csvBlob = new Blob(['sala_id,sala\n1,A-101'], { type: 'text/csv;charset=utf-8' });

    service
      .exportarOcupacaoCsv({ campus_id: 1, bloco: 'A', tipo: 'laboratorio' })
      .subscribe((blob) => {
        expect(blob).toBe(csvBlob);
      });

    expect(service.isExporting()).toBeTrue();
    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/relatorios/ocupacao-salas' &&
        r.params.get('formato') === 'csv' &&
        r.params.get('campus_id') === '1' &&
        r.params.get('bloco') === 'A' &&
        r.params.get('tipo') === 'laboratorio',
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.responseType).toBe('blob');
    req.flush(csvBlob);

    expect(service.isExporting()).toBeFalse();
    expect(spyCreateUrl).toHaveBeenCalledWith(csvBlob);
    expect(spyRevokeUrl).toHaveBeenCalledWith('blob:mock-url');
  });

  it('deve exportar CSV de remanejamentos mantendo filtros e controlando isExporting', () => {
    const spyDownload = spyOn<any>(service, 'dispararDownloadBlob');
    const csvBlob = new Blob(['id,status\n10,aprovado'], { type: 'text/csv;charset=utf-8' });

    service
      .exportarRemanejamentosCsv({
        campus_id: 2,
        status: 'aprovado',
        data_inicio: '2026-10-01',
        data_fim: '2026-10-31',
      })
      .subscribe();

    expect(service.isExporting()).toBeTrue();
    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/relatorios/remanejamentos' &&
        r.params.get('formato') === 'csv' &&
        r.params.get('campus_id') === '2' &&
        r.params.get('status') === 'aprovado' &&
        r.params.get('data_inicio') === '2026-10-01' &&
        r.params.get('data_fim') === '2026-10-31',
    );
    expect(req.request.responseType).toBe('blob');
    req.flush(csvBlob);

    expect(service.isExporting()).toBeFalse();
    expect(spyDownload).toHaveBeenCalledWith(csvBlob, 'remanejamentos.csv');
  });

  it('deve registrar erro HTTP em errorMessage quando a consulta falhar', () => {
    service.obterRemanejamentos().subscribe({
      next: () => fail('Deveria falhar com 422'),
      error: (err) => expect(err.status).toBe(422),
    });

    const req = httpMock.expectOne('/api/v1/relatorios/remanejamentos');
    req.flush(
      { detail: 'data_fim deve ser maior ou igual a data_inicio' },
      { status: 422, statusText: 'Unprocessable Entity' },
    );

    expect(service.errorMessage()).toBe('data_fim deve ser maior ou igual a data_inicio');
    expect(service.isLoading()).toBeFalse();
  });
});
