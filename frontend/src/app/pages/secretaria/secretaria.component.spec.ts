import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { SecretariaComponent } from './secretaria.component';
import {
  SecretariaService,
  Curso,
  Disciplina,
  Turma,
  Matricula,
} from '../../services/secretaria.service';
import { AuthService, UserSummary } from '../../services/auth.service';
import { of, throwError } from 'rxjs';
import { signal, computed } from '@angular/core';

describe('SecretariaComponent', () => {
  let component: SecretariaComponent;
  let fixture: ComponentFixture<SecretariaComponent>;
  let secretariaServiceSpy: jasmine.SpyObj<SecretariaService>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  // prettier-ignore
  const mockCursos = signal<Curso[]>([{ id: 1, campus_id: 2, nome: 'Ciencia da Computacao', codigo: 'CC' }]);
  // prettier-ignore
  const mockDisciplinas = signal<Disciplina[]>([{ id: 10, curso_id: 1, nome: 'Algoritmos', codigo: 'ALG1', carga_horaria: 60 }]);
  // prettier-ignore
  const mockTurmas = signal<Turma[]>([{ id: 100, disciplina_id: 10, professor_id: null, periodo_letivo: '2026.1', turno_preferido: 'matutino', num_matriculados: 1 }]);
  // prettier-ignore
  const mockMatriculas = signal<Matricula[]>([{ id: 50, aluno_id: 5, turma_id: 100, data_matricula: '2026-09-09', status: 'ativa' }]);
  // prettier-ignore
  const mockCurrentUser = signal<UserSummary | null>({ id: 1, nome: 'Secretaria Geral', email: 'sec@ufma.br', perfil: 'secretaria', campus_id: 2 });
  // prettier-ignore
  const mockLoading = signal(false), mockError = signal<string | null>(null);

  // prettier-ignore
  beforeEach(async () => {
    mockLoading.set(false); mockError.set(null);
    mockCurrentUser.set({ id: 1, nome: 'Secretaria Geral', email: 'sec@ufma.br', perfil: 'secretaria', campus_id: 2 });
    secretariaServiceSpy = jasmine.createSpyObj('SecretariaService', [
      'listarCursos', 'criarCurso', 'listarDisciplinas', 'criarDisciplina',
      'listarTurmas', 'criarTurma', 'listarMatriculas', 'matricularAluno', 'cancelarMatricula', 'limparErro',
    ], {
      cursos: mockCursos.asReadonly(), disciplinas: mockDisciplinas.asReadonly(),
      turmas: mockTurmas.asReadonly(), matriculas: mockMatriculas.asReadonly(),
      errorMessage: mockError.asReadonly(), isLoading: mockLoading.asReadonly(),
    });
    authServiceSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser: mockCurrentUser.asReadonly(),
      currentRole: computed(() => mockCurrentUser()?.perfil ?? null),
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

  // prettier-ignore
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

  // prettier-ignore
  it('nao deve carregar dados se usuario nao possuir campus valido', () => {
    const semCampus = jasmine.createSpyObj('AuthService', [], {
      currentUser: signal<UserSummary | null>(null).asReadonly(),
      currentRole: signal(null).asReadonly(),
    });
    const loc = TestBed.createComponent(SecretariaComponent);
    (loc.componentInstance as any).authService = semCampus;
    secretariaServiceSpy.listarCursos.calls.reset();
    loc.componentInstance.ngOnInit();
    expect(loc.componentInstance.campusId).toBe(0);
    expect(secretariaServiceSpy.listarCursos).not.toHaveBeenCalled();
  });

  // prettier-ignore
  it('deve alternar abas e limpar mensagem de sucesso e erro do servico', () => {
    component.mensagemSucesso.set('Sucesso anterior');
    component.selecionarAba('disciplinas');
    expect(component.abaAtiva()).toBe('disciplinas');
    expect(component.mensagemSucesso()).toBeNull();
    expect(secretariaServiceSpy.limparErro).toHaveBeenCalled();
  });

  // prettier-ignore
  it('deve submeter criacao de curso e limpar formulario', () => {
    secretariaServiceSpy.criarCurso.and.returnValue(of({ id: 2, campus_id: 2, nome: 'Engenharia', codigo: 'ENG' }));
    component.formCursoNome = 'Engenharia'; component.formCursoCodigo = 'eng';
    component.cadastrarCurso();
    expect(secretariaServiceSpy.criarCurso).toHaveBeenCalledWith({ campus_id: 2, nome: 'Engenharia', codigo: 'ENG' });
    expect(component.formCursoNome === '' && component.formCursoCodigo === '').toBeTrue();
    expect(component.mensagemSucesso()).toContain('Curso');
  });

  // prettier-ignore
  it('deve submeter criacao de disciplina com carga horaria inteira', () => {
    secretariaServiceSpy.criarDisciplina.and.returnValue(of({ id: 11, curso_id: 1, nome: 'Calculo', codigo: 'MAT1', carga_horaria: 80 }));
    component.formDiscCursoId = 1; component.formDiscNome = 'Calculo'; component.formDiscCodigo = 'mat1'; component.formDiscCarga = 80;
    component.cadastrarDisciplina();
    expect(secretariaServiceSpy.criarDisciplina).toHaveBeenCalledWith({ curso_id: 1, nome: 'Calculo', codigo: 'MAT1', carga_horaria: 80 });
    expect(component.mensagemSucesso()).toContain('Disciplina');
  });

  // prettier-ignore
  it('deve submeter criacao de turma e tratar professor id valido ou nulo', () => {
    secretariaServiceSpy.criarTurma.and.returnValue(of({ id: 101, disciplina_id: 10, professor_id: null, periodo_letivo: '2026.1', turno_preferido: 'noturno', num_matriculados: 0 }));
    component.formTurmaDiscId = 10; component.formTurmaPeriodo = '2026.1'; component.formTurmaTurno = 'noturno';
    component.cadastrarTurma();
    expect(secretariaServiceSpy.criarTurma).toHaveBeenCalledWith({ disciplina_id: 10, professor_id: null, periodo_letivo: '2026.1', turno_preferido: 'noturno' });
    expect(component.mensagemSucesso()).toContain('Turma');
  });

  // prettier-ignore
  it('deve submeter matricula de aluno com id inteiro positivo', () => {
    secretariaServiceSpy.matricularAluno.and.returnValue(of({ id: 51, aluno_id: 7, turma_id: 100, data_matricula: '2026-09-09', status: 'ativa' }));
    component.formMatAlunoId = 7; component.formMatTurmaId = 100;
    component.matricularAluno();
    expect(secretariaServiceSpy.matricularAluno).toHaveBeenCalledWith({ aluno_id: 7, turma_id: 100 });
    expect(component.mensagemSucesso()).toContain('Matricula');
  });

  // prettier-ignore
  it('deve ignorar submissoes quando campus invalido, dados nulos ou IDs invalidos', () => {
    secretariaServiceSpy.criarCurso.calls.reset(); secretariaServiceSpy.criarDisciplina.calls.reset();
    secretariaServiceSpy.criarTurma.calls.reset(); secretariaServiceSpy.matricularAluno.calls.reset();
    component.campusId = 0; component.formCursoNome = 'Teste'; component.formCursoCodigo = 'TST'; component.cadastrarCurso();
    expect(secretariaServiceSpy.criarCurso).not.toHaveBeenCalled();
    component.campusId = 2; component.formDiscCursoId = null; component.cadastrarDisciplina();
    expect(secretariaServiceSpy.criarDisciplina).not.toHaveBeenCalled();
    component.formTurmaDiscId = 10; component.formTurmaPeriodo = '   '; component.cadastrarTurma();
    component.formTurmaPeriodo = '2026.1'; component.formTurmaProfId = -1; component.cadastrarTurma();
    expect(secretariaServiceSpy.criarTurma).not.toHaveBeenCalled();
    component.formMatTurmaId = 100; component.formMatAlunoId = -5; component.matricularAluno();
    component.formMatAlunoId = 2.5; component.matricularAluno();
    expect(secretariaServiceSpy.matricularAluno).not.toHaveBeenCalled();
  });

  // prettier-ignore
  it('deve tratar erros de subscricao de forma resiliente', () => {
    secretariaServiceSpy.criarCurso.and.returnValue(throwError(() => new Error('Falha')));
    component.formCursoNome = 'Engenharia'; component.formCursoCodigo = 'ENG';
    component.cadastrarCurso();
    expect(component.mensagemSucesso()).toBeNull();
  });

  it('deve aplicar debounce de 300ms ao pesquisar turmas por texto', fakeAsync(() => {
    secretariaServiceSpy.listarTurmas.calls.reset();
    component.buscaTurmas = '2026';
    component.aoDigitarBuscaTurmas('2026');
    tick(200);
    expect(secretariaServiceSpy.listarTurmas).not.toHaveBeenCalled();
    tick(100);
    expect(secretariaServiceSpy.listarTurmas).toHaveBeenCalledWith(undefined, 2, '2026');
  }));

  it('deve cancelar matricula ativa na secretaria e exibir feedback visual de confirmacao', () => {
    const matAtiva = mockMatriculas()[0];
    secretariaServiceSpy.cancelarMatricula.and.returnValue(
      of({ ...matAtiva, status: 'cancelada' }),
    );
    component.selecionarAba('matriculas');
    fixture.detectChanges();

    const btnCancelar = fixture.nativeElement.querySelector(
      '[data-testid="btn-cancelar-matricula-50"]',
    ) as HTMLButtonElement;
    expect(btnCancelar).not.toBeNull();
    btnCancelar.click();

    expect(secretariaServiceSpy.cancelarMatricula).toHaveBeenCalledWith(50);
    expect(component.mensagemSucesso()).toContain('Matricula #50 cancelada com sucesso.');
  });

  it('deve ocultar formularios de escrita e acoes de cancelamento para perfis sem permissao de escrita', () => {
    mockCurrentUser.set({
      id: 9,
      nome: 'Prof Consulta',
      email: 'prof@ufma.br',
      perfil: 'professor',
      campus_id: 2,
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('form')).toBeNull();

    component.selecionarAba('matriculas');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('form')).toBeNull();
    expect(
      fixture.nativeElement.querySelector('[data-testid="btn-cancelar-matricula-50"]'),
    ).toBeNull();
  });
});
