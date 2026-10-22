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

export interface SalaUpdate {
  bloco?: string;
  numero?: string;
  tipo?: 'regular' | 'laboratorio' | 'auditorio' | 'reuniao';
  capacidade?: number;
  turnos_disponiveis?: string[];
  ativo?: boolean;
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

/* prettier-ignore */
export interface UsuarioRead { id: number; campus_id: number | null; nome: string; email: string; perfil: string; ativo: boolean; }

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);

  private readonly _salas = signal<Sala[]>([]);
  readonly salas = this._salas.asReadonly();

  private readonly _equipamentos = signal<Equipamento[]>([]);
  readonly equipamentos = this._equipamentos.asReadonly();

  private readonly _usuarios = signal<UsuarioRead[]>([]);
  readonly usuarios = this._usuarios.asReadonly();

  private readonly _activeRequests = signal<number>(0);
  readonly isLoading = computed(() => this._activeRequests() > 0);

  private readonly _errorMessage = signal<string | null>(null);
  readonly errorMessage = this._errorMessage.asReadonly();

  // prettier-ignore
  private montarParamsBusca(campusId?: number, q?: string): { params?: HttpParams } {
    let p = new HttpParams();
    if (campusId !== undefined && campusId !== null) {
      if (!Number.isInteger(campusId) || campusId <= 0) throw new Error('Identificador de campus invalido');
      p = p.set('campus_id', campusId.toString());
    }
    if (q?.trim()) p = p.set('q', q.trim());
    return p.keys().length ? { params: p } : {};
  }

  listarSalas(campusId?: number, q?: string): Observable<Sala[]> {
    return this.executar(
      this.http.get<Sala[]>('/api/v1/salas', this.montarParamsBusca(campusId, q)),
      (dados) => this._salas.set(dados),
    );
  }

  listarUsuarios(campusId?: number, q?: string): Observable<UsuarioRead[]> {
    return this.executar(
      this.http.get<UsuarioRead[]>('/api/v1/usuarios', this.montarParamsBusca(campusId, q)),
      (dados) => this._usuarios.set(dados),
    );
  }

  criarSala(payload: SalaCreate): Observable<Sala> {
    return this.executar(this.http.post<Sala>('/api/v1/salas', payload), (nova) =>
      this._salas.update((lista) => [...lista, nova]),
    );
  }

  atualizarSala(salaId: number, payload: SalaUpdate): Observable<Sala> {
    if (!Number.isInteger(salaId) || salaId <= 0) {
      throw new Error('Identificador de sala invalido');
    }
    return this.executar(this.http.put<Sala>(`/api/v1/salas/${salaId}`, payload), (atualizada) => {
      this._salas.update((lista) => lista.map((s) => (s.id === atualizada.id ? atualizada : s)));
    });
  }

  excluirSala(salaId: number): Observable<void> {
    if (!Number.isInteger(salaId) || salaId <= 0) {
      throw new Error('Identificador de sala invalido');
    }
    return this.executar(this.http.delete<void>(`/api/v1/salas/${salaId}`), () => {
      this._salas.update((lista) => lista.filter((s) => s.id !== salaId));
    });
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
    this._usuarios.set([]);
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
