import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AdminComponent } from './admin.component';
import { AdminService, Sala, Equipamento } from '../../services/admin.service';
import { AuthService, UserSummary } from '../../services/auth.service';
import { of, throwError } from 'rxjs';
import { signal } from '@angular/core';

describe('AdminComponent', () => {
  let component: AdminComponent;
  let fixture: ComponentFixture<AdminComponent>;
  let adminServiceSpy: jasmine.SpyObj<AdminService>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

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

  beforeEach(async () => {
    mockLoading.set(false);
    // prettier-ignore
    adminServiceSpy = jasmine.createSpyObj('AdminService', ['listarSalas', 'listarEquipamentos', 'criarSala', 'criarEquipamento'], {
      salas: mockSalas.asReadonly(), equipamentos: mockEquipamentos.asReadonly(),
      errorMessage: signal<string | null>(null).asReadonly(), isLoading: mockLoading.asReadonly(),
    });

    authServiceSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser: mockCurrentUser.asReadonly(),
    });
    adminServiceSpy.listarSalas.and.returnValue(of(mockSalas()));
    adminServiceSpy.listarEquipamentos.and.returnValue(of(mockEquipamentos()));

    await TestBed.configureTestingModule({
      imports: [AdminComponent],
      providers: [
        { provide: AdminService, useValue: adminServiceSpy },
        { provide: AuthService, useValue: authServiceSpy },
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
    const semCampusSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser: signal<UserSummary | null>(null).asReadonly(),
    });
    const localFixture = TestBed.createComponent(AdminComponent);
    localFixture.debugElement.injector.get(AuthService);
    (localFixture.componentInstance as any).authService = semCampusSpy;
    adminServiceSpy.listarSalas.calls.reset();

    localFixture.componentInstance.ngOnInit();

    expect(localFixture.componentInstance.campusId).toBe(0);
    expect(adminServiceSpy.listarSalas).not.toHaveBeenCalled();
  });

  it('deve alternar abas e limpar mensagem de sucesso', () => {
    component.mensagemSucesso.set('Mensagem teste');
    component.selecionarAba('equipamentos');
    expect(component.abaAtiva()).toBe('equipamentos');
    expect(component.mensagemSucesso()).toBeNull();
  });

  it('deve submeter criacao de sala e atualizar estado ao concluir com reset de tipo', () => {
    // prettier-ignore
    const novaSala: Sala = {
      id: 2, campus_id: 2, bloco: 'B', numero: '202', tipo: 'laboratorio', capacidade: 30, turnos_disponiveis: ['matutino'], ativo: true,
    };
    adminServiceSpy.criarSala.and.returnValue(of(novaSala));

    component.formBloco = 'B';
    component.formNumero = '202';
    component.formTipo = 'laboratorio';
    component.formCapacidade = 30.8;

    component.cadastrarSala();

    // prettier-ignore
    expect(adminServiceSpy.criarSala).toHaveBeenCalledWith(jasmine.objectContaining({
      campus_id: 2, bloco: 'B', numero: '202', tipo: 'laboratorio', capacidade: 30,
    }));
    expect(component.mensagemSucesso()).toContain('Sala B-202 cadastrada com sucesso!');
    expect(component.formBloco).toBe('');
    expect(component.formNumero).toBe('');
    expect(component.formTipo).toBe('regular');
    expect(component.formCapacidade).toBe(40);
  });

  it('deve submeter criacao de equipamento e atualizar estado ao concluir com descricao opcional', () => {
    // prettier-ignore
    const novoEq: Equipamento = { id: 11, nome: 'Notebook Dell', descricao: 'i7 16GB', created_at: '2026-03-01T10:00:00Z' };
    adminServiceSpy.criarEquipamento.and.returnValue(of(novoEq));

    component.formEquipNome = 'Notebook Dell';
    component.formEquipDesc = '   ';
    component.cadastrarEquipamento();

    expect(adminServiceSpy.criarEquipamento).toHaveBeenCalledWith({
      nome: 'Notebook Dell',
      descricao: undefined,
    });
    expect(component.mensagemSucesso()).toContain("Equipamento 'Notebook Dell' adicionado");
    expect(component.formEquipNome).toBe('');
  });

  it('nao deve submeter formularios quando adminService.isLoading for verdadeiro', () => {
    mockLoading.set(true);
    component.formBloco = 'C';
    component.formNumero = '303';
    component.cadastrarSala();
    expect(adminServiceSpy.criarSala).not.toHaveBeenCalled();

    component.formEquipNome = 'Cabo HDMI';
    component.cadastrarEquipamento();
    expect(adminServiceSpy.criarEquipamento).not.toHaveBeenCalled();
  });

  it('nao deve submeter formularios com campos vazios ou invalidos', () => {
    component.mensagemSucesso.set('Antigo');
    component.formBloco = '   ';
    component.formNumero = '';
    component.cadastrarSala();
    expect(adminServiceSpy.criarSala).not.toHaveBeenCalled();
    expect(component.mensagemSucesso()).toBeNull();

    component.formEquipNome = 'a';
    component.cadastrarEquipamento();
    expect(adminServiceSpy.criarEquipamento).not.toHaveBeenCalled();
  });

  it('nao deve submeter sala com capacidade invalida', () => {
    component.formBloco = 'A';
    component.formNumero = '101';
    component.formCapacidade = 0;
    component.cadastrarSala();
    component.formCapacidade = 5001;
    component.cadastrarSala();
    expect(adminServiceSpy.criarSala).not.toHaveBeenCalled();
  });

  it('deve manter formulario e nao exibir sucesso em caso de erro na API', () => {
    adminServiceSpy.criarSala.and.returnValue(throwError(() => new Error('Falha')));
    component.formBloco = 'A';
    component.formNumero = '101';
    component.cadastrarSala();
    expect(component.mensagemSucesso()).toBeNull();
    expect(component.formBloco).toBe('A');
  });
});
