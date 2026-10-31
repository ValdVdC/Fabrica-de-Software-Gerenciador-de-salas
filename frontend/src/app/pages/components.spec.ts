import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { ShellComponent } from '../layout/shell/shell.component';
import { LoginComponent } from './login/login.component';
import { AuthService } from '../services/auth.service';

describe('Componentes Shell e Login', () => {
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
  it('deve exibir rotulos padronizados com icones SVG sobrios no shell e omitir avatar cosmetico', () => {
    auth.setRole('admin');
    const fixture = TestBed.createComponent(ShellComponent);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;

    expect(el.querySelector('.user-avatar')).toBeNull();
    expect(el.querySelector('.nav-link')?.textContent?.trim()).toBe('Administracao');
    expect(el.querySelector('.nav-link svg')).not.toBeNull();
    expect(el.querySelector('.btn-logout svg')).not.toBeNull();
    expect(el.querySelector('.role-badge')?.textContent?.trim()).toBe('Administrador');

    auth.setRole('professor');
    fixture.detectChanges();
    expect(el.querySelector('.nav-link')?.textContent?.trim()).toBe('Grade Horaria');
    expect(el.querySelector('.nav-link svg')).not.toBeNull();

    auth.setRole('aluno');
    fixture.detectChanges();
    expect(el.querySelector('.nav-link')?.textContent?.trim()).toBe('Grade Horaria');
    expect(el.querySelector('.nav-link svg')).not.toBeNull();
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
