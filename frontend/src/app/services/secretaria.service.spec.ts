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

  it('lista cursos com e sem campusId via HttpParams e atualiza signal', () => {
    const mockCursos: Curso[] = [
      { id: 1, campus_id: 1, nome: 'Ciencia da Computacao', codigo: 'CC', ativo: true },
    ];

    service.listarCursos().subscribe((res) => expect(res.length).toBe(1));
    httpMock.expectOne('/api/v1/cursos').flush(mockCursos);
    expect(service.cursos().length).toBe(1);

    service.listarCursos(1).subscribe((res) => expect(res.length).toBe(1));
    const req = httpMock.expectOne(
      (r) => r.url === '/api/v1/cursos' && r.params.get('campus_id') === '1',
    );
    req.flush(mockCursos);
  });

  it('cria curso com sucesso e atualiza signal', () => {
    const payload: CursoCreate = { campus_id: 1, nome: 'Engenharia', codigo: 'ENG' };
    const mockCriado: Curso = { id: 2, ...payload, ativo: true };

    service.criarCurso(payload).subscribe((res) => expect(res.id).toBe(2));
    httpMock.expectOne('/api/v1/cursos').flush(mockCriado);
    expect(service.cursos().some((c) => c.id === 2)).toBeTrue();
  });

  it('lista e cria disciplinas com filtros de curso e campus', () => {
    const mockDisc: Disciplina[] = [
      { id: 1, curso_id: 1, nome: 'Algoritmos', codigo: 'ALG1', carga_horaria: 60, ativo: true },
    ];

    service.listarDisciplinas(1, 2).subscribe((res) => expect(res.length).toBe(1));
    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/disciplinas' &&
        r.params.get('curso_id') === '1' &&
        r.params.get('campus_id') === '2',
    );
    req.flush(mockDisc);
    expect(service.disciplinas().length).toBe(1);

    const payload: DisciplinaCreate = {
      curso_id: 1,
      nome: 'Estrutura de Dados',
      codigo: 'ED1',
      carga_horaria: 60,
    };
    service.criarDisciplina(payload).subscribe((res) => expect(res.id).toBe(2));
    httpMock.expectOne('/api/v1/disciplinas').flush({ id: 2, ...payload, ativo: true });
    expect(service.disciplinas().some((d) => d.id === 2)).toBeTrue();
  });

  it('lista turmas, obtem turma por id e cria nova turma', () => {
    const mockTurmas: Turma[] = [
      {
        id: 10,
        disciplina_id: 1,
        professor_id: 2,
        periodo_letivo: '2026.1',
        turno_preferido: 'matutino',
        num_matriculados: 0,
      },
    ];

    service.listarTurmas(1, 1).subscribe((res) => expect(res.length).toBe(1));
    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/turmas' &&
        r.params.get('disciplina_id') === '1' &&
        r.params.get('campus_id') === '1',
    );
    req.flush(mockTurmas);
    expect(service.turmas().length).toBe(1);

    service.obterTurma(10).subscribe((res) => expect(res.id).toBe(10));
    httpMock.expectOne('/api/v1/turmas/10').flush(mockTurmas[0]);

    const payload: TurmaCreate = {
      disciplina_id: 1,
      professor_id: null,
      periodo_letivo: '2026.1',
      turno_preferido: 'noturno',
    };
    service.criarTurma(payload).subscribe((res) => expect(res.id).toBe(11));
    httpMock.expectOne('/api/v1/turmas').flush({ id: 11, ...payload, num_matriculados: 0 });
    expect(service.turmas().some((t) => t.id === 11)).toBeTrue();
  });

  it('lista matriculas e matricula aluno em turma com atualizacao reativa', () => {
    const mockMatriculas: Matricula[] = [
      { id: 1, aluno_id: 5, turma_id: 10, data_matricula: '2026-09-09', status: 'ativa' },
    ];

    service.listarMatriculas(10).subscribe((res) => expect(res.length).toBe(1));
    const req = httpMock.expectOne(
      (r) => r.url === '/api/v1/matriculas' && r.params.get('turma_id') === '10',
    );
    req.flush(mockMatriculas);
    expect(service.matriculas().length).toBe(1);

    const payload: MatriculaCreate = { aluno_id: 6, turma_id: 10 };
    service.matricularAluno(payload).subscribe((res) => expect(res.id).toBe(2));
    httpMock
      .expectOne('/api/v1/matriculas')
      .flush({ id: 2, ...payload, data_matricula: '2026-09-09', status: 'ativa' });
    expect(service.matriculas().some((m) => m.id === 2)).toBeTrue();
  });

  it('rejeita identificadores invalidos defensivamente com excecao sincronizada', () => {
    expect(() => service.listarCursos(0)).toThrowError('Identificador de campus invalido');
    expect(() => service.listarDisciplinas(0)).toThrowError('Identificador de curso invalido');
    expect(() => service.listarDisciplinas(1, -1)).toThrowError('Identificador de campus invalido');
    expect(() => service.listarTurmas(-2)).toThrowError('Identificador de disciplina invalido');
    expect(() => service.obterTurma(0)).toThrowError('Identificador de turma invalido');
    expect(() => service.listarMatriculas(0)).toThrowError('Identificador de turma invalido');
  });

  it('nao vaza informacoes internas de servidor em erros HTTP 500', () => {
    service.listarCursos().subscribe({
      error: () => {
        expect(service.errorMessage()).toBe(
          'Erro interno no servidor. Tente novamente mais tarde.',
        );
      },
    });
    httpMock
      .expectOne('/api/v1/cursos')
      .flush(
        { detail: 'Internal database error trace' },
        { status: 500, statusText: 'Server Error' },
      );
  });
});
