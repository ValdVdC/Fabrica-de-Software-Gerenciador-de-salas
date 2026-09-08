import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService, UserRole } from '../../services/auth.service';

interface DemoAccount {
  id: UserRole;
  label: string;
  email: string;
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="login-wrapper">
      <div class="login-box">
        <div class="header-section">
          <h2>SIGAAS - Acesso ao Sistema</h2>
          <p class="desc">Sistema Integrado de Gestao de Salas e Escalas</p>
        </div>

        @if (errorMessage()) {
          <div class="alert-error" role="alert">{{ errorMessage() }}</div>
        }

        <form (ngSubmit)="onSubmit()" class="login-form">
          <div class="form-group">
            <label for="email">Email Institucional</label>
            <input
              id="email"
              type="email"
              name="email"
              [(ngModel)]="email"
              required
              placeholder="exemplo@sigaas.edu"
              class="form-control"
              [disabled]="isLoading()"
            />
          </div>

          <div class="form-group">
            <label for="senha">Senha</label>
            <input
              id="senha"
              type="password"
              name="senha"
              [(ngModel)]="senha"
              required
              placeholder="Digite sua senha"
              class="form-control"
              [disabled]="isLoading()"
            />
          </div>

          <button type="submit" class="btn-submit" [disabled]="isLoading() || !email || !senha">
            {{ isLoading() ? 'Autenticando...' : 'Entrar no Sistema' }}
          </button>
        </form>

        <div class="demo-section">
          <p class="demo-title">Atalhos de Demonstracao</p>
          <div class="roles-list">
            @for (acc of demoAccounts; track acc.id) {
              <button
                type="button"
                class="btn-demo"
                (click)="fillAndLogin(acc)"
                [disabled]="isLoading()"
              >
                <strong>{{ acc.label }}</strong>
                <small>{{ acc.email }}</small>
              </button>
            }
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .login-wrapper { display: flex; justify-content: center; align-items: center; min-height: 80vh; padding: 1.5rem; }
    .login-box { width: 100%; max-width: 420px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); padding: 2rem; }
    .header-section { text-align: center; margin-bottom: 1.5rem; }
    h2 { font-size: 1.25rem; font-weight: 700; color: #0f172a; margin: 0 0 0.25rem; }
    .desc { font-size: 0.875rem; color: #64748b; margin: 0; }
    .alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; padding: 0.75rem; border-radius: 6px; font-size: 0.875rem; margin-bottom: 1rem; }
    .login-form { display: flex; flex-direction: column; gap: 1rem; }
    .form-group { display: flex; flex-direction: column; gap: 0.25rem; text-align: left; }
    label { font-size: 0.8125rem; font-weight: 600; color: #334155; }
    .form-control { padding: 0.5rem 0.75rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.875rem; }
    .form-control:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
    .btn-submit { margin-top: 0.5rem; padding: 0.625rem; background: #0f172a; color: #fff; font-weight: 600; font-size: 0.875rem; border: none; border-radius: 6px; cursor: pointer; }
    .btn-submit:hover:not(:disabled) { background: #1e293b; }
    .btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
    .demo-section { margin-top: 1.5rem; padding-top: 1.25rem; border-top: 1px solid #f1f5f9; }
    .demo-title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 0.75rem; text-align: center; font-weight: 600; }
    .roles-list { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .btn-demo { display: flex; flex-direction: column; align-items: flex-start; padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 6px; background: #f8fafc; cursor: pointer; }
    .btn-demo:hover:not(:disabled) { background: #f1f5f9; border-color: #cbd5e1; }
    .btn-demo strong { font-size: 0.75rem; color: #1e293b; }
    .btn-demo small { font-size: 0.6875rem; color: #64748b; }
  `],
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  email = '';
  senha = '';
  readonly isLoading = signal(false);
  readonly errorMessage = signal<string | null>(null);

  readonly demoAccounts: DemoAccount[] = [
    { id: 'admin', label: 'Admin', email: 'admin@sigaas.edu' },
    { id: 'secretaria', label: 'Secretaria', email: 'secretaria@sigaas.edu' },
    { id: 'professor', label: 'Professor', email: 'professor@sigaas.edu' },
    { id: 'aluno', label: 'Aluno', email: 'aluno@sigaas.edu' },
  ];

  select(role: UserRole): void {
    this.auth.setRole(role);
    this.router.navigate([`/${role}`]);
  }

  onSubmit(): void {
    if (!this.email || !this.senha || this.isLoading()) {
      return;
    }
    this.executeLogin(this.email, this.senha);
  }

  fillAndLogin(account: DemoAccount): void {
    this.email = account.email;
    this.senha = 'sigaas123';
    this.executeLogin(this.email, this.senha);
  }

  private executeLogin(email: string, senha: string): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.auth.login({ email, senha }).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        this.router.navigate([`/${res.usuario.perfil}`]);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.detail || 'Falha na autenticacao. Verifique suas credenciais.');
      },
    });
  }
}
