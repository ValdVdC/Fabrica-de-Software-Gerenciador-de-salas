import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }

  const expectedRole = route.data?.['role'] as string | string[] | undefined;
  const expectedRoles = route.data?.['roles'] as string[] | undefined;
  const roles =
    expectedRoles ??
    (Array.isArray(expectedRole) ? expectedRole : expectedRole ? [expectedRole] : []);
  if (roles.length === 0) {
    return router.createUrlTree(['/login']);
  }

  if (roles.some((r) => authService.hasRole(r))) {
    return true;
  }

  authService.notifyAccessDenied('Acesso restrito: rota exclusiva para perfis autorizados.');
  return router.createUrlTree([authService.getHomeRoute()]);
};
