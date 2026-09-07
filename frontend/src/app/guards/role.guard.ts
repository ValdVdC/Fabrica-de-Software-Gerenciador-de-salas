import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }

  const expectedRole = route.data?.['role'] as string | undefined;
  if (!expectedRole) {
    return router.createUrlTree(['/login']);
  }

  if (authService.hasRole(expectedRole)) {
    return true;
  }

  const userRole = authService.currentRole();
  return router.createUrlTree(userRole ? [`/${userRole}`] : ['/login']);
};
