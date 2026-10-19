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
    <div class="login-box">
      <h2>SIGAAS - Acesso ao Sistema</h2>
      <p class="desc">Sistema Integrado de Gestao de Salas e Escalas</p>

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
            maxlength="255"
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
            maxlength="72"
            placeholder="Digite sua senha"
            class="form-control"
            [disabled]="isLoading()"
          />
        </div>

        <button type="submit" class="btn-submit" [disabled]="isLoading() || !email || !senha">
          {{ isLoading() ? 'Autenticando...' : 'Entrar no Sistema' }}
        </button>
      </form>

      <div class="demo-sep">Atalhos de Demonstracao</div>
      <div class="roles-list">
        @for (acc of demoAccounts; track acc.id) {
          <button
            type="button"
            class="btn-role"
            (click)="fillAndLogin(acc)"
            [disabled]="isLoading()"
          >
            <strong>{{ acc.label }}</strong>
            <small>{{ acc.email }}</small>
          </button>
        }
      </div>
    </div>
  `,
  // prettier-ignore
  styles: [`
    .alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; padding: 0.5rem; border-radius: 4px; font-size: 0.8125rem; margin-bottom: 0.75rem; }
    .login-form, .form-group { display: flex; flex-direction: column; gap: 0.75rem; }
    .form-group { gap: 0.25rem; }
    .form-group label { font-size: 0.8125rem; font-weight: 600; color: #334155; }
    .form-control { padding: 0.5rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 0.875rem; }
    .btn-submit { margin-top: 0.25rem; padding: 0.5rem; background: #0f172a; color: #fff; font-weight: 600; border: none; border-radius: 4px; cursor: pointer; }
    .btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
    .demo-sep { margin-top: 1.25rem; padding-top: 0.75rem; border-top: 1px solid #e2e8f0; font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 600; }
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
    const target = role === 'coordenador' ? 'admin' : role;
    this.router.navigate([`/${target}`]);
  }

  onSubmit(): void {
    if (!this.email || !this.senha || this.isLoading()) {
      return;
    }
    this.executeLogin(this.email, this.senha);
  }

  fillAndLogin(account: DemoAccount): void {
    if (this.isLoading()) {
      return;
    }
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
        const target = res.usuario.perfil === 'coordenador' ? 'admin' : res.usuario.perfil;
        this.router.navigate([`/${target}`]);
      },
      error: (err) => {
        this.isLoading.set(false);
        const detail = err.error?.detail;
        if (Array.isArray(detail)) {
          this.errorMessage.set(
            detail.map((d: { msg?: string }) => d.msg || 'Erro de validacao').join(', '),
          );
        } else {
          this.errorMessage.set(
            typeof detail === 'string'
              ? detail
              : 'Falha na autenticacao. Verifique suas credenciais.',
          );
        }
      },
    });
  }
}
