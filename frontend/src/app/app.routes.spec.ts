import { routes } from './app.routes';

describe('Rotas Principais', () => {
  it('define login, rota protegida por shell e rotas filhas', () => {
    expect(routes.find((r) => r.path === 'login')).toBeDefined();
    const shell = routes.find((r) => r.path === '');
    expect(shell?.canActivate?.length).toBeGreaterThan(0);
    const children = shell?.children || [];
    ['admin', 'secretaria', 'professor', 'aluno'].forEach((role) => {
      expect(children.find((r) => r.path === role)?.data?.['role']).toBe(role);
    });
    expect(routes.find((r) => r.path === '**')?.redirectTo).toBe('login');
  });
});
