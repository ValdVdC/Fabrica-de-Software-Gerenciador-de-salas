import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, finalize, throwError } from 'rxjs';

export type TipoSalaType = 'regular' | 'laboratorio' | 'auditorio' | 'reuniao';
export type StatusSugestaoType = 'pendente' | 'aprovado' | 'rejeitado';

/* prettier-ignore */
export interface RelatorioOcupacaoSalaRead { sala_id: number; campus_id: number; sala: string; bloco: string; numero: string; tipo: TipoSalaType; capacidade: number; quantidade_horarios: number; taxa_ocupacao_semanal: number; }
/* prettier-ignore */
export interface RelatorioRemanejamentoRead { id: number; campus_id: number; horario_id: number; status: StatusSugestaoType; sala_origem_id: number; sala_origem: string; sala_origem_capacidade: number; sala_destino_id: number; sala_destino: string; sala_destino_capacidade: number; decisor_id?: number | null; decisor?: string | null; motivo: string; justificativa?: string | null; criado_em: string; atualizado_em: string; }
/* prettier-ignore */
export interface FiltroOcupacaoSalas { campus_id?: number | null; bloco?: string | null; tipo?: string | null; skip?: number; limit?: number; }
/* prettier-ignore */
export interface FiltroRemanejamentos { campus_id?: number | null; status?: string | null; data_inicio?: string | null; data_fim?: string | null; skip?: number; limit?: number; }

@Injectable({ providedIn: 'root' })
export class RelatorioService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/relatorios';

  private readonly _ocupacaoSalas = signal<RelatorioOcupacaoSalaRead[]>([]);
  readonly ocupacaoSalas = this._ocupacaoSalas.asReadonly();
  private readonly _remanejamentos = signal<RelatorioRemanejamentoRead[]>([]);
  readonly remanejamentos = this._remanejamentos.asReadonly();
  private readonly _activeRequests = signal<number>(0);
  readonly isLoading = computed(() => this._activeRequests() > 0);
  private readonly _exportRequests = signal<number>(0);
  readonly isExporting = computed(() => this._exportRequests() > 0);
  private readonly _errorMessage = signal<string | null>(null);
  readonly errorMessage = this._errorMessage.asReadonly();

  obterOcupacaoSalas(filtros: FiltroOcupacaoSalas = {}): Observable<RelatorioOcupacaoSalaRead[]> {
    this._activeRequests.update((c) => c + 1);
    this._errorMessage.set(null);
    const params = this.montarParams(filtros, false);
    return this.http
      .get<RelatorioOcupacaoSalaRead[]>(`${this.baseUrl}/ocupacao-salas`, { params })
      .pipe(
        tap((res) => this._ocupacaoSalas.set(res)),
        catchError((err) =>
          this.tratarErro(err, 'Erro ao carregar relatorio de ocupacao de salas.'),
        ),
        finalize(() => this._activeRequests.update((c) => Math.max(0, c - 1))),
      );
  }

  obterRemanejamentos(
    filtros: FiltroRemanejamentos = {},
  ): Observable<RelatorioRemanejamentoRead[]> {
    this._activeRequests.update((c) => c + 1);
    this._errorMessage.set(null);
    const params = this.montarParams(filtros, false);
    return this.http
      .get<RelatorioRemanejamentoRead[]>(`${this.baseUrl}/remanejamentos`, { params })
      .pipe(
        tap((res) => this._remanejamentos.set(res)),
        catchError((err) => this.tratarErro(err, 'Erro ao carregar relatorio de remanejamentos.')),
        finalize(() => this._activeRequests.update((c) => Math.max(0, c - 1))),
      );
  }

  exportarOcupacaoCsv(filtros: FiltroOcupacaoSalas = {}): Observable<Blob> {
    const params = this.montarParams(filtros, true).set('formato', 'csv');
    return this.executarDownloadCsv(`${this.baseUrl}/ocupacao-salas`, params, 'ocupacao_salas.csv');
  }

  exportarRemanejamentosCsv(filtros: FiltroRemanejamentos = {}): Observable<Blob> {
    const params = this.montarParams(filtros, true).set('formato', 'csv');
    return this.executarDownloadCsv(`${this.baseUrl}/remanejamentos`, params, 'remanejamentos.csv');
  }

  limparErro(): void {
    this._errorMessage.set(null);
  }

  private executarDownloadCsv(
    url: string,
    params: HttpParams,
    nomeArquivo: string,
  ): Observable<Blob> {
    this._exportRequests.update((c) => c + 1);
    this._errorMessage.set(null);
    return this.http.get(url, { params, responseType: 'blob' }).pipe(
      tap((blob) => this.dispararDownloadBlob(blob, nomeArquivo)),
      catchError((err) => this.tratarErro(err, 'Erro ao exportar relatorio em CSV.')),
      finalize(() => this._exportRequests.update((c) => Math.max(0, c - 1))),
    );
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
    if (f['campus_id'] && f['campus_id'] > 0) p = p.set('campus_id', String(f['campus_id']));
    for (const k of ['bloco', 'tipo', 'status', 'data_inicio', 'data_fim']) {
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
