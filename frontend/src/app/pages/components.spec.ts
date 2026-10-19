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
  it('deve alternar perfil no login e navegar', () => {
    TestBed.createComponent(LoginComponent).componentInstance.select('professor');
    expect(auth.currentRole()).toBe('professor');
    expect(router.navigate).toHaveBeenCalledWith(['/professor']);
  });
  it('deve exibir rotulos padronizados no shell e omitir avatar cosmetico', () => {
    auth.setRole('admin');
    const fixture = TestBed.createComponent(ShellComponent);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;

    expect(el.querySelector('.user-avatar')).toBeNull();
    expect(el.querySelector('.nav-link')?.textContent?.trim()).toBe('Administracao');
    expect(el.querySelector('.role-badge')?.textContent?.trim()).toBe('Administrador');

    auth.setRole('professor');
    fixture.detectChanges();
    expect(el.querySelector('.nav-link')?.textContent?.trim()).toBe('Grade Horaria');

    auth.setRole('aluno');
    fixture.detectChanges();
    expect(el.querySelector('.nav-link')?.textContent?.trim()).toBe('Grade Horaria');
  });
});
