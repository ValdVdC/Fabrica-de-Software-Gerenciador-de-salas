import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, finalize, throwError } from 'rxjs';

export type TipoEventoLogType = 'criacao' | 'remanejamento' | 'alteracao' | 'cancelamento';

export interface LogRead {
  id: number;
  campus_id?: number | null;
  horario_id?: number | null;
  snapshot_evento?: Record<string, unknown> | null;
  tipo_evento: TipoEventoLogType;
  usuario_responsavel: number;
  detalhes?: string | null;
  timestamp: string;
}

export interface SugestoesPorStatusRead {
  pendente: number;
  aprovado: number;
  rejeitado: number;
  total: number;
}

export interface DashboardResumoRead {
  salas_ativas: number;
  turmas: number;
  horarios: number;
  sugestoes: SugestoesPorStatusRead;
  vagas_recuperadas: number;
  eventos_recentes: LogRead[];
}

export interface OcupacaoPorDiaRead {
  dia_semana: number;
  total_horarios: number;
}

export interface OcupacaoPorTurnoRead {
  turno: string;
  total_horarios: number;
}

export interface DashboardOcupacaoRead {
  por_dia_semana: OcupacaoPorDiaRead[];
  por_turno: OcupacaoPorTurnoRead[];
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/dashboard';

  private readonly _resumo = signal<DashboardResumoRead | null>(null);
  readonly resumo = this._resumo.asReadonly();

  private readonly _ocupacao = signal<DashboardOcupacaoRead | null>(null);
  readonly ocupacao = this._ocupacao.asReadonly();

  private readonly _activeRequests = signal<number>(0);
  readonly isLoading = computed(() => this._activeRequests() > 0);

  private readonly _errorMessage = signal<string | null>(null);
  readonly errorMessage = this._errorMessage.asReadonly();

  obterResumo(campusId?: number | null): Observable<DashboardResumoRead> {
    this._activeRequests.update((c) => c + 1);
    this._errorMessage.set(null);
    const params = this.criarParams(campusId);

    return this.http.get<DashboardResumoRead>(`${this.baseUrl}/resumo`, { params }).pipe(
      tap((res) => this._resumo.set(res)),
      catchError((err) => this.tratarErro(err, 'Erro ao carregar resumo do dashboard.')),
      finalize(() => this._activeRequests.update((c) => Math.max(0, c - 1))),
    );
  }

  obterOcupacao(campusId?: number | null): Observable<DashboardOcupacaoRead> {
    this._activeRequests.update((c) => c + 1);
    this._errorMessage.set(null);
    const params = this.criarParams(campusId);

    return this.http.get<DashboardOcupacaoRead>(`${this.baseUrl}/ocupacao`, { params }).pipe(
      tap((res) => this._ocupacao.set(res)),
      catchError((err) =>
        this.tratarErro(err, 'Erro ao carregar indicadores de ocupacao do dashboard.'),
      ),
      finalize(() => this._activeRequests.update((c) => Math.max(0, c - 1))),
    );
  }

  limparErro(): void {
    this._errorMessage.set(null);
  }

  private criarParams(campusId?: number | null): HttpParams {
    let params = new HttpParams();
    if (typeof campusId === 'number' && Number.isInteger(campusId) && campusId > 0) {
      params = params.set('campus_id', campusId.toString());
    }
    return params;
  }

  private tratarErro(err: any, fallbackMsg: string): Observable<never> {
    const detail = err?.error?.detail;
    let msg = typeof detail === 'string' ? detail : fallbackMsg;
    if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
      msg = detail[0].msg;
    }
    this._errorMessage.set(msg);
    return throwError(() => err);
  }
}
