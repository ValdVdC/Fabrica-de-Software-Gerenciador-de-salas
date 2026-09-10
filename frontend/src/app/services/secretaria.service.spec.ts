import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import {
  SecretariaService,
  Curso,
  CursoCreate,
  Disciplina,
  DisciplinaCreate,
  Turma,
  TurmaCreate,
  Matricula,
  MatriculaCreate,
} from './secretaria.service';

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

  afterEach(() => {
    httpMock.verify();
  });

  it('lista e cria cursos com suporte a query params e atualizacao reativa', () => {
    const mockCursos: Curso[] = [{ id: 1, campus_id: 1, nome: 'Computacao', codigo: 'CC' }];
    service.listarCursos().subscribe((res) => expect(res.length).toBe(1));
    httpMock.expectOne('/api/v1/cursos').flush(mockCursos);
    expect(service.cursos().length).toBe(1);

    service.listarCursos(1).subscribe();
    httpMock
      .expectOne((r) => r.url === '/api/v1/cursos' && r.params.get('campus_id') === '1')
      .flush(mockCursos);

    const payload: CursoCreate = { campus_id: 1, nome: 'Engenharia', codigo: 'ENG' };
    service.criarCurso(payload).subscribe((res) => expect(res.id).toBe(2));
    httpMock.expectOne('/api/v1/cursos').flush({ id: 2, ...payload });
    expect(service.cursos().some((c) => c.id === 2)).toBeTrue();
  });

  it('lista e cria disciplinas com filtros de curso e campus', () => {
    const mockDisc: Disciplina[] = [
      { id: 1, curso_id: 1, nome: 'Algoritmos', codigo: 'ALG1', carga_horaria: 60 },
    ];
    service.listarDisciplinas(1, 2).subscribe((res) => expect(res.length).toBe(1));
    httpMock
      .expectOne(
        (r) =>
          r.url === '/api/v1/disciplinas' &&
          r.params.get('curso_id') === '1' &&
          r.params.get('campus_id') === '2',
      )
      .flush(mockDisc);
    expect(service.disciplinas().length).toBe(1);

    const payload: DisciplinaCreate = {
      curso_id: 1,
      nome: 'Estruturas',
      codigo: 'ED1',
      carga_horaria: 60,
    };
    service.criarDisciplina(payload).subscribe((res) => expect(res.id).toBe(2));
    httpMock.expectOne('/api/v1/disciplinas').flush({ id: 2, ...payload });
    expect(service.disciplinas().some((d) => d.id === 2)).toBeTrue();
  });

  it('lista turmas, obtem turma por id e cria nova turma', () => {
    const mockTurma: Turma = {
      id: 10,
      disciplina_id: 1,
      professor_id: 2,
      periodo_letivo: '2026.1',
      turno_preferido: 'integral',
      num_matriculados: 0,
    };
    service.listarTurmas(1, 1).subscribe((res) => expect(res.length).toBe(1));
    httpMock
      .expectOne(
        (r) =>
          r.url === '/api/v1/turmas' &&
          r.params.get('disciplina_id') === '1' &&
          r.params.get('campus_id') === '1',
      )
      .flush([mockTurma]);
    expect(service.turmas().length).toBe(1);

    service.obterTurma(10).subscribe((res) => expect(res.id).toBe(10));
    httpMock.expectOne('/api/v1/turmas/10').flush(mockTurma);

    const payload: TurmaCreate = {
      disciplina_id: 1,
      periodo_letivo: '2026.1',
      turno_preferido: 'noturno',
    };
    service.criarTurma(payload).subscribe((res) => expect(res.id).toBe(11));
    httpMock
      .expectOne('/api/v1/turmas')
      .flush({ id: 11, ...payload, professor_id: null, num_matriculados: 0 });
    expect(service.turmas().some((t) => t.id === 11)).toBeTrue();
  });

  it('sincroniza matricula e incrementa num_matriculados na turma reativamente', () => {
    service.listarTurmas().subscribe();
    httpMock
      .expectOne('/api/v1/turmas')
      .flush([
        {
          id: 10,
          disciplina_id: 1,
          professor_id: null,
          periodo_letivo: '2026.1',
          turno_preferido: 'matutino',
          num_matriculados: 0,
        },
      ]);

    service.listarMatriculas(10).subscribe((res) => expect(res.length).toBe(0));
    httpMock
      .expectOne((r) => r.url === '/api/v1/matriculas' && r.params.get('turma_id') === '10')
      .flush([]);

    const payload: MatriculaCreate = { aluno_id: 5, turma_id: 10 };
    service.matricularAluno(payload).subscribe((res) => expect(res.id).toBe(1));
    httpMock
      .expectOne('/api/v1/matriculas')
      .flush({ id: 1, ...payload, data_matricula: '2026-09-09', status: 'ativa' });

    expect(service.matriculas().some((m) => m.id === 1)).toBeTrue();
    const turma = service.turmas().find((t) => t.id === 10);
    expect(turma?.num_matriculados).toBe(1);
  });

  it('nao ativa isLoading antes da subscricao devido ao defer', () => {
    service.listarCursos();
    expect(service.isLoading()).toBeFalse();
  });

  it('rejeita identificadores e payloads invalidos defensivamente com excecao sincronizada', () => {
    expect(() => service.listarCursos(0)).toThrowError('Identificador de campus invalido');
    expect(() => service.listarDisciplinas(0)).toThrowError('Identificador de curso invalido');
    expect(() => service.listarDisciplinas(1, -1)).toThrowError('Identificador de campus invalido');
    expect(() => service.listarTurmas(-2)).toThrowError('Identificador de disciplina invalido');
    expect(() => service.obterTurma(0)).toThrowError('Identificador de turma invalido');
    expect(() => service.listarMatriculas(0)).toThrowError('Identificador de turma invalido');
    expect(() => service.criarCurso({ campus_id: 0, nome: '', codigo: '' })).toThrowError(
      'Dados de curso invalidos',
    );
    expect(() =>
      service.criarDisciplina({ curso_id: 0, nome: '', codigo: '', carga_horaria: 0 }),
    ).toThrowError('Dados de disciplina invalidos');
    expect(() =>
      service.criarTurma({ disciplina_id: 0, periodo_letivo: '', turno_preferido: 'matutino' }),
    ).toThrowError('Dados de turma invalidos');
    expect(() => service.matricularAluno({ aluno_id: 0, turma_id: 0 })).toThrowError(
      'Dados de matricula invalidos',
    );
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
    service.limparErro();
    expect(service.errorMessage()).toBeNull();
    service.resetState();
    expect(service.cursos().length).toBe(0);
    expect(service.disciplinas().length).toBe(0);
    expect(service.turmas().length).toBe(0);
    expect(service.matriculas().length).toBe(0);
  });
});
