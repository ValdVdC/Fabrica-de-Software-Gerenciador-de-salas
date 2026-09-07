import { AuthService } from './auth.service';

describe('AuthService', () => {
  it('gerencia ciclo de vida do perfil reativo com seguranca', () => {
    const service = new AuthService();
    expect(service.currentRole()).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
    service.setRole('coordenador');
    expect(service.hasRole('admin')).toBeTrue();
    expect(service.hasRole('aluno')).toBeFalse();
    service.logout();
    expect(service.isAuthenticated()).toBeFalse();
  });
});
