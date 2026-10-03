import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, finalize, catchError, throwError } from 'rxjs';

export interface MetricasAlocacao {
  tempo_sequencial_ms: number;
  tempo_paralelo_ms: number;
  speedup: number;
  eficiencia_pct: number;
  fracao_amdahl: number;
  threads: number;
  total_turmas: number;
  alocadas: number;
  conflitos: number;
}

export interface AlocacaoItem {
  turma_id: number;
  disciplina_codigo: string;
  disciplina_nome: string;
  sala_id: number;
  sala_bloco: string;
  sala_numero: string;
  dia_semana: number;
  hora_inicio: string;
  hora_fim: string;
  score_desperdicio?: number;
}

export interface AlocacaoOtimizarRequest {
  periodo_letivo: string;
  campus_id: number;
  max_threads: number;
  salvar_no_banco: boolean;
}

export interface AlocacaoOtimizarResponse {
  sucesso: boolean;
  mensagem: string;
  metricas: MetricasAlocacao;
  alocacoes: AlocacaoItem[];
}

export interface AlocacaoBenchmarkRequest {
  cenario: string;
  threads: number;
}

export interface AlocacaoBenchmarkResponse {
  cenario: string;
  num_turmas: number;
  num_salas: number;
  metricas: MetricasAlocacao;
}

@Injectable({ providedIn: 'root' })
export class AlocacaoService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/v1/alocacao';

  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);
  readonly sucessoMessage = signal<string | null>(null);
  readonly metricas = signal<MetricasAlocacao | null>(null);
  readonly alocacoes = signal<AlocacaoItem[]>([]);

  otimizarAlocacao(payload: AlocacaoOtimizarRequest): Observable<AlocacaoOtimizarResponse> {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.sucessoMessage.set(null);

    return this.http.post<AlocacaoOtimizarResponse>(`${this.apiUrl}/otimizar`, payload).pipe(
      tap((res) => {
        this.metricas.set(res.metricas);
        this.alocacoes.set(res.alocacoes);
        this.sucessoMessage.set(res.mensagem);
      }),
      catchError((err) => {
        const msg = err.error?.detail || 'Erro ao executar alocacao inteligente.';
        this.errorMessage.set(msg);
        return throwError(() => err);
      }),
      finalize(() => this.isLoading.set(false)),
    );
  }

  executarBenchmark(payload: AlocacaoBenchmarkRequest): Observable<AlocacaoBenchmarkResponse> {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    return this.http.post<AlocacaoBenchmarkResponse>(`${this.apiUrl}/benchmark`, payload).pipe(
      tap((res) => {
        this.metricas.set(res.metricas);
        this.sucessoMessage.set(`Benchmark '${res.cenario}' concluido com sucesso.`);
      }),
      catchError((err) => {
        const msg = err.error?.detail || 'Erro ao executar benchmark de alocacao.';
        this.errorMessage.set(msg);
        return throwError(() => err);
      }),
      finalize(() => this.isLoading.set(false)),
    );
  }

  limparMensagens(): void {
    this.errorMessage.set(null);
    this.sucessoMessage.set(null);
  }
}
