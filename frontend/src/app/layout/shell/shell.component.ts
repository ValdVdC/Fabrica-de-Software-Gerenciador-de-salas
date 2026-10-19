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
            <a routerLink="/admin" routerLinkActive="active" class="nav-link">Administracao</a>
          } @else if (authService.currentRole() === 'secretaria') {
            <a routerLink="/secretaria" routerLinkActive="active" class="nav-link"
              >Secretaria Academica</a
            >
          } @else if (authService.currentRole() === 'professor') {
            <a routerLink="/professor" routerLinkActive="active" class="nav-link">Grade Horaria</a>
          } @else if (authService.currentRole() === 'aluno') {
            <a routerLink="/aluno" routerLinkActive="active" class="nav-link">Grade Horaria</a>
          }
        </nav>

        <div class="header-user">
          <span class="user-name">{{ authService.currentUser()?.nome || 'Usuario' }}</span>
          <span class="role-badge">{{ formatarPerfil(authService.currentRole()) }}</span>
          @if (authService.currentUser()?.campus_id; as campusId) {
            <span class="campus-badge">Campus #{{ campusId }}</span>
          }
          <button type="button" class="btn-logout" (click)="sair()">Sair</button>
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
