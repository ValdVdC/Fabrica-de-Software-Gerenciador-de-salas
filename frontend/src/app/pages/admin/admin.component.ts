import { Component } from '@angular/core';

@Component({
  selector: 'app-admin',
  standalone: true,
  template: `<div class="panel-card">
    <h2>Painel da Administracao</h2>
    <p class="desc">Controle de campi, infraestrutura de salas e motor de alocacao.</p>
    <span class="badge">Ativo</span>
  </div>`,
})
export class AdminComponent {}
