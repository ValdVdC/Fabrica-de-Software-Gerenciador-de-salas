import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService, UserRole } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  template: `<div class="login-box"><h2>SIGAAS - Acesso</h2><p class="desc">Selecione o perfil institucional</p><div class="roles-list">@for (role of roles; track role.id) {<button type="button" class="btn-role" (click)="select(role.id)"><strong>{{ role.label }}</strong><small>{{ role.desc }}</small></button>}</div></div>`
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly roles: { id: UserRole; label: string; desc: string }[] = [
    { id: 'admin', label: 'Administrador / Coordenacao', desc: 'Gestao de campi e salas' },
    { id: 'secretaria', label: 'Secretaria Academica', desc: 'Gestao de turmas e ofertas' },
    { id: 'professor', label: 'Professor', desc: 'Consulta de salas e horarios' },
    { id: 'aluno', label: 'Aluno', desc: 'Grade horaria individual' }
  ];
  select(role: UserRole): void {
    this.auth.setRole(role);
    this.router.navigate([`/${role}`]);
  }
}
