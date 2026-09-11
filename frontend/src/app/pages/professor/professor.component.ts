import { Component } from '@angular/core';
import { GradeHorariaComponent } from '../grade-horaria/grade-horaria.component';

@Component({
  selector: 'app-professor',
  standalone: true,
  imports: [GradeHorariaComponent],
  template: `
    <app-grade-horaria
      titulo="Painel do Docente"
      subtitulo="Grade semanal de aulas ministradas e salas alocadas no campus"
      perfil="professor"
    />
  `,
})
export class ProfessorComponent {}
