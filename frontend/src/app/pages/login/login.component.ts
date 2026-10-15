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
      <div class="login-container">
        <div class="login-box">
          <div class="login-brand-header">
            <h2>SIGAAS - Acesso ao Sistema</h2>
            <p class="desc">Sistema Integrado de Gestao de Salas e Escalas</p>
          </div>

          @if (errorMessage()) {
            <div class="alert alert-error" role="alert">{{ errorMessage() }}</div>
          }

          <form (ngSubmit)="onSubmit()" class="login-form">
            <div class="form-group">
              <div class="input-icon-wrapper">
                <span class="input-left-icon" aria-hidden="true">
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <rect width="20" height="16" x="2" y="4" rx="2"></rect>
                    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                  </svg>
                </span>
                <input
                  id="email"
                  type="email"
                  name="email"
                  [(ngModel)]="email"
                  required
                  maxlength="255"
                  placeholder="Email Institucional"
                  aria-label="Email Institucional"
                  class="form-input login-input-with-icon"
                  [disabled]="isLoading()"
                />
              </div>
            </div>

            <div class="form-group">
              <div class="input-icon-wrapper">
                <span class="input-left-icon" aria-hidden="true">
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                  </svg>
                </span>
                <input
                  id="senha"
                  [type]="mostrarSenha() ? 'text' : 'password'"
                  name="senha"
                  [(ngModel)]="senha"
                  required
                  maxlength="72"
                  placeholder="Senha"
                  aria-label="Senha"
                  class="form-input login-input-with-icon login-input-with-right-icon"
                  [disabled]="isLoading()"
                />
                <button
                  type="button"
                  class="btn-toggle-eye"
                  (click)="alternarMostrarSenha()"
                  [attr.aria-label]="mostrarSenha() ? 'Ocultar senha' : 'Exibir senha'"
                  [title]="mostrarSenha() ? 'Ocultar senha' : 'Exibir senha'"
                >
                  @if (mostrarSenha()) {
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path>
                      <path
                        d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"
                      ></path>
                      <path
                        d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"
                      ></path>
                      <line x1="2" y1="2" x2="22" y2="22"></line>
                    </svg>
                  } @else {
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  }
                </button>
              </div>
            </div>

            <button
              type="submit"
              class="btn-primary login-btn-submit"
              [disabled]="isLoading() || !email || !senha"
            >
              {{ isLoading() ? 'Autenticando...' : 'Entrar no Sistema' }}
            </button>
          </form>
        </div>

        <div class="demo-accounts-panel">
          <div class="demo-accounts-header">
            <span class="demo-accounts-title">Perfis de Acesso Rapido</span>
            <span class="demo-accounts-sub">Selecione uma conta para demonstracao direta</span>
          </div>
          <div class="demo-accounts-grid">
            @for (acc of demoAccounts; track acc.id) {
              <button
                type="button"
                class="btn-demo-pill"
                (click)="fillAndLogin(acc)"
                [disabled]="isLoading()"
              >
                <span class="demo-pill-label">{{ acc.label }}</span>
                <span class="demo-pill-email tabular-nums">{{ acc.email }}</span>
              </button>
            }
          </div>
        </div>
      </div>
    </div>
  `,
  // prettier-ignore
  styles: [`
    .login-wrapper {
      min-height: 100vh;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2.5rem 1.25rem;
      background:
        linear-gradient(
          135deg,
          rgba(15, 23, 42, 0.88) 0%,
          rgba(30, 41, 59, 0.82) 50%,
          rgba(15, 23, 42, 0.94) 100%
        ),
        url('/sigaas-bg.avif') center center / cover no-repeat fixed;
      box-sizing: border-box;
    }
    .login-container {
      max-width: 480px;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .login-box {
      width: 100%;
      margin: 0;
      padding: 2.25rem;
      background: #ffffff;
      border: 1px solid rgba(226, 232, 240, 0.95);
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.25), 0 8px 10px -6px rgba(0, 0, 0, 0.2);
      border-radius: 8px;
    }
    .login-brand-header {
      margin-bottom: 1.5rem;
      text-align: left;
    }
    .login-brand-header h2 {
      margin: 0;
      font-size: 1.35rem;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.01em;
    }
    .login-brand-header .desc {
      margin: 0.35rem 0 0;
      font-size: 0.8125rem;
      color: #64748b;
      line-height: 1.45;
    }
    .login-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .input-icon-wrapper {
      position: relative;
      display: flex;
      align-items: center;
      width: 100%;
    }
    .input-left-icon {
      position: absolute;
      left: 1rem;
      top: 50%;
      transform: translateY(-50%);
      color: #64748b;
      pointer-events: none;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .form-input {
      height: 48px;
      box-sizing: border-box;
      width: 100%;
      font-size: 0.875rem;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      color: #0f172a;
      background: #ffffff;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .form-input:focus {
      border-color: #252ceb;
      box-shadow: 0 0 0 3px rgba(37, 44, 235, 0.15);
      outline: none;
    }
    .login-input-with-icon {
      padding-left: 2.85rem;
      padding-right: 1rem;
    }
    .login-input-with-right-icon {
      padding-right: 2.85rem;
    }
    .btn-toggle-eye {
      position: absolute;
      right: 0.5rem;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      cursor: pointer;
      color: #64748b;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border-radius: 4px;
      transition: color 0.15s ease, background-color 0.15s ease;
    }
    .btn-toggle-eye:hover {
      color: #0f172a;
      background-color: #f1f5f9;
    }
    .login-btn-submit {
      height: 48px;
      width: 100%;
      margin-top: 0.25rem;
      font-size: 0.875rem;
      font-weight: 600;
      border-radius: 6px;
    }
    .demo-accounts-panel {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 1.15rem 1.25rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15);
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      box-sizing: border-box;
    }
    .demo-accounts-header {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }
    .demo-accounts-title {
      font-size: 0.6875rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #475569;
    }
    .demo-accounts-sub {
      font-size: 0.75rem;
      color: #64748b;
    }
    .demo-accounts-grid {
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .btn-demo-pill {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.55rem 0.85rem;
      border: 1px solid #e2e8f0;
      border-radius: 5px;
      background: #f8fafc;
      cursor: pointer;
      transition: all 0.15s ease-in-out;
      text-align: left;
    }
    .btn-demo-pill:hover:not(:disabled) {
      background: #f1f5f9;
      border-color: #4f46e5;
    }
    .btn-demo-pill:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .demo-pill-label {
      font-size: 0.8125rem;
      font-weight: 600;
      color: #0f172a;
    }
    .demo-pill-email {
      font-size: 0.75rem;
      color: #64748b;
      font-family: monospace;
    }
  `],
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  email = '';
  senha = '';
  readonly isLoading = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly mostrarSenha = signal(false);

  readonly demoAccounts: DemoAccount[] = [
    { id: 'admin', label: 'Administrador Geral', email: 'admin@sigaas.edu' },
    { id: 'coordenador', label: 'Coordenacao de Curso', email: 'coord.cc@sigaas.edu' },
    { id: 'secretaria', label: 'Secretaria Academica', email: 'secretaria@sigaas.edu' },
    { id: 'professor', label: 'Docente', email: 'professor@sigaas.edu' },
    { id: 'aluno', label: 'Discente', email: 'aluno@sigaas.edu' },
  ];

  alternarMostrarSenha(): void {
    this.mostrarSenha.update((v) => !v);
  }

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
