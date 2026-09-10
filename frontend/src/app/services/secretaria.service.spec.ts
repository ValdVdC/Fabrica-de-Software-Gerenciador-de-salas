import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { SecretariaService } from './secretaria.service';

describe('SecretariaService', () => {
  let service: SecretariaService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [SecretariaService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(SecretariaService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  function expectPost(url: string, body: unknown, response: any) {
    const r = httpMock.expectOne(url);
    expect(r.request.method).toBe('POST');
    expect(r.request.body).toEqual(body);
    r.flush(response);
  }

  it('lista e cria cursos com suporte a query params e atualizacao reativa', () => {
    service.listarCursos().subscribe((res) => expect(res.length).toBe(1));
    httpMock
      .expectOne('/api/v1/cursos')
      .flush([{ id: 1, campus_id: 1, nome: 'Computacao', codigo: 'CC' }]);
    expect(service.cursos().length).toBe(1);

    service.listarCursos(1).subscribe();
    httpMock
      .expectOne((r) => r.url === '/api/v1/cursos' && r.params.get('campus_id') === '1')
      .flush([]);

    const payload = { campus_id: 1, nome: 'Engenharia', codigo: 'ENG' };
    service.criarCurso(payload).subscribe((res) => expect(res.id).toBe(2));
    expectPost('/api/v1/cursos', payload, { id: 2, ...payload });
    expect(service.cursos().some((c) => c.id === 2)).toBeTrue();
  });

  it('lista e cria disciplinas com filtros de curso e campus', () => {
    service.listarDisciplinas(1, 2).subscribe((res) => expect(res.length).toBe(1));
    httpMock
      .expectOne(
        (r) =>
          r.url === '/api/v1/disciplinas' &&
          r.params.get('curso_id') === '1' &&
          r.params.get('campus_id') === '2',
      )
      .flush([{ id: 1, curso_id: 1, nome: 'Algoritmos', codigo: 'ALG1', carga_horaria: 60 }]);
    expect(service.disciplinas().length).toBe(1);

    const payload = { curso_id: 1, nome: 'ED', codigo: 'ED1', carga_horaria: 60 };
    service.criarDisciplina(payload).subscribe((r) => expect(r.id).toBe(2));
    expectPost('/api/v1/disciplinas', payload, { id: 2, ...payload });
    expect(service.disciplinas().some((d) => d.id === 2)).toBeTrue();
  });

  it('lista turmas, obtem turma por id e cria nova turma', () => {
    /* prettier-ignore */
    const turma = { id: 10, disciplina_id: 1, professor_id: 2, periodo_letivo: '2026.1', turno_preferido: 'integral' as const, num_matriculados: 0 };
    service.listarTurmas(1, 1).subscribe((res) => expect(res.length).toBe(1));
    httpMock
      .expectOne(
        (r) =>
          r.url === '/api/v1/turmas' &&
          r.params.get('disciplina_id') === '1' &&
          r.params.get('campus_id') === '1',
      )
      .flush([turma]);
    expect(service.turmas().length).toBe(1);

    service.obterTurma(10).subscribe((res) => expect(res.id).toBe(10));
    httpMock.expectOne('/api/v1/turmas/10').flush(turma);

    const payload = {
      disciplina_id: 1,
      periodo_letivo: '2026.1',
      turno_preferido: 'noturno' as const,
    };
    service.criarTurma(payload).subscribe((r) => expect(r.id).toBe(11));
    /* prettier-ignore */
    expectPost('/api/v1/turmas', payload, { id: 11, professor_id: null, num_matriculados: 0, ...payload });
    expect(service.turmas().some((t) => t.id === 11)).toBeTrue();
  });

  it('sincroniza matricula e incrementa num_matriculados na turma reativamente', () => {
    service.listarTurmas().subscribe();
    /* prettier-ignore */
    httpMock.expectOne('/api/v1/turmas').flush([{ id: 10, disciplina_id: 1, professor_id: null, periodo_letivo: '2026.1', turno_preferido: 'matutino', num_matriculados: 0 }]);

    service.listarMatriculas(10).subscribe();
    httpMock
      .expectOne((r) => r.url === '/api/v1/matriculas' && r.params.get('turma_id') === '10')
      .flush([]);

    const payload = { aluno_id: 5, turma_id: 10 };
    service.matricularAluno(payload).subscribe((r) => expect(r.id).toBe(1));
    /* prettier-ignore */
    expectPost('/api/v1/matriculas', payload, { id: 1, data_matricula: '2026-09-09', status: 'ativa', ...payload });

    expect(service.matriculas().some((m) => m.id === 1)).toBeTrue();
    expect(service.turmas().find((t) => t.id === 10)?.num_matriculados).toBe(1);
  });

  it('nao ativa isLoading antes da subscricao devido ao defer', () => {
    service.listarCursos();
    expect(service.isLoading()).toBeFalse();
  });

  it('rejeita identificadores e payloads invalidos defensivamente com excecao sincronizada', () => {
    /* prettier-ignore */
    const invalidFns = [
      () => service.listarCursos(0), () => service.listarDisciplinas(0),
      () => service.listarDisciplinas(1, -1), () => service.listarTurmas(-2),
      () => service.obterTurma(0), () => service.listarMatriculas(0),
      () => service.criarCurso({ campus_id: 0, nome: '', codigo: '' }),
      () => service.criarDisciplina({ curso_id: 0, nome: '', codigo: '', carga_horaria: 0 }),
      () => service.criarTurma({ disciplina_id: 0, periodo_letivo: '', turno_preferido: 'matutino' }),
      () => service.matricularAluno({ aluno_id: 0, turma_id: 0 }),
    ];
    invalidFns.forEach((fn) => expect(fn).toThrow());
  });

  it('trata erros HTTP 0, 422 estruturado do Pydantic e 500 sem vazamento', () => {
    service.listarCursos().subscribe({
      error: () => expect(service.errorMessage()).toBe('Nao foi possivel conectar ao servidor'),
    });
    httpMock.expectOne('/api/v1/cursos').flush({}, { status: 0, statusText: 'Unknown Error' });

    service.criarCurso({ campus_id: 1, nome: 'A', codigo: 'B' }).subscribe({
      error: () =>
        expect(service.errorMessage()).toContain('String should have at least 2 characters'),
    });
    httpMock
      .expectOne('/api/v1/cursos')
      .flush(
        { detail: [{ msg: 'String should have at least 2 characters' }] },
        { status: 422, statusText: 'Unprocessable Entity' },
      );

    service.listarCursos().subscribe({
      error: () =>
        expect(service.errorMessage()).toBe(
          'Erro interno no servidor. Tente novamente mais tarde.',
        ),
    });
    httpMock
      .expectOne('/api/v1/cursos')
      .flush({ detail: 'traceback' }, { status: 500, statusText: 'Server Error' });
  });

  it('reseta estado e limpa mensagens de erro com resetState e limparErro', () => {
    service.listarCursos().subscribe();
    /* prettier-ignore */
    httpMock.expectOne('/api/v1/cursos').flush([{ id: 1, campus_id: 1, nome: 'C', codigo: 'C' }]);
    service.listarDisciplinas().subscribe();
    /* prettier-ignore */
    httpMock.expectOne('/api/v1/disciplinas').flush([{ id: 1, curso_id: 1, nome: 'D', codigo: 'D', carga_horaria: 60 }]);
    service.listarTurmas().subscribe();
    /* prettier-ignore */
    httpMock.expectOne('/api/v1/turmas').flush([{ id: 1, disciplina_id: 1, professor_id: null, periodo_letivo: '2026.1', turno_preferido: 'matutino', num_matriculados: 0 }]);
    service.listarMatriculas().subscribe();
    /* prettier-ignore */
    httpMock.expectOne('/api/v1/matriculas').flush([{ id: 1, aluno_id: 1, turma_id: 1, data_matricula: '2026-09-09', status: 'ativa' }]);
    service.listarCursos().subscribe({ error: () => {} });
    httpMock.expectOne('/api/v1/cursos').flush({}, { status: 500, statusText: 'Err' });

    expect(
      service.cursos().length &&
        service.disciplinas().length &&
        service.turmas().length &&
        service.matriculas().length,
    ).toBe(1);
    expect(service.errorMessage()).not.toBeNull();

    service.limparErro();
    expect(service.errorMessage()).toBeNull();
    service.resetState();
    expect(
      service.cursos().length +
        service.disciplinas().length +
        service.turmas().length +
        service.matriculas().length,
    ).toBe(0);
  });

  it('ignora respostas pendentes apos resetState via geracao', () => {
    service.listarCursos().subscribe();
    const req = httpMock.expectOne('/api/v1/cursos');
    service.resetState();
    req.flush([{ id: 99, campus_id: 1, nome: 'Fantasma', codigo: 'FAN' }]);
    expect(service.cursos().length).toBe(0);
    expect(service.isLoading()).toBeFalse();
  });
});
