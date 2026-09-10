import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SecretariaComponent } from './secretaria.component';
import {
  SecretariaService,
  Curso,
  Disciplina,
  Turma,
  Matricula,
} from '../../services/secretaria.service';
import { AuthService, UserSummary } from '../../services/auth.service';
import { of } from 'rxjs';
import { signal } from '@angular/core';

describe('SecretariaComponent', () => {
  let component: SecretariaComponent;
  let fixture: ComponentFixture<SecretariaComponent>;
  let secretariaServiceSpy: jasmine.SpyObj<SecretariaService>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  /* prettier-ignore */
  const mockCursos = signal<Curso[]>([{ id: 1, campus_id: 2, nome: 'Ciencia da Computacao', codigo: 'CC' }]);
  /* prettier-ignore */
  const mockDisciplinas = signal<Disciplina[]>([{ id: 10, curso_id: 1, nome: 'Algoritmos', codigo: 'ALG1', carga_horaria: 60 }]);
  /* prettier-ignore */
  const mockTurmas = signal<Turma[]>([{ id: 100, disciplina_id: 10, professor_id: null, periodo_letivo: '2026.1', turno_preferido: 'matutino', num_matriculados: 1 }]);
  /* prettier-ignore */
  const mockMatriculas = signal<Matricula[]>([{ id: 50, aluno_id: 5, turma_id: 100, data_matricula: '2026-09-09', status: 'ativa' }]);
  /* prettier-ignore */
  const mockCurrentUser = signal<UserSummary | null>({ id: 1, nome: 'Secretaria Geral', email: 'sec@ufma.br', perfil: 'secretaria', campus_id: 2 });
  const mockLoading = signal(false),
    mockError = signal<string | null>(null);

  beforeEach(async () => {
    mockLoading.set(false);
    mockError.set(null);
    /* prettier-ignore */
    secretariaServiceSpy = jasmine.createSpyObj('SecretariaService', [
      'listarCursos', 'criarCurso', 'listarDisciplinas', 'criarDisciplina',
      'listarTurmas', 'criarTurma', 'listarMatriculas', 'matricularAluno',
    ], {
      cursos: mockCursos.asReadonly(), disciplinas: mockDisciplinas.asReadonly(),
      turmas: mockTurmas.asReadonly(), matriculas: mockMatriculas.asReadonly(),
      errorMessage: mockError.asReadonly(), isLoading: mockLoading.asReadonly(),
    });

    authServiceSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser: mockCurrentUser.asReadonly(),
    });
    secretariaServiceSpy.listarCursos.and.returnValue(of(mockCursos()));
    secretariaServiceSpy.listarDisciplinas.and.returnValue(of(mockDisciplinas()));
    secretariaServiceSpy.listarTurmas.and.returnValue(of(mockTurmas()));
    secretariaServiceSpy.listarMatriculas.and.returnValue(of(mockMatriculas()));

    await TestBed.configureTestingModule({
      imports: [SecretariaComponent],
      providers: [
        { provide: SecretariaService, useValue: secretariaServiceSpy },
        { provide: AuthService, useValue: authServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SecretariaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  /* prettier-ignore */
  it('deve inicializar com dados carregados e campus do usuario autenticado', () => {
    expect(component).toBeTruthy();
    expect(component.campusId).toBe(2);
    expect(secretariaServiceSpy.listarCursos).toHaveBeenCalledWith(2);
    expect(secretariaServiceSpy.listarDisciplinas).toHaveBeenCalledWith(undefined, 2);
    expect(secretariaServiceSpy.listarTurmas).toHaveBeenCalledWith(undefined, 2);
    expect(secretariaServiceSpy.listarMatriculas).toHaveBeenCalled();
    expect(component.abaAtiva()).toBe('cursos');
    expect(component.totalCursos() && component.totalDisciplinas() && component.totalTurmas() && component.totalMatriculas()).toBe(1);
  });

  it('nao deve carregar dados se usuario nao possuir campus valido', () => {
    const semCampus = jasmine.createSpyObj('AuthService', [], {
      currentUser: signal<UserSummary | null>(null).asReadonly(),
    });
    const loc = TestBed.createComponent(SecretariaComponent);
    (loc.componentInstance as any).authService = semCampus;
    secretariaServiceSpy.listarCursos.calls.reset();
    loc.componentInstance.ngOnInit();
    expect(loc.componentInstance.campusId).toBe(0);
    expect(secretariaServiceSpy.listarCursos).not.toHaveBeenCalled();
  });

  it('deve alternar abas e limpar mensagem de sucesso', () => {
    component.mensagemSucesso.set('Sucesso anterior');
    component.selecionarAba('disciplinas');
    expect(component.abaAtiva()).toBe('disciplinas');
    expect(component.mensagemSucesso()).toBeNull();
  });

  /* prettier-ignore */
  it('deve submeter criacao de curso e limpar formulario', () => {
    secretariaServiceSpy.criarCurso.and.returnValue(of({ id: 2, campus_id: 2, nome: 'Engenharia', codigo: 'ENG' }));
    component.formCursoNome = 'Engenharia'; component.formCursoCodigo = 'eng';
    component.cadastrarCurso();
    expect(secretariaServiceSpy.criarCurso).toHaveBeenCalledWith({ campus_id: 2, nome: 'Engenharia', codigo: 'ENG' });
    expect(component.formCursoNome === '' && component.formCursoCodigo === '').toBeTrue();
    expect(component.mensagemSucesso()).toContain('Curso');
  });

  /* prettier-ignore */
  it('deve submeter criacao de disciplina com carga horaria inteira', () => {
    secretariaServiceSpy.criarDisciplina.and.returnValue(of({ id: 11, curso_id: 1, nome: 'Calculo', codigo: 'MAT1', carga_horaria: 80 }));
    component.formDiscCursoId = 1; component.formDiscNome = 'Calculo'; component.formDiscCodigo = 'mat1'; component.formDiscCarga = 80.5;
    component.cadastrarDisciplina();
    expect(secretariaServiceSpy.criarDisciplina).toHaveBeenCalledWith({ curso_id: 1, nome: 'Calculo', codigo: 'MAT1', carga_horaria: 80 });
    expect(component.mensagemSucesso()).toContain('Disciplina');
  });

  /* prettier-ignore */
  it('deve submeter criacao de turma', () => {
    secretariaServiceSpy.criarTurma.and.returnValue(of({ id: 101, disciplina_id: 10, professor_id: null, periodo_letivo: '2026.1', turno_preferido: 'noturno', num_matriculados: 0 }));
    component.formTurmaDiscId = 10; component.formTurmaPeriodo = '2026.1'; component.formTurmaTurno = 'noturno';
    component.cadastrarTurma();
    expect(secretariaServiceSpy.criarTurma).toHaveBeenCalledWith({ disciplina_id: 10, professor_id: null, periodo_letivo: '2026.1', turno_preferido: 'noturno' });
    expect(component.mensagemSucesso()).toContain('Turma');
  });

  /* prettier-ignore */
  it('deve submeter matricula de aluno', () => {
    secretariaServiceSpy.matricularAluno.and.returnValue(of({ id: 51, aluno_id: 7, turma_id: 100, data_matricula: '2026-09-09', status: 'ativa' }));
    component.formMatAlunoId = 7; component.formMatTurmaId = 100;
    component.matricularAluno();
    expect(secretariaServiceSpy.matricularAluno).toHaveBeenCalledWith({ aluno_id: 7, turma_id: 100 });
    expect(component.mensagemSucesso()).toContain('Matricula');
  });

  it('deve ignorar submissoes quando campus invalido ou campos vazios', () => {
    secretariaServiceSpy.criarCurso.calls.reset();
    component.campusId = 0;
    component.formCursoNome = '';
    component.cadastrarCurso();
    expect(secretariaServiceSpy.criarCurso).not.toHaveBeenCalled();
  });
});
