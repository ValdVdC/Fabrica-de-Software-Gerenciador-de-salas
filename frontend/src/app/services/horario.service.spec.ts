import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { HorarioService, HorarioMeu } from './horario.service';

describe('HorarioService', () => {
  let service: HorarioService;
  let httpMock: HttpTestingController;

  const mockHorarios: HorarioMeu[] = [
    {
      id: 1,
      campus_id: 1,
      turma_id: 10,
      disciplina_nome: 'Algoritmos e Estruturas de Dados',
      disciplina_codigo: 'AED1',
      periodo_letivo: '2026.1',
      turno: 'matutino',
      dia_semana: 0,
      hora_inicio: '10:00:00',
      hora_fim: '12:00:00',
      sala_id: 101,
      sala_bloco: 'Bloco 1',
      sala_numero: '101',
      sala_tipo: 'regular',
      professor_id: 2,
      professor_nome: 'Prof Alan Turing',
    },
    {
      id: 2,
      campus_id: 1,
      turma_id: 10,
      disciplina_nome: 'Algoritmos e Estruturas de Dados',
      disciplina_codigo: 'AED1',
      periodo_letivo: '2026.1',
      turno: 'matutino',
      dia_semana: 0,
      hora_inicio: '08:00:00',
      hora_fim: '10:00:00',
      sala_id: 101,
      sala_bloco: 'Bloco 1',
      sala_numero: '101',
      sala_tipo: 'regular',
      professor_id: 2,
      professor_nome: 'Prof Alan Turing',
    },
    {
      id: 3,
      campus_id: 1,
      turma_id: 11,
      disciplina_nome: 'Calculo Diferencial',
      disciplina_codigo: 'MAT1',
      periodo_letivo: '2026.1',
      turno: 'matutino',
      dia_semana: 2,
      hora_inicio: '08:00:00',
      hora_fim: '10:00:00',
      sala_id: 102,
      sala_bloco: 'Bloco 2',
      sala_numero: '202',
      sala_tipo: 'laboratorio',
      professor_id: 3,
      professor_nome: 'Prof Ada Lovelace',
    },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [HorarioService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(HorarioService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('inicializa com estado limpo e computeds zerados', () => {
    expect(service.horarios()).toEqual([]);
    expect(service.isLoading()).toBeFalse();
    expect(service.errorMessage()).toBeNull();
    expect(service.totalAulas()).toBe(0);
    expect(service.disciplinasDistintas()).toEqual([]);
  });

  it('carrega horarios com sucesso e atualiza signals e computeds reativos', () => {
    service.carregarMeusHorarios().subscribe((dados) => {
      expect(dados.length).toBe(3);
    });

    const req = httpMock.expectOne('/api/v1/horarios/meus');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush(mockHorarios);

    expect(service.horarios().length).toBe(3);
    expect(service.totalAulas()).toBe(3);
    expect(service.disciplinasDistintas()).toEqual(['AED1', 'MAT1']);
    expect(service.errorMessage()).toBeNull();
  });

  it('repassa parametros sanitizados de paginacao skip e limit', () => {
    service.carregarMeusHorarios(10, 50).subscribe();

    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/horarios/meus' &&
        r.params.get('skip') === '10' &&
        r.params.get('limit') === '50',
    );
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('valida defensivamente parametros invalidos de paginacao antes do disparo HTTP', () => {
    expect(() => service.carregarMeusHorarios(-1)).toThrowError('Parametro skip invalido');
    expect(() => service.carregarMeusHorarios(0, 0)).toThrowError('Parametro limit invalido');
    expect(() => service.carregarMeusHorarios(0, 201)).toThrowError('Parametro limit invalido');
    expect(() => service.carregarMeusHorarios(1.5 as any)).toThrowError('Parametro skip invalido');
  });

  it('filtra e ordena horarios do dia cronologicamente', () => {
    service.carregarMeusHorarios().subscribe();
    httpMock.expectOne('/api/v1/horarios/meus').flush(mockHorarios);

    const horariosSegunda = service.obterHorariosDoDia(0);
    expect(horariosSegunda.length).toBe(2);
    expect(horariosSegunda[0].hora_inicio).toBe('08:00:00');
    expect(horariosSegunda[1].hora_inicio).toBe('10:00:00');

    const horariosQuarta = service.obterHorariosDoDia(2);
    expect(horariosQuarta.length).toBe(1);
    expect(horariosQuarta[0].disciplina_codigo).toBe('MAT1');

    const horariosSexta = service.obterHorariosDoDia(4);
    expect(horariosSexta.length).toBe(0);

    expect(() => service.obterHorariosDoDia(-1)).toThrowError('Dia da semana invalido');
    expect(() => service.obterHorariosDoDia(7)).toThrowError('Dia da semana invalido');
  });

  it('gerencia ciclo de vida atomico de isLoading via defer apenas na subscricao', () => {
    const obs$ = service.carregarMeusHorarios();
    expect(service.isLoading()).toBeFalse();

    obs$.subscribe();
    expect(service.isLoading()).toBeTrue();

    httpMock.expectOne('/api/v1/horarios/meus').flush([]);
    expect(service.isLoading()).toBeFalse();
  });

  it('captura erro 401 e atualiza errorMessage', () => {
    service.carregarMeusHorarios().subscribe({ error: () => {} });
    httpMock
      .expectOne('/api/v1/horarios/meus')
      .flush({ detail: 'Token invalido' }, { status: 401, statusText: 'Unauthorized' });

    expect(service.errorMessage()).toBe('Sessao expirada. Faca login novamente.');
    expect(service.isLoading()).toBeFalse();
  });

  it('captura erro 403 e utiliza detail fornecido', () => {
    service.carregarMeusHorarios().subscribe({ error: () => {} });
    httpMock
      .expectOne('/api/v1/horarios/meus')
      .flush({ detail: 'Usuario inativo no sistema' }, { status: 403, statusText: 'Forbidden' });

    expect(service.errorMessage()).toBe('Usuario inativo no sistema');
  });

  it('captura erro 422 com array de validacao do Pydantic v2', () => {
    service.carregarMeusHorarios().subscribe({ error: () => {} });
    httpMock
      .expectOne('/api/v1/horarios/meus')
      .flush(
        { detail: [{ msg: 'skip deve ser maior ou igual a zero' }] },
        { status: 422, statusText: 'Unprocessable Entity' },
      );

    expect(service.errorMessage()).toBe('skip deve ser maior ou igual a zero');
  });

  it('captura erro 500 e falha de conexao status 0 de forma segura', () => {
    service.carregarMeusHorarios().subscribe({ error: () => {} });
    httpMock
      .expectOne('/api/v1/horarios/meus')
      .flush({ detail: 'Internal trace' }, { status: 500, statusText: 'Server Error' });
    expect(service.errorMessage()).toBe('Erro interno no servidor. Tente novamente mais tarde.');

    service.carregarMeusHorarios().subscribe({ error: () => {} });
    httpMock
      .expectOne('/api/v1/horarios/meus')
      .error(new ProgressEvent('error'), { status: 0, statusText: 'Unknown Error' });
    expect(service.errorMessage()).toBe('Falha de conexao com o servidor');
  });

  it('limparErro e resetState restauram os signals', () => {
    service.carregarMeusHorarios().subscribe({ error: () => {} });
    httpMock
      .expectOne('/api/v1/horarios/meus')
      .flush({}, { status: 500, statusText: 'Server Error' });
    expect(service.errorMessage()).not.toBeNull();

    service.limparErro();
    expect(service.errorMessage()).toBeNull();

    service.carregarMeusHorarios().subscribe();
    httpMock.expectOne('/api/v1/horarios/meus').flush(mockHorarios);
    expect(service.horarios().length).toBe(3);

    service.resetState();
    expect(service.horarios()).toEqual([]);
    expect(service.isLoading()).toBeFalse();
    expect(service.errorMessage()).toBeNull();
  });

  it('ignora respostas pendentes apos resetState via controle de geracao', () => {
    service.carregarMeusHorarios().subscribe();
    const req = httpMock.expectOne('/api/v1/horarios/meus');

    service.resetState();
    req.flush(mockHorarios);

    expect(service.horarios().length).toBe(0);
    expect(service.isLoading()).toBeFalse();
  });

  it('limpa erro anterior imediatamente ao iniciar nova requisicao', () => {
    service.carregarMeusHorarios().subscribe({ error: () => {} });
    httpMock
      .expectOne('/api/v1/horarios/meus')
      .flush({}, { status: 500, statusText: 'Server Error' });
    expect(service.errorMessage()).not.toBeNull();

    service.carregarMeusHorarios().subscribe();
    expect(service.errorMessage()).toBeNull();
    httpMock.expectOne('/api/v1/horarios/meus').flush([]);
  });

  it('aplica fallback seguro quando detail em 403 nao for string', () => {
    service.carregarMeusHorarios().subscribe({ error: () => {} });
    httpMock
      .expectOne('/api/v1/horarios/meus')
      .flush({ detail: { codigo: 99 } }, { status: 403, statusText: 'Forbidden' });

    expect(service.errorMessage()).toBe('Permissao insuficiente para realizar esta acao.');
  });
});
