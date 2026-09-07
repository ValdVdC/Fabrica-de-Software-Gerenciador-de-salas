import { Component } from '@angular/core';

@Component({
  selector: 'app-aluno',
  standalone: true,
  template: `<div class="panel-card">
    <h2>Painel do Discente</h2>
    <p class="desc">Consulta de grade horaria individual e salas no campus.</p>
    <span class="badge">Ativo</span>
  </div>`,
})
export class AlunoComponent {}
