import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let authService: AuthService;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        { provide: Router, useValue: routerSpy },
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    authService = TestBed.inject(AuthService);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('deve anexar header Authorization Bearer em chamadas para a API protegida', () => {
    spyOn(authService, 'getToken').and.returnValue('mock_jwt_token_123');
    http.get('/api/v1/campi').subscribe();
    const req = httpMock.expectOne('/api/v1/campi');
    expect(req.request.headers.has('Authorization')).toBeTrue();
    expect(req.request.headers.get('Authorization')).toBe('Bearer mock_jwt_token_123');
    req.flush([]);
  });

  it('nao deve anexar header Authorization na rota de login', () => {
    spyOn(authService, 'getToken').and.returnValue('mock_jwt_token_123');
    http.post('/api/v1/auth/login', { email: 'a@b.com', senha: '123' }).subscribe();
    const req = httpMock.expectOne('/api/v1/auth/login');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('nao deve vazar token para urls externas contendo /api/v1/', () => {
    spyOn(authService, 'getToken').and.returnValue('mock_jwt_token_123');
    http.get('https://externo.com/api/v1/recurso').subscribe();
    const req = httpMock.expectOne('https://externo.com/api/v1/recurso');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('deve deslogar e redirecionar para /login em caso de status 401', () => {
    spyOn(authService, 'getToken').and.returnValue('mock_jwt_token_123');
    spyOn(authService, 'logout');
    http.get('/api/v1/salas').subscribe({ error: () => {} });
    const req = httpMock.expectOne('/api/v1/salas');
    req.flush('Sessao expirada', { status: 401, statusText: 'Unauthorized' });
    expect(authService.logout).toHaveBeenCalled();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('nao deve deslogar nem redirecionar em caso de status 403 Forbidden e deve notificar acesso restrito', () => {
    spyOn(authService, 'getToken').and.returnValue('mock_jwt_token_123');
    spyOn(authService, 'logout');
    http.post('/api/v1/usuarios', {}).subscribe({ error: () => {} });
    const req = httpMock.expectOne('/api/v1/usuarios');
    req.flush(
      { detail: 'Privilegio insuficiente para conceder este perfil' },
      { status: 403, statusText: 'Forbidden' },
    );
    expect(authService.logout).not.toHaveBeenCalled();
    expect(routerSpy.navigate).not.toHaveBeenCalled();
    expect(authService.accessDeniedMessage()).toBe(
      'Privilegio insuficiente para conceder este perfil',
    );
  });

  it('deve registrar mensagem padrao de acesso restrito quando status 403 nao possuir detail textual', () => {
    spyOn(authService, 'getToken').and.returnValue('mock_jwt_token_123');
    spyOn(authService, 'logout');
    http.patch('/api/v1/salas/1', {}).subscribe({ error: () => {} });
    const req = httpMock.expectOne('/api/v1/salas/1');
    req.flush('Forbidden', { status: 403, statusText: 'Forbidden' });
    expect(authService.logout).not.toHaveBeenCalled();
    expect(authService.accessDeniedMessage()).toContain('Acesso restrito');
  });
});
