import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot } from '@angular/router';
import { roleGuard } from './role.guard';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';

describe('Guards de Autenticacao e Perfil', () => {
  let auth: AuthService, router: { createUrlTree: jasmine.Spy };
  beforeEach(() => {
    router = { createUrlTree: jasmine.createSpy('createUrlTree').and.callFake((c: string[]) => c.join('/')) };
    TestBed.configureTestingModule({ providers: [AuthService, { provide: Router, useValue: router }] });
    auth = TestBed.inject(AuthService);
  });
  it('authGuard permite autenticado e bloqueia nulo', () => {
    expect(TestBed.runInInjectionContext(() => authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot))).not.toBeTrue();
    auth.setRole('admin');
    expect(TestBed.runInInjectionContext(() => authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot))).toBeTrue();
  });
  it('roleGuard bloqueia nao autenticado ou sem role', () => {
    const route = { data: { role: 'admin' } } as unknown as ActivatedRouteSnapshot;
    TestBed.runInInjectionContext(() => roleGuard(route, {} as RouterStateSnapshot));
    expect(router.createUrlTree).toHaveBeenCalledWith(['/login']);
    auth.setRole('admin');
    TestBed.runInInjectionContext(() => roleGuard({ data: {} } as unknown as ActivatedRouteSnapshot, {} as RouterStateSnapshot));
    expect(router.createUrlTree).toHaveBeenCalledWith(['/login']);
  });
  it('roleGuard permite role correspondente ou coordenador', () => {
    const route = { data: { role: 'admin' } } as unknown as ActivatedRouteSnapshot;
    auth.setRole('admin');
    expect(TestBed.runInInjectionContext(() => roleGuard(route, {} as RouterStateSnapshot))).toBeTrue();
    auth.setRole('coordenador');
    expect(TestBed.runInInjectionContext(() => roleGuard(route, {} as RouterStateSnapshot))).toBeTrue();
  });
  it('roleGuard redireciona quando divergente', () => {
    auth.setRole('professor');
    TestBed.runInInjectionContext(() => roleGuard({ data: { role: 'admin' } } as unknown as ActivatedRouteSnapshot, {} as RouterStateSnapshot));
    expect(router.createUrlTree).toHaveBeenCalledWith(['/professor']);
  });
});
