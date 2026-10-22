import { Component, inject } from '@angular/core';
import { Router, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService, UserRole } from '../../services/auth.service';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="shell-layout">
      <header class="shell-header">
        <div class="header-brand">
          <span class="brand-title">SIGAAS</span>
          <span class="brand-sub">Gestao Academica</span>
        </div>

        <nav class="header-nav" aria-label="Navegacao Principal">
          @if (
            authService.currentRole() === 'admin' || authService.currentRole() === 'coordenador'
          ) {
            <a routerLink="/admin" routerLinkActive="active" class="nav-link">
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect>
                <path d="M9 22v-4h6v4"></path>
                <path d="M8 6h.01"></path>
                <path d="M16 6h.01"></path>
                <path d="M8 10h.01"></path>
                <path d="M16 10h.01"></path>
              </svg>
              Administracao
            </a>
          } @else if (authService.currentRole() === 'secretaria') {
            <a routerLink="/secretaria" routerLinkActive="active" class="nav-link">
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path
                  d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"
                ></path>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
              </svg>
              Secretaria Academica
            </a>
          } @else if (authService.currentRole() === 'professor') {
            <a routerLink="/professor" routerLinkActive="active" class="nav-link">
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              Grade Horaria
            </a>
          } @else if (authService.currentRole() === 'aluno') {
            <a routerLink="/aluno" routerLinkActive="active" class="nav-link">
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              Grade Horaria
            </a>
          }
          @if (
            authService.currentRole() === 'admin' ||
            authService.currentRole() === 'coordenador' ||
            authService.currentRole() === 'secretaria'
          ) {
            <a routerLink="/relatorios" routerLinkActive="active" class="nav-link">
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
              </svg>
              Relatorios
            </a>
          }
        </nav>

        <div class="header-user">
          <span class="user-name">{{ authService.currentUser()?.nome || 'Usuario' }}</span>
          <span class="role-badge">{{ formatarPerfil(authService.currentRole()) }}</span>
          @if (authService.currentUser()?.campus_id; as campusId) {
            <span class="campus-badge">Campus #{{ campusId }}</span>
          }
          <button type="button" class="btn-logout" (click)="sair()">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            Sair
          </button>
        </div>
      </header>
      <main class="shell-content">
        <router-outlet />
      </main>
    </div>
  `,
})
export class ShellComponent {
  readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  formatarPerfil(perfil: UserRole | null): string {
    switch (perfil) {
      case 'admin':
        return 'Administrador';
      case 'coordenador':
        return 'Coordenador';
      case 'secretaria':
        return 'Secretaria';
      case 'professor':
        return 'Docente';
      case 'aluno':
        return 'Discente';
      default:
        return 'Convidado';
    }
  }

  sair(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
