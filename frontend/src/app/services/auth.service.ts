import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export type UserRole = 'admin' | 'coordenador' | 'secretaria' | 'professor' | 'aluno';

export interface UserSummary {
  id: number;
  nome: string;
  email: string;
  perfil: UserRole;
  campus_id: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  usuario: UserSummary;
}

export interface LoginPayload {
  email: string;
  senha: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient, { optional: true });
  private readonly _currentRole = signal<UserRole | null>(null);
  private readonly _currentUser = signal<UserSummary | null>(null);
  private readonly _token = signal<string | null>(null);

  readonly currentRole = this._currentRole.asReadonly();
  readonly currentUser = this._currentUser.asReadonly();
  readonly token = this._token.asReadonly();

  constructor() {
    this.restoreSession();
  }

  private restoreSession(): void {
    try {
      if (typeof localStorage !== 'undefined') {
        const storedToken = localStorage.getItem('sigaas_token');
        const storedUser = localStorage.getItem('sigaas_user');
        if (storedToken && storedUser) {
          const user = JSON.parse(storedUser) as UserSummary;
          this._token.set(storedToken);
          this._currentUser.set(user);
          this._currentRole.set(user.perfil);
        }
      }
    } catch {
      this.logout();
    }
  }

  login(payload: LoginPayload): Observable<TokenResponse> {
    if (!this.http) {
      throw new Error('HttpClient nao disponivel');
    }
    return this.http.post<TokenResponse>('/api/v1/auth/login', payload).pipe(
      tap((res) => {
        this._token.set(res.access_token);
        this._currentUser.set(res.usuario);
        this._currentRole.set(res.usuario.perfil);
        try {
          if (typeof localStorage !== 'undefined') {
            localStorage.setItem('sigaas_token', res.access_token);
            localStorage.setItem('sigaas_user', JSON.stringify(res.usuario));
          }
        } catch {
          // Ignora falha de persistencia em contextos com storage indisponivel
        }
      }),
    );
  }

  getToken(): string | null {
    return this._token();
  }

  isAuthenticated(): boolean {
    return Boolean(this._token() && this._currentRole());
  }

  hasRole(role: string): boolean {
    const curr = this._currentRole();
    return curr === role || (role === 'admin' && curr === 'coordenador');
  }

  setRole(role: UserRole | null): void {
    this._currentRole.set(role);
    if (role && !this._token()) {
      this._token.set(`session_${role}_token`);
    } else if (!role) {
      this._token.set(null);
    }
  }

  logout(): void {
    this._token.set(null);
    this._currentUser.set(null);
    this._currentRole.set(null);
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('sigaas_token');
        localStorage.removeItem('sigaas_user');
      }
    } catch {
      // Ignora falha de remocao em storage indisponivel
    }
  }
}
