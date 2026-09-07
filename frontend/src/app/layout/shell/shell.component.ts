import { Component, inject } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet],
  template: `<div class="shell-layout"><header class="shell-header"><div class="header-brand"><span class="brand-title">SIGAAS</span><span class="brand-sub">Gestao Academica</span></div><div class="header-user"><span class="role-badge">Perfil: {{ authService.currentRole() }}</span><button type="button" class="btn-logout" (click)="sair()">Sair</button></div></header><main class="shell-content"><router-outlet /></main></div>`
})
export class ShellComponent {
  readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  sair(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
