import { Component } from '@angular/core';

@Component({
  selector: 'app-professor',
  standalone: true,
  template: `<div class="panel-card">
    <h2>Painel do Docente</h2>
    <p class="desc">Consulta de salas alocadas, grade de aulas e notificacoes.</p>
    <span class="badge">Ativo</span>
  </div>`,
})
export class ProfessorComponent {}
