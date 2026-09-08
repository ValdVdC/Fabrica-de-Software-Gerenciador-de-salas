import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface Sala {
  id: number;
  campus_id: number;
  bloco: string;
  numero: string;
  tipo: 'regular' | 'laboratorio' | 'auditorio' | 'reuniao';
  capacidade: number;
  turnos_disponiveis: string[];
  ativo: boolean;
}

export interface SalaCreate {
  campus_id: number;
  bloco: string;
  numero: string;
  tipo: string;
  capacidade: number;
  turnos_disponiveis: string[];
}

export interface Equipamento {
  id: number;
  nome: string;
  descricao?: string;
  created_at: string;
}

export interface EquipamentoCreate {
  nome: string;
  descricao?: string;
}

export interface SalaEquipamento {
  sala_id: number;
  equipamento_id: number;
  quantidade: number;
}

export interface SalaEquipamentoCreate {
  equipamento_id: number;
  quantidade: number;
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);

  readonly salas = signal<Sala[]>([]);
  readonly equipamentos = signal<Equipamento[]>([]);
  readonly isLoading = signal(false);
  readonly errorMessage = signal<string | null>(null);

  listarSalas(campusId?: number): Observable<Sala[]> {
    this.iniciar();
    const url = campusId ? `/api/v1/salas?campus_id=${campusId}` : '/api/v1/salas';
    return this.http.get<Sala[]>(url).pipe(this.tratar((d) => this.salas.set(d)));
  }

  criarSala(payload: SalaCreate): Observable<Sala> {
    this.iniciar();
    return this.http
      .post<Sala>('/api/v1/salas', payload)
      .pipe(this.tratar((s) => this.salas.update((l) => [...l, s])));
  }

  listarEquipamentos(): Observable<Equipamento[]> {
    this.iniciar();
    return this.http
      .get<Equipamento[]>('/api/v1/equipamentos')
      .pipe(this.tratar((d) => this.equipamentos.set(d)));
  }

  criarEquipamento(payload: EquipamentoCreate): Observable<Equipamento> {
    this.iniciar();
    return this.http
      .post<Equipamento>('/api/v1/equipamentos', payload)
      .pipe(this.tratar((e) => this.equipamentos.update((l) => [...l, e])));
  }

  associarEquipamento(salaId: number, payload: SalaEquipamentoCreate): Observable<SalaEquipamento> {
    this.iniciar();
    return this.http
      .post<SalaEquipamento>(`/api/v1/salas/${salaId}/equipamentos`, payload)
      .pipe(this.tratar(() => {}));
  }

  private iniciar(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);
  }

  private tratar<T>(fn: (res: T) => void) {
    return tap<T>({
      next: (res) => {
        fn(res);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.errorMessage.set(this.extrairErro(err));
        this.isLoading.set(false);
      },
    });
  }

  private extrairErro(err: any): string {
    const detail = err?.error?.detail;
    if (detail) {
      if (Array.isArray(detail))
        return detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
      return String(detail);
    }
    return 'Falha na comunicacao com a API administrativa';
  }
}
