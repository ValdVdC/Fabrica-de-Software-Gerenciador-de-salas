import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AdminService, Sala, Equipamento, SalaCreate } from './admin.service';

describe('AdminService', () => {
  let service: AdminService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AdminService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('lista salas com e sem campusId via HttpParams', () => {
    const mockSalas: Sala[] = [
      {
        id: 1,
        campus_id: 1,
        bloco: 'A',
        numero: '101',
        tipo: 'regular',
        capacidade: 40,
        turnos_disponiveis: ['matutino'],
        ativo: true,
      },
    ];

    service.listarSalas().subscribe((res) => expect(res.length).toBe(1));
    httpMock.expectOne('/api/v1/salas').flush(mockSalas);
    expect(service.salas().length).toBe(1);

    service.listarSalas(1).subscribe((res) => expect(res.length).toBe(1));
    const req = httpMock.expectOne(
      (r) => r.url === '/api/v1/salas' && r.params.get('campus_id') === '1',
    );
    req.flush(mockSalas);
  });

  it('rejeita campusId e salaId invalidos com excecao', () => {
    expect(() => service.listarSalas(0)).toThrowError('Identificador de campus invalido');
    expect(() => service.listarSalas(-5)).toThrowError('Identificador de campus invalido');
    expect(() => service.associarEquipamento(0, { equipamento_id: 1, quantidade: 1 })).toThrowError(
      'Identificador de sala invalido',
    );
  });

  it('cria sala e equipamento com sucesso', () => {
    const payloadSala: SalaCreate = {
      campus_id: 1,
      bloco: 'B',
      numero: '202',
      tipo: 'laboratorio',
      capacidade: 30,
      turnos_disponiveis: ['vespertino'],
    };
    service.criarSala(payloadSala).subscribe((res) => expect(res.id).toBe(2));
    httpMock
      .expectOne('/api/v1/salas')
      .flush({ id: 2, ...payloadSala, tipo: 'laboratorio', ativo: true });
    expect(service.salas().some((s) => s.id === 2)).toBeTrue();

    service
      .criarEquipamento({ nome: 'Caixa de Som' })
      .subscribe((res) => expect(res.nome).toBe('Caixa de Som'));
    httpMock
      .expectOne('/api/v1/equipamentos')
      .flush({ id: 2, nome: 'Caixa de Som', created_at: '2026-09-08' });
    expect(service.equipamentos().some((e) => e.id === 2)).toBeTrue();
  });

  it('associa equipamento a sala com quantidade', () => {
    service
      .associarEquipamento(1, { equipamento_id: 1, quantidade: 2 })
      .subscribe((res) => expect(res.quantidade).toBe(2));
    httpMock
      .expectOne('/api/v1/salas/1/equipamentos')
      .flush({ sala_id: 1, equipamento_id: 1, quantidade: 2 });
  });

  it('nao vaza informacoes internas de servidor em erros HTTP 500', () => {
    service.listarSalas().subscribe({
      error: () => {
        expect(service.errorMessage()).toBe(
          'Erro interno no servidor. Tente novamente mais tarde.',
        );
      },
    });
    httpMock
      .expectOne('/api/v1/salas')
      .flush(
        { detail: 'psycopg2.OperationalError: stacktrace' },
        { status: 500, statusText: 'Server Error' },
      );
    expect(service.isLoading()).toBeFalse();
  });

  it('trata erros de validacao 422 e objetos sem vazar metadados brutos', () => {
    service.criarEquipamento({ nome: 'A' }).subscribe({
      error: () => expect(service.errorMessage()).toBe('Nome muito curto'),
    });
    httpMock
      .expectOne('/api/v1/equipamentos')
      .flush(
        { detail: [null, { msg: 'Nome muito curto' }] },
        { status: 422, statusText: 'Unprocessable' },
      );

    service.criarEquipamento({ nome: 'B' }).subscribe({
      error: () => expect(service.errorMessage()).toBe('Recurso bloqueado'),
    });
    httpMock
      .expectOne('/api/v1/equipamentos')
      .flush({ detail: { message: 'Recurso bloqueado' } }, { status: 409, statusText: 'Conflict' });
  });

  it('gerencia isLoading de forma resiliente contra race conditions em chamadas paralelas', () => {
    service.listarSalas().subscribe();
    service.listarEquipamentos().subscribe();

    expect(service.isLoading()).toBeTrue();
    httpMock.expectOne('/api/v1/salas').flush([]);
    expect(service.isLoading()).toBeTrue();

    httpMock.expectOne('/api/v1/equipamentos').flush([]);
    expect(service.isLoading()).toBeFalse();
  });

  it('expoe signals como somente leitura e reseta estado com resetState', () => {
    expect((service.salas as any).set).toBeUndefined();
    expect((service.equipamentos as any).set).toBeUndefined();

    service.resetState();
    expect(service.salas()).toEqual([]);
    expect(service.equipamentos()).toEqual([]);
    expect(service.errorMessage()).toBeNull();
  });
});
