import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AdminComponent } from './admin.component';
import { AdminService, Sala, Equipamento } from '../../services/admin.service';
import { AuthService, UserSummary } from '../../services/auth.service';
import { AlocacaoService, MetricasAlocacao, AlocacaoItem } from '../../services/alocacao.service';
import { of, throwError } from 'rxjs';
import { signal } from '@angular/core';

describe('AdminComponent', () => {
  let component: AdminComponent;
  let fixture: ComponentFixture<AdminComponent>;
  let adminServiceSpy: jasmine.SpyObj<AdminService>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let alocacaoServiceSpy: jasmine.SpyObj<AlocacaoService>;

  // prettier-ignore
  const mockSalas = signal<Sala[]>([
    { id: 1, campus_id: 2, bloco: 'A', numero: '101', tipo: 'regular', capacidade: 40, turnos_disponiveis: ['matutino'], ativo: true },
  ]);
  const mockEquipamentos = signal<Equipamento[]>([
    { id: 10, nome: 'Projetor HD', descricao: 'Sala de aula', created_at: '2026-03-01T10:00:00Z' },
  ]);
  // prettier-ignore
  const mockCurrentUser = signal<UserSummary | null>({ id: 1, nome: 'Admin Master', email: 'admin@ufma.br', perfil: 'admin', campus_id: 2 });
  const mockLoading = signal(false);

  const mockAlocacaoLoading = signal(false);
  const mockAlocacaoError = signal<string | null>(null);
  const mockAlocacaoSucesso = signal<string | null>(null);
  const mockMetricas = signal<MetricasAlocacao | null>(null);
  const mockAlocacoes = signal<AlocacaoItem[]>([]);

  beforeEach(async () => {
    mockLoading.set(false);
    mockCurrentUser.set({
      id: 1,
      nome: 'Admin Master',
      email: 'admin@ufma.br',
      perfil: 'admin',
      campus_id: 2,
    });
    mockAlocacaoLoading.set(false);
    mockAlocacaoError.set(null);
    mockAlocacaoSucesso.set(null);
    mockMetricas.set(null);
    mockAlocacoes.set([]);

    adminServiceSpy = jasmine.createSpyObj(
      'AdminService',
      [
        'listarSalas',
        'listarEquipamentos',
        'criarSala',
        'criarEquipamento',
        'atualizarSala',
        'excluirSala',
        'associarEquipamento',
      ],
      {
        salas: mockSalas.asReadonly(),
        equipamentos: mockEquipamentos.asReadonly(),
        errorMessage: signal<string | null>(null).asReadonly(),
        isLoading: mockLoading.asReadonly(),
      },
    );

    authServiceSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser: mockCurrentUser.asReadonly(),
    });

    alocacaoServiceSpy = jasmine.createSpyObj(
      'AlocacaoService',
      ['otimizarAlocacao', 'executarBenchmark', 'limparMensagens'],
      {
        isLoading: mockAlocacaoLoading.asReadonly(),
        errorMessage: mockAlocacaoError.asReadonly(),
        sucessoMessage: mockAlocacaoSucesso.asReadonly(),
        metricas: mockMetricas.asReadonly(),
        alocacoes: mockAlocacoes.asReadonly(),
      },
    );

    adminServiceSpy.listarSalas.and.returnValue(of(mockSalas()));
    adminServiceSpy.listarEquipamentos.and.returnValue(of(mockEquipamentos()));

    await TestBed.configureTestingModule({
      imports: [AdminComponent],
      providers: [
        { provide: AdminService, useValue: adminServiceSpy },
        { provide: AuthService, useValue: authServiceSpy },
        { provide: AlocacaoService, useValue: alocacaoServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('deve inicializar com salas e equipamentos carregados e campus do usuario', () => {
    expect(component).toBeTruthy();
    expect(component.campusId).toBe(2);
    expect(adminServiceSpy.listarSalas).toHaveBeenCalledWith(2);
    expect(adminServiceSpy.listarEquipamentos).toHaveBeenCalled();
    expect(component.abaAtiva()).toBe('salas');
    expect(component.totalSalas()).toBe(1);
    expect(component.capacidadeTotal()).toBe(40);
  });

  it('nao deve listar salas se usuario autenticado nao possuir campus valido', () => {
    mockCurrentUser.set({
      id: 2,
      nome: 'Admin Sem Campus',
      email: 'sem@campus.br',
      perfil: 'admin',
      campus_id: 0,
    });
    const localFixture = TestBed.createComponent(AdminComponent);
    const localComp = localFixture.componentInstance;
    adminServiceSpy.listarSalas.calls.reset();

    localComp.ngOnInit();
    expect(localComp.campusId).toBe(0);
    expect(adminServiceSpy.listarSalas).not.toHaveBeenCalled();
  });

  it('deve alternar entre as abas e limpar mensagens', () => {
    component.mensagemSucesso.set('Mensagem antiga');
    component.selecionarAba('equipamentos');
    expect(component.abaAtiva()).toBe('equipamentos');
    expect(component.mensagemSucesso()).toBeNull();

    component.selecionarAba('alocacao');
    expect(component.abaAtiva()).toBe('alocacao');

    component.selecionarAba('resumo');
    expect(component.abaAtiva()).toBe('resumo');
  });

  it('deve formatar corretamente os dias da semana segundo ISO 8601', () => {
    expect(component.formatarDiaSemana(0)).toBe('Segunda-feira');
    expect(component.formatarDiaSemana(1)).toBe('Terca-feira');
    expect(component.formatarDiaSemana(2)).toBe('Quarta-feira');
    expect(component.formatarDiaSemana(3)).toBe('Quinta-feira');
    expect(component.formatarDiaSemana(4)).toBe('Sexta-feira');
    expect(component.formatarDiaSemana(5)).toBe('Sabado');
    expect(component.formatarDiaSemana(6)).toBe('Domingo');
    expect(component.formatarDiaSemana(7)).toBe('Dia 7');
  });

  it('deve acionar alocacao inteligente via alocacaoService', () => {
    component.campusId = 2;
    component.formPeriodoLetivo = '2026.1';
    component.formMaxThreads = 4;
    component.formSalvarNoBanco = true;

    alocacaoServiceSpy.otimizarAlocacao.and.returnValue(
      of({
        sucesso: true,
        mensagem: 'Alocacao executada com sucesso.',
        metricas: {
          tempo_sequencial_ms: 18.0,
          tempo_paralelo_ms: 4.5,
          speedup: 4.0,
          eficiencia_pct: 100.0,
          fracao_amdahl: 1.0,
          threads: 4,
          total_turmas: 10,
          alocadas: 10,
          conflitos: 0,
        },
        alocacoes: [],
      }),
    );

    component.executarAlocacao();

    expect(alocacaoServiceSpy.otimizarAlocacao).toHaveBeenCalledWith({
      periodo_letivo: '2026.1',
      campus_id: 2,
      max_threads: 4,
      salvar_no_banco: true,
    });
  });

  it('deve acionar benchmark cientifico via alocacaoService', () => {
    component.formMaxThreads = 4;
    alocacaoServiceSpy.executarBenchmark.and.returnValue(
      of({
        cenario: 'medio',
        num_turmas: 100,
        num_salas: 40,
        metricas: {
          tempo_sequencial_ms: 19.0,
          tempo_paralelo_ms: 5.0,
          speedup: 3.8,
          eficiencia_pct: 95.0,
          fracao_amdahl: 0.98,
          threads: 4,
          total_turmas: 100,
          alocadas: 99,
          conflitos: 1,
        },
      }),
    );

    component.executarBenchmark('medio');

    expect(alocacaoServiceSpy.executarBenchmark).toHaveBeenCalledWith({
      cenario: 'medio',
      threads: 4,
    });
  });

  it('deve cadastrar nova sala com sucesso e limpar formulario', () => {
    const novaSala: Sala = {
      id: 2,
      campus_id: 2,
      bloco: 'B',
      numero: '202',
      tipo: 'laboratorio',
      capacidade: 30,
      turnos_disponiveis: ['matutino', 'vespertino', 'noturno'],
      ativo: true,
    };
    adminServiceSpy.criarSala.and.returnValue(of(novaSala));

    component.campusId = 2;
    component.formBloco = 'B';
    component.formNumero = '202';
    component.formTipo = 'laboratorio';
    component.formCapacidade = 30;
    component.cadastrarSala();

    expect(adminServiceSpy.criarSala).toHaveBeenCalledWith({
      campus_id: 2,
      bloco: 'B',
      numero: '202',
      tipo: 'laboratorio',
      capacidade: 30,
      turnos_disponiveis: ['matutino', 'vespertino', 'noturno'],
    });
    expect(component.mensagemSucesso()).toContain('Sala B - 202 cadastrada com sucesso.');
    expect(component.formBloco).toBe('');
    expect(component.formNumero).toBe('');
  });

  it('deve cadastrar novo equipamento no catalogo institucional', () => {
    const novoEquip: Equipamento = {
      id: 15,
      nome: 'Projetor 4K',
      descricao: 'Para auditorio',
      created_at: '2026-03-02T12:00:00Z',
    };
    adminServiceSpy.criarEquipamento.and.returnValue(of(novoEquip));

    component.formEquipNome = 'Projetor 4K';
    component.formEquipDesc = 'Para auditorio';
    component.cadastrarEquipamento();

    expect(adminServiceSpy.criarEquipamento).toHaveBeenCalledWith({
      nome: 'Projetor 4K',
      descricao: 'Para auditorio',
    });
    expect(component.mensagemSucesso()).toContain(
      "Equipamento 'Projetor 4K' cadastrado com sucesso.",
    );
    expect(component.formEquipNome).toBe('');
  });

  it('deve atualizar sala em edicao com sucesso', () => {
    const salaAlvo: Sala = {
      id: 10,
      campus_id: 2,
      bloco: 'C',
      numero: '301',
      tipo: 'auditorio',
      capacidade: 100,
      turnos_disponiveis: ['noturno'],
      ativo: true,
    };
    const salaAtualizada: Sala = { ...salaAlvo, capacidade: 150, tipo: 'regular' };
    adminServiceSpy.atualizarSala.and.returnValue(of(salaAtualizada));

    component.iniciarEdicao(salaAlvo);
    component.formEditCapacidade = 150;
    component.formEditTipo = 'regular';
    component.salvarEdicao();

    expect(adminServiceSpy.atualizarSala).toHaveBeenCalledWith(10, {
      bloco: 'C',
      numero: '301',
      tipo: 'regular',
      capacidade: 150,
    });
    expect(component.mensagemSucesso()).toContain('Sala C - 301 atualizada com sucesso.');
    expect(component.salaEmEdicao()).toBeNull();
  });

  it('deve excluir sala com sucesso e fechar edicao caso a sala excluida estivesse em edicao', () => {
    // prettier-ignore
    const salaAlvo: Sala = { id: 15, campus_id: 2, bloco: 'D', numero: '401', tipo: 'laboratorio', capacidade: 25, turnos_disponiveis: ['vespertino'], ativo: true };
    adminServiceSpy.excluirSala.and.returnValue(of(void 0));

    component.iniciarEdicao(salaAlvo);
    component.excluirSala(salaAlvo);

    expect(adminServiceSpy.excluirSala).toHaveBeenCalledWith(15);
    expect(component.mensagemSucesso()).toContain('Sala D - 401 excluida com sucesso.');
    expect(component.salaEmEdicao()).toBeNull();
  });

  it('deve vincular equipamento a sala com sucesso', () => {
    adminServiceSpy.associarEquipamento.and.returnValue(
      of({ sala_id: 1, equipamento_id: 10, quantidade: 3 }),
    );
    component.formAssocSalaId = 1;
    component.formAssocEquipId = 10;
    component.formAssocQtd = 3;
    component.vincularEquipamento();

    expect(adminServiceSpy.associarEquipamento).toHaveBeenCalledWith(1, {
      equipamento_id: 10,
      quantidade: 3,
    });
    expect(component.mensagemSucesso()).toContain('Equipamento vinculado a sala com sucesso.');
    expect(component.formAssocSalaId).toBeNull();
    expect(component.formAssocEquipId).toBeNull();
  });
});
