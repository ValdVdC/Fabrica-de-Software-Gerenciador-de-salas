import { Component } from '@angular/core';
import { GradeHorariaComponent } from '../grade-horaria/grade-horaria.component';

@Component({
  selector: 'app-aluno',
  standalone: true,
  imports: [GradeHorariaComponent],
  template: `
    <app-grade-horaria
      titulo="Painel do Discente"
      subtitulo="Grade horaria semanal individual e localizacao de salas"
      perfil="aluno"
    />
  `,
})
export class AlunoComponent {}
