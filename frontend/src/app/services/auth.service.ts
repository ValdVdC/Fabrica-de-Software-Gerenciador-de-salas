import { Injectable, signal } from '@angular/core';

export type UserRole = 'admin' | 'coordenador' | 'secretaria' | 'professor' | 'aluno';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly _currentRole = signal<UserRole | null>(null);
  readonly currentRole = this._currentRole.asReadonly();

  isAuthenticated(): boolean {
    return this._currentRole() !== null;
  }

  hasRole(role: string): boolean {
    const curr = this._currentRole();
    return curr === role || (role === 'admin' && curr === 'coordenador');
  }

  setRole(role: UserRole | null): void {
    this._currentRole.set(role);
  }

  logout(): void {
    this._currentRole.set(null);
  }
}
