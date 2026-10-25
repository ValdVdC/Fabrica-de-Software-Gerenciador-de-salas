import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { HistoricoComponent } from './historico.component';
import { LogService, LogRead } from '../../services/log.service';
import { AuthService } from '../../services/auth.service';

describe('HistoricoComponent', () => {
  let component: HistoricoComponent;
  let fixture: ComponentFixture<HistoricoComponent>;

  const logsSig = signal<LogRead[]>([]);
  const loadingSig = signal<boolean>(false);
  const exportingSig = signal<boolean>(false);
  const errorSig = signal<string | null>(null);

  let mockLogService: any;
  let mockAuthService: any;

  beforeEach(async () => {
    logsSig.set([
      {
        id: 101,
        campus_id: 1,
        horario_id: 10,
        snapshot_evento: { entidade: 'sala', id: 5 },
        tipo_evento: 'remanejamento',
        usuario_responsavel: 3,
        detalhes: 'Remanejamento aprovado da sala A-101 para B-202',
        timestamp: '2026-10-20T14:30:00Z',
      },
    ]);
    loadingSig.set(false);
    exportingSig.set(false);
    errorSig.set(null);

    mockLogService = {
      logs: logsSig.asReadonly(),
      isLoading: loadingSig.asReadonly(),
      isExporting: exportingSig.asReadonly(),
      errorMessage: errorSig.asReadonly(),
      listarLogs: jasmine.createSpy('listarLogs').and.callFake(() => of(logsSig())),
      exportarLogsCsv: jasmine.createSpy('exportarLogsCsv').and.returnValue(of(new Blob(['csv']))),
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
      imports: [HistoricoComponent],
      providers: [
        { provide: LogService, useValue: mockLogService },
        { provide: AuthService, useValue: mockAuthService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HistoricoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('deve carregar trilha de auditoria ao inicializar em modo somente leitura', () => {
    expect(mockLogService.listarLogs).toHaveBeenCalled();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('#101');
    expect(compiled.textContent).toContain('Remanejamento aprovado');
  });

  it('deve bloquear consulta e exportacao quando data_fim for menor que data_inicio', () => {
    mockLogService.listarLogs.calls.reset();
    component.filtroDataInicio = '2026-10-31';
    component.filtroDataFim = '2026-10-01';
    component.aplicarFiltros();
    fixture.detectChanges();

    expect(component.erroValidacao()).toContain('data final deve ser maior ou igual');
    expect(mockLogService.listarLogs).not.toHaveBeenCalled();

    component.exportarCsv();
    expect(mockLogService.exportarLogsCsv).not.toHaveBeenCalled();
  });

  it('deve desabilitar botao de exportacao enquanto isExporting for verdadeiro', () => {
    exportingSig.set(true);
    fixture.detectChanges();

    const btnExport = fixture.nativeElement.querySelector(
      '[data-testid="btn-exportar-logs-csv"]',
    ) as HTMLButtonElement;
    expect(btnExport).toBeTruthy();
    expect(btnExport.disabled).toBeTrue();
  });

  it('deve aplicar filtros combinados e exportar CSV com os mesmos filtros', () => {
    component.filtroTipoEvento = 'remanejamento';
    component.filtroUsuarioId = 3;
    component.aplicarFiltros();

    expect(mockLogService.listarLogs).toHaveBeenCalledWith(
      jasmine.objectContaining({ tipo_evento: 'remanejamento', usuario_id: 3, skip: 0 }),
    );

    component.exportarCsv();
    expect(mockLogService.exportarLogsCsv).toHaveBeenCalledWith(
      jasmine.objectContaining({ tipo_evento: 'remanejamento', usuario_id: 3 }),
    );
  });

  it('deve navegar entre paginas ajustando skip', () => {
    component.proximaPagina();
    expect(component.skip()).toBe(component.limit);
    expect(mockLogService.listarLogs).toHaveBeenCalledWith(
      jasmine.objectContaining({ skip: component.limit }),
    );

    component.paginaAnterior();
    expect(component.skip()).toBe(0);
  });
});
