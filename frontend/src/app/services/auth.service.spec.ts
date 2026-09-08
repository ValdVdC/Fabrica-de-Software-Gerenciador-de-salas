import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthService, TokenResponse } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [AuthService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('gerencia ciclo de vida do perfil reativo com seguranca', () => {
    expect(service.currentRole()).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
    service.setRole('coordenador');
    expect(service.hasRole('admin')).toBeTrue();
    expect(service.hasRole('aluno')).toBeFalse();
    service.logout();
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('realiza login com sucesso e persiste sessao', () => {
    const mockResponse: TokenResponse = {
      access_token: 'fake_token_jwt',
      token_type: 'bearer',
      usuario: {
        id: 1,
        nome: 'Admin Teste',
        email: 'admin@sigaas.edu',
        perfil: 'admin',
        campus_id: 1,
      },
    };

    service.login({ email: 'admin@sigaas.edu', senha: '123' }).subscribe((res) => {
      expect(res.access_token).toBe('fake_token_jwt');
      expect(service.getToken()).toBe('fake_token_jwt');
      expect(service.currentRole()).toBe('admin');
      expect(service.currentUser()?.nome).toBe('Admin Teste');
      expect(localStorage.getItem('sigaas_token')).toBe('fake_token_jwt');
    });

    const req = httpMock.expectOne('/api/v1/auth/login');
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);
  });

  it('limpa estado e storage ao efetuar logout', () => {
    service.setRole('admin');
    localStorage.setItem('sigaas_token', 'token_teste');
    localStorage.setItem('sigaas_user', '{"id":1}');

    service.logout();

    expect(service.getToken()).toBeNull();
    expect(service.currentRole()).toBeNull();
    expect(service.currentUser()).toBeNull();
    expect(localStorage.getItem('sigaas_token')).toBeNull();
    expect(localStorage.getItem('sigaas_user')).toBeNull();
  });
});
