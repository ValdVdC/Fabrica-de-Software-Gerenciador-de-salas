import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { ShellComponent } from '../layout/shell/shell.component';
import { LoginComponent } from './login/login.component';
import { AuthService } from '../services/auth.service';

describe('Componentes Shell e Login', () => {
  let auth: AuthService, router: jasmine.SpyObj<Router>;
  beforeEach(async () => {
    router = jasmine.createSpyObj('Router', ['navigate']);
    await TestBed.configureTestingModule({
      imports: [ShellComponent, LoginComponent],
      providers: [AuthService, { provide: Router, useValue: router }],
    }).compileComponents();
    auth = TestBed.inject(AuthService);
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
});
