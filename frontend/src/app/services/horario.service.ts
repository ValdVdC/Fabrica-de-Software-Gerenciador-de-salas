import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, defer, tap, finalize } from 'rxjs';

/* prettier-ignore */
export interface HorarioMeu {
  id: number;
  campus_id: number;
  turma_id: number;
  disciplina_nome: string;
  disciplina_codigo: string;
  periodo_letivo: string;
  turno: string;
  dia_semana: number;
  hora_inicio: string;
  hora_fim: string;
  sala_id: number;
  sala_bloco: string;
  sala_numero: string;
  sala_tipo: string;
  professor_id?: number | null;
  professor_nome?: string | null;
}

export const DIAS_SEMANA_LABELS: Record<number, string> = {
  0: 'Segunda-feira',
  1: 'Terca-feira',
  2: 'Quarta-feira',
  3: 'Quinta-feira',
  4: 'Sexta-feira',
  5: 'Sabado',
  6: 'Domingo',
};

@Injectable({ providedIn: 'root' })
export class HorarioService {
  private readonly http = inject(HttpClient);

  private readonly _horarios = signal<HorarioMeu[]>([]);
  readonly horarios = this._horarios.asReadonly();

  private readonly _activeRequests = signal<number>(0);
  readonly isLoading = computed(() => this._activeRequests() > 0);

  private readonly _errorMessage = signal<string | null>(null);
  readonly errorMessage = this._errorMessage.asReadonly();

  readonly totalAulas = computed(() => this._horarios().length);

  readonly disciplinasDistintas = computed(() => {
    const codigos = new Set(this._horarios().map((h) => h.disciplina_codigo));
    return Array.from(codigos);
  });

  private _geracao = 0;

  private extrairErro(err: any): string {
    if (!err || typeof err !== 'object') return 'Erro desconhecido';
    if (err.status === 0) return 'Falha de conexao com o servidor';
    if (err.status === 401) return 'Sessao expirada. Faca login novamente.';
    if (err.status === 403) {
      return typeof err.error?.detail === 'string'
        ? err.error.detail
        : 'Permissao insuficiente para realizar esta acao.';
    }
    if (err.status >= 500) return 'Erro interno no servidor. Tente novamente mais tarde.';
    const det = err.error?.detail;
    if (Array.isArray(det)) {
      return det.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
    }
    if (typeof det === 'string') return det;
    return err.message || 'Ocorreu um erro na comunicacao com o servidor.';
  }

  carregarMeusHorarios(skip?: number, limit?: number): Observable<HorarioMeu[]> {
    if (skip !== undefined && (!Number.isInteger(skip) || skip < 0)) {
      throw new Error('Parametro skip invalido');
    }
    if (limit !== undefined && (!Number.isInteger(limit) || limit < 1 || limit > 200)) {
      throw new Error('Parametro limit invalido');
    }

    let params: HttpParams | undefined;
    if (skip !== undefined || limit !== undefined) {
      params = new HttpParams();
      if (skip !== undefined) params = params.set('skip', skip.toString());
      if (limit !== undefined) params = params.set('limit', limit.toString());
    }

    return defer(() => {
      const g = this._geracao;
      this._errorMessage.set(null);
      this._activeRequests.update((n) => n + 1);
      return this.http.get<HorarioMeu[]>('/api/v1/horarios/meus', { params }).pipe(
        tap({
          next: (dados) => {
            if (this._geracao === g) {
              this._horarios.set(dados);
              this._errorMessage.set(null);
            }
          },
          error: (err) => {
            if (this._geracao === g) {
              this._errorMessage.set(this.extrairErro(err));
            }
          },
        }),
        finalize(() => {
          if (this._geracao === g) {
            this._activeRequests.update((n) => Math.max(0, n - 1));
          }
        }),
      );
    });
  }

  obterHorariosDoDia(dia: number): HorarioMeu[] {
    if (!Number.isInteger(dia) || dia < 0 || dia > 6) {
      throw new Error('Dia da semana invalido');
    }
    return this._horarios()
      .filter((h) => h.dia_semana === dia)
      .sort((a, b) => (a.hora_inicio ?? '').localeCompare(b.hora_inicio ?? ''));
  }

  limparErro(): void {
    this._errorMessage.set(null);
  }

  resetState(): void {
    this._geracao++;
    this._horarios.set([]);
    this._activeRequests.set(0);
    this._errorMessage.set(null);
  }
}
