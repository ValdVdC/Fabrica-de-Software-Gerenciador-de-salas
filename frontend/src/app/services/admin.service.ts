import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, finalize } from 'rxjs';

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

  private readonly _salas = signal<Sala[]>([]);
  readonly salas = this._salas.asReadonly();

  private readonly _equipamentos = signal<Equipamento[]>([]);
  readonly equipamentos = this._equipamentos.asReadonly();

  private readonly _activeRequests = signal<number>(0);
  readonly isLoading = computed(() => this._activeRequests() > 0);

  private readonly _errorMessage = signal<string | null>(null);
  readonly errorMessage = this._errorMessage.asReadonly();

  listarSalas(campusId?: number): Observable<Sala[]> {
    let params: HttpParams | undefined;
    if (campusId !== undefined && campusId !== null) {
      if (!Number.isInteger(campusId) || campusId <= 0) {
        throw new Error('Identificador de campus invalido');
      }
      params = new HttpParams().set('campus_id', campusId.toString());
    }
    return this.executar(this.http.get<Sala[]>('/api/v1/salas', { params }), (dados) =>
      this._salas.set(dados),
    );
  }

  criarSala(payload: SalaCreate): Observable<Sala> {
    return this.executar(this.http.post<Sala>('/api/v1/salas', payload), (nova) =>
      this._salas.update((lista) => [...lista, nova]),
    );
  }

  listarEquipamentos(): Observable<Equipamento[]> {
    return this.executar(this.http.get<Equipamento[]>('/api/v1/equipamentos'), (dados) =>
      this._equipamentos.set(dados),
    );
  }

  criarEquipamento(payload: EquipamentoCreate): Observable<Equipamento> {
    return this.executar(this.http.post<Equipamento>('/api/v1/equipamentos', payload), (novo) =>
      this._equipamentos.update((lista) => [...lista, novo]),
    );
  }

  associarEquipamento(salaId: number, payload: SalaEquipamentoCreate): Observable<SalaEquipamento> {
    if (!Number.isInteger(salaId) || salaId <= 0) {
      throw new Error('Identificador de sala invalido');
    }
    return this.executar(
      this.http.post<SalaEquipamento>(`/api/v1/salas/${salaId}/equipamentos`, payload),
      () => {},
    );
  }

  resetState(): void {
    this._salas.set([]);
    this._equipamentos.set([]);
    this._errorMessage.set(null);
    this._activeRequests.set(0);
  }

  private executar<T>(source: Observable<T>, onSucesso: (res: T) => void): Observable<T> {
    this._activeRequests.update((c) => c + 1);
    this._errorMessage.set(null);
    return source.pipe(
      tap({
        next: (res) => onSucesso(res),
        error: (err) => this._errorMessage.set(this.extrairErro(err)),
      }),
      finalize(() => this._activeRequests.update((c) => Math.max(0, c - 1))),
    );
  }

  private extrairErro(err: any): string {
    if (!err) return 'Erro desconhecido na requisicao';
    if (err.status === 0) return 'Nao foi possivel conectar ao servidor';
    if (err.status >= 500) return 'Erro interno no servidor. Tente novamente mais tarde.';

    const detail = err.error?.detail;
    if (detail) {
      if (Array.isArray(detail)) {
        const msgs = detail
          .map((d: any) => (d && typeof d === 'object' && d.msg ? String(d.msg) : null))
          .filter(Boolean);
        return msgs.length > 0 ? msgs.join('; ') : 'Dados de entrada invalidos';
      }
      if (typeof detail === 'object' && detail !== null) {
        return detail.message || detail.msg || 'Requisicao invalida';
      }
      return String(detail);
    }
    return err.statusText || 'Falha na comunicacao com a API administrativa';
  }
}
