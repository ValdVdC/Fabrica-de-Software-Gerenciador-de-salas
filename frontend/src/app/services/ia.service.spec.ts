import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import {
  IaService,
  SugestaoRemanejamento,
  SugestaoDecisaoPayload,
  AnaliseIAResponse,
} from './ia.service';

describe('IaService', () => {
  let service: IaService;
  let httpMock: HttpTestingController;

  const mockSugestao: SugestaoRemanejamento = {
    id: 1,
    horario_id: 10,
    sala_atual_id: 101,
    sala_sugerida_id: 204,
    motivo: 'Ociosidade fisica detectada decorrente de alto absenteismo previsto',
    justificativa: null,
    status: 'pendente',
    aprovado_por: null,
    criado_em: '2026-10-15T10:00:00Z',
    atualizado_em: '2026-10-15T10:00:00Z',
    prob_ausencia: 0.78,
    turma_id: 5,
    disciplina_codigo: 'CC101',
    disciplina_nome: 'Algoritmos e Estruturas de Dados I',
    sala_atual_bloco: 'Bloco A',
    sala_atual_numero: '101',
    sala_atual_capacidade: 60,
    sala_sugerida_bloco: 'Bloco B',
    sala_sugerida_numero: '204',
    sala_sugerida_capacidade: 25,
    dia_semana: 0,
    hora_inicio: '08:00',
    hora_fim: '10:00',
    campus_id: 2,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [IaService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(IaService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('deve inicializar com sinais vazios e estado consistente', () => {
    expect(service.isLoading()).toBeFalse();
    expect(service.errorMessage()).toBeNull();
    expect(service.sucessoMessage()).toBeNull();
    expect(service.sugestoes().length).toBe(0);
  });

  it('deve listar sugestoes via GET /api/v1/sugestoes e atualizar signal sugestoes', () => {
    service.obterSugestoes().subscribe((res) => {
      expect(res.length).toBe(1);
      expect(res[0].id).toBe(1);
    });
    const req = httpMock.expectOne('/api/v1/sugestoes');
    expect(req.request.method).toBe('GET');
    req.flush([mockSugestao]);
    expect(service.sugestoes().length).toBe(1);
    expect(service.sugestoes()[0].disciplina_codigo).toBe('CC101');
    expect(service.isLoading()).toBeFalse();
  });

  it('deve filtrar sugestoes por status e campusId via query param', () => {
    service.obterSugestoes('pendente', 2).subscribe((res) => expect(res.length).toBe(1));
    const req = httpMock.expectOne('/api/v1/sugestoes?status=pendente&campus_id=2');
    expect(req.request.method).toBe('GET');
    req.flush([mockSugestao]);
    expect(service.sugestoes().length).toBe(1);
  });

  it('deve aprovar sugestao via PATCH /api/v1/sugestoes/{id} e atualizar estado local', () => {
    const aprovada: SugestaoRemanejamento = {
      ...mockSugestao,
      status: 'aprovado',
      justificativa: 'Aprovado',
    };
    service.aprovarSugestao(1, 'Aprovado').subscribe((res) => expect(res.status).toBe('aprovado'));
    const req = httpMock.expectOne('/api/v1/sugestoes/1');
    expect(req.request.method).toBe('PATCH');
    const expectedPayload: SugestaoDecisaoPayload = {
      status: 'aprovado',
      justificativa: 'Aprovado',
    };
    expect(req.request.body).toEqual(expectedPayload);
    req.flush(aprovada);
    expect(service.sucessoMessage()).toContain('aprovada com sucesso');
    expect(service.isLoading()).toBeFalse();
  });

  it('deve rejeitar sugestao via PATCH /api/v1/sugestoes/{id} com justificativa', () => {
    const rejeitada: SugestaoRemanejamento = {
      ...mockSugestao,
      status: 'rejeitado',
      justificativa: 'Rejeitado',
    };
    service
      .rejeitarSugestao(1, 'Rejeitado')
      .subscribe((res) => expect(res.status).toBe('rejeitado'));
    const req = httpMock.expectOne('/api/v1/sugestoes/1');
    expect(req.request.method).toBe('PATCH');
    const expectedPayload: SugestaoDecisaoPayload = {
      status: 'rejeitado',
      justificativa: 'Rejeitado',
    };
    expect(req.request.body).toEqual(expectedPayload);
    req.flush(rejeitada);
    expect(service.sucessoMessage()).toContain('rejeitada com sucesso');
    expect(service.isLoading()).toBeFalse();
  });

  it('deve barrar rejeicao sem justificativa e definir errorMessage', () => {
    service.rejeitarSugestao(1, '   ').subscribe({
      next: () => fail('Deveria ter falhado sem justificativa'),
      error: (err) => {
        expect(err.message).toContain('Justificativa e obrigatoria');
      },
    });
    expect(service.errorMessage()).toBe('Justificativa e obrigatoria para rejeitar a sugestao.');
    httpMock.expectNone('/api/v1/sugestoes/1');
  });

  it('deve disparar rotina de analise de IA e realizar merge sem apagar sugestoes existentes', () => {
    service.sugestoes.set([mockSugestao]);
    const novaSugestao: SugestaoRemanejamento = { ...mockSugestao, id: 2, horario_id: 11 };
    const mockAnaliseResponse: AnaliseIAResponse = {
      total_turmas_analisadas: 25,
      total_sugestoes_geradas: 1,
      sugestoes: [novaSugestao],
      tempo_processamento_ms: 45.2,
    };

    service.dispararAnalise(2, '2026.1', 0.4).subscribe((res) => {
      expect(res.total_turmas_analisadas).toBe(25);
      expect(res.total_sugestoes_geradas).toBe(1);
    });

    const req = httpMock.expectOne('/api/v1/ia/analisar');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      campus_id: 2,
      periodo_letivo: '2026.1',
      limiar_ociosidade: 0.4,
    });
    req.flush(mockAnaliseResponse);

    expect(service.sugestoes().length).toBe(2);
    expect(service.sucessoMessage()).toContain('Analise preditiva de absenteismo concluida');
  });

  it('deve capturar erro 401 Unauthorized e atualizar errorMessage defensivamente', () => {
    service
      .obterSugestoes()
      .subscribe({
        next: () => fail('Deveria ter falhado com 401'),
        error: (err) => expect(err.status).toBe(401),
      });
    const req = httpMock.expectOne('/api/v1/sugestoes');
    req.flush({ detail: 'Token ausente ou expirado' }, { status: 401, statusText: 'Unauthorized' });
    expect(service.errorMessage()).toBe('Token ausente ou expirado');
    expect(service.isLoading()).toBeFalse();
  });

  it('deve capturar erro 403 Forbidden com mensagem de privilegio insuficiente', () => {
    service
      .aprovarSugestao(1)
      .subscribe({
        next: () => fail('Deveria ter falhado com 403'),
        error: (err) => expect(err.status).toBe(403),
      });
    const req = httpMock.expectOne('/api/v1/sugestoes/1');
    req.flush(
      { detail: 'Acesso negado: privilegio insuficiente' },
      { status: 403, statusText: 'Forbidden' },
    );
    expect(service.errorMessage()).toBe('Acesso negado: privilegio insuficiente');
  });

  it('deve capturar erro 404 Not Found (BOLA / registro inexistente)', () => {
    service
      .aprovarSugestao(999)
      .subscribe({
        next: () => fail('Deveria ter falhado com 404'),
        error: (err) => expect(err.status).toBe(404),
      });
    const req = httpMock.expectOne('/api/v1/sugestoes/999');
    req.flush({ detail: 'Sugestao nao encontrada' }, { status: 404, statusText: 'Not Found' });
    expect(service.errorMessage()).toBe('Sugestao nao encontrada');
  });

  it('deve capturar erro 409 Conflict ao aprovar sugestao com sala ocupada', () => {
    service
      .aprovarSugestao(1)
      .subscribe({
        next: () => fail('Deveria ter falhado com 409'),
        error: (err) => expect(err.status).toBe(409),
      });
    const req = httpMock.expectOne('/api/v1/sugestoes/1');
    req.flush(
      { detail: 'Sala sugerida nao esta mais disponivel no horario especificado' },
      { status: 409, statusText: 'Conflict' },
    );
    expect(service.errorMessage()).toBe(
      'Sala sugerida nao esta mais disponivel no horario especificado',
    );
  });

  it('deve limpar mensagens de erro e sucesso com limparMensagens()', () => {
    service.limparMensagens();
    expect(service.errorMessage()).toBeNull();
    expect(service.sucessoMessage()).toBeNull();
  });
});
