import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import {
  AlocacaoService,
  AlocacaoOtimizarRequest,
  AlocacaoOtimizarResponse,
  AlocacaoBenchmarkRequest,
  AlocacaoBenchmarkResponse,
} from './alocacao.service';

describe('AlocacaoService', () => {
  let service: AlocacaoService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AlocacaoService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AlocacaoService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('deve inicializar com sinais vazios e estado consistente', () => {
    expect(service.isLoading()).toBeFalse();
    expect(service.errorMessage()).toBeNull();
    expect(service.sucessoMessage()).toBeNull();
    expect(service.metricas()).toBeNull();
    expect(service.alocacoes().length).toBe(0);
  });

  it('deve disparar POST /api/v1/alocacao/otimizar e atualizar sinais reativos', () => {
    const payload: AlocacaoOtimizarRequest = {
      periodo_letivo: '2026.1',
      campus_id: 1,
      max_threads: 4,
      salvar_no_banco: true,
    };

    const mockResponse: AlocacaoOtimizarResponse = {
      sucesso: true,
      mensagem: 'Alocacao executada com sucesso.',
      metricas: {
        tempo_sequencial_ms: 20.0,
        tempo_paralelo_ms: 5.5,
        speedup: 3.64,
        eficiencia_pct: 91.0,
        fracao_amdahl: 0.965,
        threads: 4,
        total_turmas: 25,
        alocadas: 25,
        conflitos: 0,
      },
      alocacoes: [
        {
          turma_id: 1,
          disciplina_codigo: 'CC101',
          disciplina_nome: 'Algoritmos I',
          sala_id: 10,
          sala_bloco: 'Bloco A',
          sala_numero: '101',
          dia_semana: 0,
          hora_inicio: '08:00',
          hora_fim: '10:00',
          score_desperdicio: 5,
        },
      ],
    };

    service.otimizarAlocacao(payload).subscribe((res) => {
      expect(res.sucesso).toBeTrue();
      expect(res.alocacoes.length).toBe(1);
    });

    const req = httpMock.expectOne('/api/v1/alocacao/otimizar');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(mockResponse);

    expect(service.metricas()?.speedup).toBe(3.64);
    expect(service.alocacoes().length).toBe(1);
    expect(service.sucessoMessage()).toBe('Alocacao executada com sucesso.');
    expect(service.isLoading()).toBeFalse();
  });

  it('deve capturar erro em falha HTTP na otimizacao', () => {
    const payload: AlocacaoOtimizarRequest = {
      periodo_letivo: '2026.1',
      campus_id: 1,
      max_threads: 4,
      salvar_no_banco: false,
    };

    service.otimizarAlocacao(payload).subscribe({
      next: () => fail('Deveria ter falhado com erro 403'),
      error: (err) => {
        expect(err.status).toBe(403);
      },
    });

    const req = httpMock.expectOne('/api/v1/alocacao/otimizar');
    req.flush(
      { detail: 'Acesso negado: privilegio insuficiente.' },
      { status: 403, statusText: 'Forbidden' },
    );

    expect(service.errorMessage()).toBe('Acesso negado: privilegio insuficiente.');
    expect(service.isLoading()).toBeFalse();
  });

  it('deve disparar POST /api/v1/alocacao/benchmark e atualizar metricas', () => {
    const payload: AlocacaoBenchmarkRequest = {
      cenario: 'medio',
      threads: 4,
    };

    const mockResponse: AlocacaoBenchmarkResponse = {
      cenario: 'medio',
      num_turmas: 100,
      num_salas: 40,
      metricas: {
        tempo_sequencial_ms: 19.0,
        tempo_paralelo_ms: 5.0,
        speedup: 3.8,
        eficiencia_pct: 95.0,
        fracao_amdahl: 0.9824,
        threads: 4,
        total_turmas: 100,
        alocadas: 99,
        conflitos: 1,
      },
    };

    service.executarBenchmark(payload).subscribe((res) => {
      expect(res.cenario).toBe('medio');
      expect(res.metricas.speedup).toBe(3.8);
    });

    const req = httpMock.expectOne('/api/v1/alocacao/benchmark');
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);

    expect(service.metricas()?.speedup).toBe(3.8);
    expect(service.sucessoMessage()).toContain("Benchmark 'medio' concluido com sucesso.");
  });

  it('deve limpar mensagens de erro e sucesso com limparMensagens', () => {
    service.limparMensagens();
    expect(service.errorMessage()).toBeNull();
    expect(service.sucessoMessage()).toBeNull();
  });
});
