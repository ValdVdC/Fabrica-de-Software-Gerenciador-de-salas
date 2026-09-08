import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let authService: AuthService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AuthService,
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

  it('nao deve anexar header Authorization se usuario nao possui token', () => {
    spyOn(authService, 'getToken').and.returnValue(null);

    http.get('/api/v1/campi').subscribe();

    const req = httpMock.expectOne('/api/v1/campi');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush([]);
  });
});
