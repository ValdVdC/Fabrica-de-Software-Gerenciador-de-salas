import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, finalize, throwError } from 'rxjs';

export type TipoEventoLogType = 'criacao' | 'remanejamento' | 'alteracao' | 'cancelamento';

/* prettier-ignore */
export interface LogRead { id: number; campus_id?: number | null; horario_id?: number | null; snapshot_evento?: Record<string, unknown> | null; tipo_evento: TipoEventoLogType; usuario_responsavel: number; detalhes?: string | null; timestamp: string; }
/* prettier-ignore */
export interface FiltroLogs { campus_id?: number | null; tipo_evento?: string | null; usuario_id?: number | null; horario_id?: number | null; data_inicio?: string | null; data_fim?: string | null; skip?: number; limit?: number; }

@Injectable({ providedIn: 'root' })
export class LogService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/logs';

  private readonly _logs = signal<LogRead[]>([]);
  readonly logs = this._logs.asReadonly();
  private readonly _activeRequests = signal<number>(0);
  readonly isLoading = computed(() => this._activeRequests() > 0);
  private readonly _exportRequests = signal<number>(0);
  readonly isExporting = computed(() => this._exportRequests() > 0);
  private readonly _errorMessage = signal<string | null>(null);
  readonly errorMessage = this._errorMessage.asReadonly();

  listarLogs(filtros: FiltroLogs = {}): Observable<LogRead[]> {
    this._activeRequests.update((c) => c + 1);
    this._errorMessage.set(null);
    const params = this.montarParams(filtros, false);
    return this.http.get<LogRead[]>(this.baseUrl, { params }).pipe(
      tap((res) => this._logs.set(res)),
      catchError((err) => this.tratarErro(err, 'Erro ao carregar historico de operacoes.')),
      finalize(() => this._activeRequests.update((c) => Math.max(0, c - 1))),
    );
  }

  exportarLogsCsv(filtros: FiltroLogs = {}): Observable<Blob> {
    this._exportRequests.update((c) => c + 1);
    this._errorMessage.set(null);
    const params = this.montarParams(filtros, true).set('formato', 'csv');
    return this.http.get(this.baseUrl, { params, responseType: 'blob' }).pipe(
      tap((blob) => this.dispararDownloadBlob(blob, 'historico_logs.csv')),
      catchError((err) => this.tratarErro(err, 'Erro ao exportar historico em CSV.')),
      finalize(() => this._exportRequests.update((c) => Math.max(0, c - 1))),
    );
  }

  limparErro(): void {
    this._errorMessage.set(null);
  }

  protected dispararDownloadBlob(blob: Blob, nomeArquivo: string): void {
    if (typeof window === 'undefined' || !window.URL?.createObjectURL) return;
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nomeArquivo;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  private montarParams(f: Record<string, any>, ignorarPaginacao: boolean): HttpParams {
    let p = new HttpParams();
    for (const k of ['campus_id', 'usuario_id', 'horario_id']) {
      if (f[k] && Number(f[k]) > 0) p = p.set(k, String(f[k]));
    }
    for (const k of ['tipo_evento', 'data_inicio', 'data_fim']) {
      if (typeof f[k] === 'string' && f[k].trim()) p = p.set(k, f[k].trim());
    }
    if (!ignorarPaginacao) {
      if (f['skip'] !== undefined && f['skip'] >= 0) p = p.set('skip', String(f['skip']));
      if (f['limit'] !== undefined && f['limit'] >= 1) p = p.set('limit', String(f['limit']));
    }
    return p;
  }

  private tratarErro(err: any, fallbackMsg: string): Observable<never> {
    const detail = err?.error?.detail;
    let msg = typeof detail === 'string' ? detail : fallbackMsg;
    if (Array.isArray(detail) && detail.length > 0 && detail[0]?.msg) {
      msg = String(detail[0].msg);
    }
    this._errorMessage.set(msg);
    return throwError(() => err);
  }
}
