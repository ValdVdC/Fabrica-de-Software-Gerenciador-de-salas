import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal, WritableSignal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { GradeHorariaComponent } from './grade-horaria.component';
import { HorarioService, HorarioMeu } from '../../services/horario.service';

describe('GradeHorariaComponent', () => {
  let component: GradeHorariaComponent;
  let fixture: ComponentFixture<GradeHorariaComponent>;

  let mockHorariosSignal: WritableSignal<HorarioMeu[]>;
  let mockIsLoadingSignal: WritableSignal<boolean>;
  let mockErrorMessageSignal: WritableSignal<string | null>;
  let mockTotalAulasSignal: WritableSignal<number>;
  let mockDisciplinasDistintasSignal: WritableSignal<string[]>;

  let mockHorarioService: any;

  const mockAulas: HorarioMeu[] = [
    {
      id: 1,
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
      id: 2,
      campus_id: 1,
      turma_id: 11,
      disciplina_nome: 'Calculo Diferencial',
      disciplina_codigo: 'MAT1',
      periodo_letivo: '2026.1',
      turno: 'matutino',
      dia_semana: 2,
      hora_inicio: '10:00:00',
      hora_fim: '12:00:00',
      sala_id: 102,
      sala_bloco: 'Bloco 2',
      sala_numero: '202',
      sala_tipo: 'laboratorio',
      professor_id: 3,
      professor_nome: 'Prof Ada Lovelace',
    },
  ];

  beforeEach(async () => {
    mockHorariosSignal = signal<HorarioMeu[]>([]);
    mockIsLoadingSignal = signal<boolean>(false);
    mockErrorMessageSignal = signal<string | null>(null);
    mockTotalAulasSignal = signal<number>(0);
    mockDisciplinasDistintasSignal = signal<string[]>([]);

    mockHorarioService = {
      horarios: mockHorariosSignal,
      isLoading: mockIsLoadingSignal,
      errorMessage: mockErrorMessageSignal,
      totalAulas: mockTotalAulasSignal,
      disciplinasDistintas: mockDisciplinasDistintasSignal,
      carregarMeusHorarios: jasmine.createSpy('carregarMeusHorarios').and.returnValue(of([])),
      obterHorariosDoDia: jasmine.createSpy('obterHorariosDoDia').and.callFake((dia: number) => {
        return mockHorariosSignal().filter((h) => h.dia_semana === dia);
      }),
    };

    await TestBed.configureTestingModule({
      imports: [GradeHorariaComponent],
      providers: [{ provide: HorarioService, useValue: mockHorarioService }],
    }).compileComponents();

    fixture = TestBed.createComponent(GradeHorariaComponent);
    component = fixture.componentInstance;
  });

  it('deve inicializar e disparar carregarMeusHorarios', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
    expect(mockHorarioService.carregarMeusHorarios).toHaveBeenCalled();
  });

  it('deve exibir metricas de resumo e perfil ativo', () => {
    mockTotalAulasSignal.set(2);
    mockDisciplinasDistintasSignal.set(['AED1', 'MAT1']);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Total de Aulas');
    expect(compiled.textContent).toContain('2');
    expect(compiled.textContent).toContain('Disciplinas');
    expect(compiled.textContent).toContain('Discente');
  });

  it('deve exibir mensagem de carregamento quando isLoading e totalAulas for zero', () => {
    mockIsLoadingSignal.set(true);
    mockTotalAulasSignal.set(0);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.loading-box')?.textContent).toContain(
      'Carregando grade horaria...',
    );
  });

  it('deve exibir mensagem de grade vazia quando nao houver aulas', () => {
    mockIsLoadingSignal.set(false);
    mockTotalAulasSignal.set(0);
    mockErrorMessageSignal.set(null);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.empty-box')?.textContent).toContain('Nenhum horario alocado');
  });

  it('deve exibir banner de erro e disparar retry ao clicar em tentar novamente', () => {
    mockErrorMessageSignal.set('Falha ao obter grade');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const alert = compiled.querySelector('.alert-error');
    expect(alert?.textContent).toContain('Falha ao obter grade');

    const btnRetry = compiled.querySelector('.btn-retry') as HTMLButtonElement;
    btnRetry.click();
    expect(mockHorarioService.carregarMeusHorarios).toHaveBeenCalledTimes(2);
  });

  it('deve renderizar a grade semanal com colunas e cards de aula', () => {
    mockHorariosSignal.set(mockAulas);
    mockTotalAulasSignal.set(2);
    mockDisciplinasDistintasSignal.set(['AED1', 'MAT1']);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const colunas = compiled.querySelectorAll('.dia-coluna');
    expect(colunas.length).toBe(6);

    expect(compiled.textContent).toContain('AED1');
    expect(compiled.textContent).toContain('Bloco 1 - 101');
    expect(compiled.textContent).toContain('08:00 - 10:00');
    expect(compiled.textContent).toContain('Docente: Prof Alan Turing');
  });

  it('deve renderizar detalhes de turma quando o perfil for professor', () => {
    fixture.componentRef.setInput('perfil', 'professor');
    mockHorariosSignal.set(mockAulas);
    mockTotalAulasSignal.set(2);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Docente');
    expect(compiled.textContent).toContain('Periodo: 2026.1 (matutino)');
  });

  it('nao deve renderizar a grade semanal quando houver erro e totalAulas for zero', () => {
    mockErrorMessageSignal.set('Falha na conexao');
    mockTotalAulasSignal.set(0);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.alert-error')).toBeTruthy();
    expect(compiled.querySelector('.timetable-grid')).toBeNull();
    expect(compiled.querySelector('.empty-box')).toBeNull();
  });

  it('deve desabilitar botao de retry quando isLoading for true', () => {
    mockErrorMessageSignal.set('Erro na rede');
    mockIsLoadingSignal.set(true);
    fixture.detectChanges();

    const btnRetry = fixture.nativeElement.querySelector('.btn-retry') as HTMLButtonElement;
    expect(btnRetry.disabled).toBeTrue();
    expect(btnRetry.textContent).toContain('Carregando...');
  });

  it('deve exibir fallback Docente a definir quando professor_nome for nulo', () => {
    const aulaSemProf: HorarioMeu[] = [{ ...mockAulas[0], professor_nome: null }];
    mockHorariosSignal.set(aulaSemProf);
    mockTotalAulasSignal.set(1);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Docente: A definir');
  });

  it('deve incluir coluna de domingo quando houver aula no dia 6', () => {
    const aulaDomingo: HorarioMeu[] = [{ ...mockAulas[0], dia_semana: 6 }];
    mockHorariosSignal.set(aulaDomingo);
    mockTotalAulasSignal.set(1);
    fixture.detectChanges();

    const colunas = fixture.nativeElement.querySelectorAll('.dia-coluna');
    expect(colunas.length).toBe(7);
    expect(fixture.nativeElement.textContent).toContain('Domingo');
  });

  it('deve formatar intervalo com fallback e padding defensivo', () => {
    expect(component.formatarIntervalo('8:00', '10:00')).toBe('08:00 - 10:00');
    expect(component.formatarIntervalo('08:00:00', '10:00:00')).toBe('08:00 - 10:00');
    expect(component.formatarIntervalo('08:00', null)).toBe('A partir de 08:00');
    expect(component.formatarIntervalo(null, '10:00')).toBe('Ate 10:00');
    expect(component.formatarIntervalo(null, null)).toBe('Horario a definir');
    expect(component.formatarHorario('08:00:00')).toBe('08:00');
  });

  it('deve acionar recarregar ao clicar no botao do cabecalho', () => {
    fixture.detectChanges();
    const btn = fixture.nativeElement.querySelector('.grade-actions button') as HTMLButtonElement;
    btn.click();
    expect(mockHorarioService.carregarMeusHorarios).toHaveBeenCalledTimes(2);
  });
});
