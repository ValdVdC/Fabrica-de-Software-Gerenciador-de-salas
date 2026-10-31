import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { signal } from '@angular/core';
import { ShellComponent } from '../layout/shell/shell.component';
import { LoginComponent } from './login/login.component';
import { AlunoComponent } from './aluno/aluno.component';
import { AuthService } from '../services/auth.service';
import { SecretariaService, Matricula } from '../services/secretaria.service';
import { HorarioService } from '../services/horario.service';

describe('Componentes Shell, Login e Aluno', () => {
  let auth: AuthService, router: Router;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ShellComponent, LoginComponent],
      providers: [AuthService, provideRouter([])],
    }).compileComponents();
    auth = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
    spyOn(router, 'navigate');
  });
  it('deve deslogar no shell e redirecionar para login', () => {
    auth.setRole('admin');
    TestBed.createComponent(ShellComponent).componentInstance.sair();
    expect(auth.currentRole()).toBeNull();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });
  it('deve renderizar layout institucional limpo sem atalhos de demonstracao ou toggle de senha', () => {
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.login-box')).not.toBeNull();
    expect(el.querySelector('#email')).not.toBeNull();
    const senhaInput = el.querySelector('#senha') as HTMLInputElement;
    expect(senhaInput?.getAttribute('type')).toBe('password');
    const submitBtn = el.querySelector('.btn-submit') as HTMLButtonElement;
    expect(submitBtn?.textContent?.trim()).toBe('Entrar');
    expect(el.querySelector('.demo-sep')).toBeNull();
    expect(el.querySelector('.roles-list')).toBeNull();
    expect(el.querySelector('.btn-role')).toBeNull();
    expect(el.querySelector('.demo-accounts-panel')).toBeNull();
    expect(el.querySelector('.btn-toggle-eye')).toBeNull();
    expect(el.querySelector('.login-wrapper')).toBeNull();
  });
  it('deve exibir rotulos padronizados com icones SVG sobrios no shell e omitir menus restritos por perfil', () => {
    auth.setRole('admin');
    const fixture = TestBed.createComponent(ShellComponent);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;

    const getLinks = () =>
      Array.from(el.querySelectorAll('.nav-link')).map((a) => a.textContent?.trim());

    expect(el.querySelector('.user-avatar')).toBeNull();
    expect(getLinks()).toEqual(['Administracao', 'Dashboard', 'Relatorios', 'Historico']);
    expect(el.querySelector('.nav-link svg')).not.toBeNull();
    expect(el.querySelector('.btn-logout svg')).not.toBeNull();
    expect(el.querySelector('.role-badge')?.textContent?.trim()).toBe('Administrador');

    auth.setRole('coordenador');
    fixture.detectChanges();
    expect(getLinks()).toEqual(['Administracao', 'Dashboard', 'Relatorios', 'Historico']);

    auth.setRole('secretaria');
    fixture.detectChanges();
    expect(getLinks()).toEqual(['Secretaria Academica', 'Dashboard', 'Relatorios']);

    auth.setRole('professor');
    fixture.detectChanges();
    expect(getLinks()).toEqual(['Grade Horaria']);

    auth.setRole('aluno');
    fixture.detectChanges();
    expect(getLinks()).toEqual(['Grade Horaria']);
  });
  it('deve exibir e limpar banner de notificacao de acesso restrito no shell', () => {
    auth.setRole('secretaria');
    auth.notifyAccessDenied('Acesso restrito ao perfil');
    const fixture = TestBed.createComponent(ShellComponent);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const banner = el.querySelector('[data-testid="access-denied-banner"]');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('Acesso restrito ao perfil');

    const closeBtn = banner?.querySelector('button') as HTMLButtonElement;
    closeBtn.click();
    fixture.detectChanges();
    expect(el.querySelector('[data-testid="access-denied-banner"]')).toBeNull();
  });
});

describe('AlunoComponent - Cancelamento de Matricula e Feedback Visual', () => {
  const mockMatriculas = signal<Matricula[]>([
    { id: 100, aluno_id: 15, turma_id: 5, data_matricula: '2026-09-10', status: 'ativa' },
    { id: 101, aluno_id: 15, turma_id: 6, data_matricula: '2026-09-10', status: 'cancelada' },
  ]);
  let secretariaSpy: jasmine.SpyObj<SecretariaService>;
  let horarioSpy: jasmine.SpyObj<HorarioService>;

  beforeEach(async () => {
    secretariaSpy = jasmine.createSpyObj(
      'SecretariaService',
      ['listarMatriculas', 'cancelarMatricula', 'limparErro'],
      {
        matriculas: mockMatriculas.asReadonly(),
        isLoading: signal(false).asReadonly(),
        errorMessage: signal<string | null>(null).asReadonly(),
      },
    );
    secretariaSpy.listarMatriculas.and.returnValue(of(mockMatriculas()));
    secretariaSpy.cancelarMatricula.and.returnValue(
      of({ ...mockMatriculas()[0], status: 'cancelada' }),
    );

    horarioSpy = jasmine.createSpyObj(
      'HorarioService',
      ['carregarMeusHorarios', 'obterHorariosDoDia'],
      {
        horarios: signal([]).asReadonly(),
        totalAulas: signal(0).asReadonly(),
        disciplinasDistintas: signal([]).asReadonly(),
        isLoading: signal(false).asReadonly(),
        errorMessage: signal<string | null>(null).asReadonly(),
      },
    );
    horarioSpy.carregarMeusHorarios.and.returnValue(of([]));
    horarioSpy.obterHorariosDoDia.and.returnValue([]);

    await TestBed.configureTestingModule({
      imports: [AlunoComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: SecretariaService, useValue: secretariaSpy },
        { provide: HorarioService, useValue: horarioSpy },
      ],
    }).compileComponents();
  });

  it('deve listar matriculas proprias do aluno, permitir cancelamento de matricula ativa e exibir feedback visual', () => {
    const fixture = TestBed.createComponent(AlunoComponent);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;

    expect(secretariaSpy.listarMatriculas).toHaveBeenCalled();
    const btnAtiva = el.querySelector(
      '[data-testid="btn-aluno-cancelar-matricula-100"]',
    ) as HTMLButtonElement;
    const btnCancelada = el.querySelector('[data-testid="btn-aluno-cancelar-matricula-101"]');

    expect(btnAtiva).not.toBeNull();
    expect(btnCancelada).toBeNull();

    btnAtiva.click();
    fixture.detectChanges();

    expect(secretariaSpy.cancelarMatricula).toHaveBeenCalledWith(100);
    expect(horarioSpy.carregarMeusHorarios).toHaveBeenCalled();
    expect(el.textContent).toContain('Matricula #100 cancelada com sucesso.');
  });
  it('deve exibir e limpar banner de notificacao de acesso restrito no shell', () => {
    auth.setRole('secretaria');
    auth.notifyAccessDenied('Acesso restrito ao perfil');
    const fixture = TestBed.createComponent(ShellComponent);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const banner = el.querySelector('[data-testid="access-denied-banner"]');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('Acesso restrito ao perfil');

    const closeBtn = banner?.querySelector('button') as HTMLButtonElement;
    closeBtn.click();
    fixture.detectChanges();
    expect(el.querySelector('[data-testid="access-denied-banner"]')).toBeNull();
  });
});
