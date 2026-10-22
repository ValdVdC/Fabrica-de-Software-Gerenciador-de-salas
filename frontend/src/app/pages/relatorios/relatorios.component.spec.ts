import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { RelatoriosComponent } from './relatorios.component';
import {
  RelatorioService,
  RelatorioOcupacaoSalaRead,
  RelatorioRemanejamentoRead,
} from '../../services/relatorio.service';
import { AuthService } from '../../services/auth.service';

describe('RelatoriosComponent', () => {
  let component: RelatoriosComponent;
  let fixture: ComponentFixture<RelatoriosComponent>;

  const ocupacaoSig = signal<RelatorioOcupacaoSalaRead[]>([]);
  const remanejamentosSig = signal<RelatorioRemanejamentoRead[]>([]);
  const loadingSig = signal<boolean>(false);
  const exportingSig = signal<boolean>(false);
  const errorSig = signal<string | null>(null);

  let mockRelatorioService: any;
  let mockAuthService: any;

  beforeEach(async () => {
    ocupacaoSig.set([
      {
        sala_id: 1,
        campus_id: 1,
        sala: 'A-101',
        bloco: 'A',
        numero: '101',
        tipo: 'laboratorio',
        capacidade: 40,
        quantidade_horarios: 6,
        taxa_ocupacao_semanal: 40.0,
      },
    ]);
    remanejamentosSig.set([
      {
        id: 10,
        campus_id: 1,
        horario_id: 5,
        status: 'aprovado',
        sala_origem_id: 1,
        sala_origem: 'A-101',
        sala_origem_capacidade: 50,
        sala_destino_id: 2,
        sala_destino: 'B-202',
        sala_destino_capacidade: 30,
        decisor_id: 1,
        decisor: 'Coordenador',
        motivo: 'Ociosidade identificada',
        justificativa: 'Homologado',
        criado_em: '2026-10-15T10:00:00Z',
        atualizado_em: '2026-10-16T14:00:00Z',
      },
    ]);
    loadingSig.set(false);
    exportingSig.set(false);
    errorSig.set(null);

    mockRelatorioService = {
      ocupacaoSalas: ocupacaoSig.asReadonly(),
      remanejamentos: remanejamentosSig.asReadonly(),
      isLoading: loadingSig.asReadonly(),
      isExporting: exportingSig.asReadonly(),
      errorMessage: errorSig.asReadonly(),
      obterOcupacaoSalas: jasmine
        .createSpy('obterOcupacaoSalas')
        .and.callFake(() => of(ocupacaoSig())),
      obterRemanejamentos: jasmine
        .createSpy('obterRemanejamentos')
        .and.callFake(() => of(remanejamentosSig())),
      exportarOcupacaoCsv: jasmine
        .createSpy('exportarOcupacaoCsv')
        .and.returnValue(of(new Blob(['csv']))),
      exportarRemanejamentosCsv: jasmine
        .createSpy('exportarRemanejamentosCsv')
        .and.returnValue(of(new Blob(['csv']))),
      limparErro: jasmine.createSpy('limparErro').and.callFake(() => errorSig.set(null)),
    };

    mockAuthService = {
      currentRole: signal('coordenador').asReadonly(),
      currentUser: signal({
        id: 1,
        nome: 'Coord',
        email: 'c@sigaas.edu',
        perfil: 'coordenador',
        campus_id: 1,
      }).asReadonly(),
    };

    await TestBed.configureTestingModule({
      imports: [RelatoriosComponent],
      providers: [
        { provide: RelatorioService, useValue: mockRelatorioService },
        { provide: AuthService, useValue: mockAuthService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RelatoriosComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('deve carregar relatorio de ocupacao de salas ao inicializar', () => {
    expect(mockRelatorioService.obterOcupacaoSalas).toHaveBeenCalled();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('A-101');
    expect(compiled.textContent).toContain('40%');
  });

  it('deve alternar para a aba de remanejamentos e carregar os dados', () => {
    component.selecionarAba('remanejamentos');
    fixture.detectChanges();

    expect(mockRelatorioService.obterRemanejamentos).toHaveBeenCalled();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('B-202');
    expect(compiled.textContent).toContain('Coordenador');
  });

  it('deve bloquear consulta e exportacao quando data_fim for menor que data_inicio', () => {
    component.selecionarAba('remanejamentos');
    mockRelatorioService.obterRemanejamentos.calls.reset();

    component.filtroDataInicio = '2026-10-31';
    component.filtroDataFim = '2026-10-01';
    component.aplicarFiltros();
    fixture.detectChanges();

    expect(component.erroValidacao()).toContain('data final deve ser maior ou igual');
    expect(mockRelatorioService.obterRemanejamentos).not.toHaveBeenCalled();

    component.exportarCsv();
    expect(mockRelatorioService.exportarRemanejamentosCsv).not.toHaveBeenCalled();
  });

  it('deve desabilitar botao de exportacao enquanto isExporting for verdadeiro', () => {
    exportingSig.set(true);
    fixture.detectChanges();

    const btnExport = fixture.nativeElement.querySelector(
      '[data-testid="btn-exportar-csv"]',
    ) as HTMLButtonElement;
    expect(btnExport).toBeTruthy();
    expect(btnExport.disabled).toBeTrue();
  });

  it('deve acionar exportarOcupacaoCsv na aba de ocupacao e exportarRemanejamentosCsv na aba de remanejamentos', () => {
    component.filtroBloco = 'A';
    component.exportarCsv();
    expect(mockRelatorioService.exportarOcupacaoCsv).toHaveBeenCalledWith(
      jasmine.objectContaining({ bloco: 'A' }),
    );

    component.selecionarAba('remanejamentos');
    component.filtroStatus = 'aprovado';
    component.exportarCsv();
    expect(mockRelatorioService.exportarRemanejamentosCsv).toHaveBeenCalledWith(
      jasmine.objectContaining({ status: 'aprovado' }),
    );
  });

  it('deve navegar entre paginas ajustando skip', () => {
    component.proximaPagina();
    expect(component.skip()).toBe(component.limit);
    expect(mockRelatorioService.obterOcupacaoSalas).toHaveBeenCalledWith(
      jasmine.objectContaining({ skip: component.limit }),
    );

    component.paginaAnterior();
    expect(component.skip()).toBe(0);
  });
});
