import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, finalize, catchError, throwError } from 'rxjs';

export type StatusSugestaoType = 'pendente' | 'aprovado' | 'rejeitado';

export interface SugestaoRemanejamento {
  id: number;
  horario_id: number;
  sala_atual_id: number;
  sala_sugerida_id: number;
  motivo: string;
  justificativa?: string | null;
  status: StatusSugestaoType;
  aprovado_por?: number | null;
  criado_em: string;
  atualizado_em: string;
  prob_ausencia?: number | null;
  turma_id?: number | null;
  disciplina_codigo?: string | null;
  disciplina_nome?: string | null;
  sala_atual_bloco?: string | null;
  sala_atual_numero?: string | null;
  sala_atual_capacidade?: number | null;
  sala_sugerida_bloco?: string | null;
  sala_sugerida_numero?: string | null;
  sala_sugerida_capacidade?: number | null;
  dia_semana?: number | null;
  hora_inicio?: string | null;
  hora_fim?: string | null;
  campus_id?: number | null;
}

export interface SugestaoDecisaoPayload {
  status: 'aprovado' | 'rejeitado';
  justificativa?: string;
}

export interface AnaliseIARequest {
  campus_id?: number;
  periodo_letivo?: string;
  limiar_ociosidade?: number;
}

export interface AnaliseIAResponse {
  total_turmas_analisadas: number;
  total_sugestoes_geradas: number;
  sugestoes: SugestaoRemanejamento[];
  tempo_processamento_ms: number;
}

@Injectable({ providedIn: 'root' })
export class IaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  readonly sugestoes = signal<SugestaoRemanejamento[]>([]);
  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);
  readonly sucessoMessage = signal<string | null>(null);

  obterSugestoes(status?: string, campusId?: number): Observable<SugestaoRemanejamento[]> {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    if (campusId && campusId > 0) params = params.set('campus_id', campusId.toString());

    return this.http.get<SugestaoRemanejamento[]>(`${this.baseUrl}/sugestoes`, { params }).pipe(
      tap((res) => this.sugestoes.set(res)),
      catchError((err) => this.tratarErro(err, 'Erro ao carregar sugestoes de remanejamento.')),
      finalize(() => this.isLoading.set(false)),
    );
  }

  aprovarSugestao(id: number, justificativa?: string): Observable<SugestaoRemanejamento> {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.sucessoMessage.set(null);

    const payload: SugestaoDecisaoPayload = {
      status: 'aprovado',
      ...(justificativa ? { justificativa: justificativa.trim() } : {}),
    };

    return this.http.patch<SugestaoRemanejamento>(`${this.baseUrl}/sugestoes/${id}`, payload).pipe(
      tap((res) => {
        this.sucessoMessage.set(`Sugestao #${id} aprovada com sucesso.`);
        this.atualizarItemNaLista(res);
      }),
      catchError((err) => this.tratarErro(err, 'Erro ao aprovar sugestao de remanejamento.')),
      finalize(() => this.isLoading.set(false)),
    );
  }

  rejeitarSugestao(id: number, justificativa?: string): Observable<SugestaoRemanejamento> {
    const justTrimmed = justificativa?.trim();
    if (!justTrimmed) {
      this.errorMessage.set('Justificativa e obrigatoria para rejeitar a sugestao.');
      return throwError(() => new Error('Justificativa e obrigatoria para rejeitar a sugestao.'));
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.sucessoMessage.set(null);

    const payload: SugestaoDecisaoPayload = {
      status: 'rejeitado',
      justificativa: justTrimmed,
    };

    return this.http.patch<SugestaoRemanejamento>(`${this.baseUrl}/sugestoes/${id}`, payload).pipe(
      tap((res) => {
        this.sucessoMessage.set(`Sugestao #${id} rejeitada com sucesso.`);
        this.atualizarItemNaLista(res);
      }),
      catchError((err) => this.tratarErro(err, 'Erro ao rejeitar sugestao de remanejamento.')),
      finalize(() => this.isLoading.set(false)),
    );
  }

  definirErro(msg: string): void {
    this.errorMessage.set(msg);
  }

  dispararAnalise(
    campusId?: number,
    periodoLetivo?: string,
    limiarOciosidade: number = 0.4,
  ): Observable<AnaliseIAResponse> {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.sucessoMessage.set(null);

    const payload: AnaliseIARequest = {
      ...(campusId ? { campus_id: campusId } : {}),
      ...(periodoLetivo ? { periodo_letivo: periodoLetivo } : {}),
      limiar_ociosidade: limiarOciosidade,
    };

    return this.http.post<AnaliseIAResponse>(`${this.baseUrl}/ia/analisar`, payload).pipe(
      tap((res) => {
        const mapa = new Map<number, SugestaoRemanejamento>();
        this.sugestoes().forEach((s) => mapa.set(s.id, s));
        res.sugestoes.forEach((s) => mapa.set(s.id, s));
        this.sugestoes.set(Array.from(mapa.values()));
        this.sucessoMessage.set(
          `Analise preditiva de absenteismo concluida: ${res.total_sugestoes_geradas} sugestoes geradas em ${res.tempo_processamento_ms}ms.`,
        );
      }),
      catchError((err) => this.tratarErro(err, 'Erro ao executar analise preditiva de IA.')),
      finalize(() => this.isLoading.set(false)),
    );
  }

  limparMensagens(): void {
    this.errorMessage.set(null);
    this.sucessoMessage.set(null);
  }

  private atualizarItemNaLista(item: SugestaoRemanejamento): void {
    const atual = this.sugestoes();
    const idx = atual.findIndex((s) => s.id === item.id);
    if (idx !== -1) {
      const atualizados = [...atual];
      atualizados[idx] = item;
      this.sugestoes.set(atualizados);
    }
  }

  private tratarErro(err: any, fallbackMsg: string): Observable<never> {
    const detail = err?.error?.detail;
    let msg = typeof detail === 'string' ? detail : fallbackMsg;
    if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
      msg = detail[0].msg;
    }
    this.errorMessage.set(msg);
    return throwError(() => err);
  }
}
