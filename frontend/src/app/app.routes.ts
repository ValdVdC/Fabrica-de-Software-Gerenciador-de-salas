import { Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login.component';
import { ShellComponent } from './layout/shell/shell.component';
import { AdminComponent } from './pages/admin/admin.component';
import { SecretariaComponent } from './pages/secretaria/secretaria.component';
import { ProfessorComponent } from './pages/professor/professor.component';
import { AlunoComponent } from './pages/aluno/aluno.component';
import { authGuard } from './guards/auth.guard';
import { roleGuard } from './guards/role.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      { path: 'admin', component: AdminComponent, canActivate: [roleGuard], data: { role: 'admin' } },
      { path: 'secretaria', component: SecretariaComponent, canActivate: [roleGuard], data: { role: 'secretaria' } },
      { path: 'professor', component: ProfessorComponent, canActivate: [roleGuard], data: { role: 'professor' } },
      { path: 'aluno', component: AlunoComponent, canActivate: [roleGuard], data: { role: 'aluno' } },
      { path: '', redirectTo: 'admin', pathMatch: 'full' }
    ]
  },
  { path: '**', redirectTo: 'login' }
];
