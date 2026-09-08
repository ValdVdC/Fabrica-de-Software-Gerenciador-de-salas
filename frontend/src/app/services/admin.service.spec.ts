import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AdminService, Sala, Equipamento, SalaCreate } from './admin.service';

describe('AdminService', () => {
  let service: AdminService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AdminService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('lista salas e equipamentos atualizando signals', () => {
    const mockSalas: Sala[] = [
      {
        id: 1,
        campus_id: 1,
        bloco: 'A',
        numero: '101',
        tipo: 'regular',
        capacidade: 40,
        turnos_disponiveis: ['matutino'],
        ativo: true,
      },
    ];
    const mockEquips: Equipamento[] = [
      { id: 1, nome: 'Projetor HD', descricao: 'Sala aula', created_at: '2026-09-08' },
    ];

    service.listarSalas().subscribe((res) => expect(res.length).toBe(1));
    httpMock.expectOne('/api/v1/salas').flush(mockSalas);
    expect(service.salas().length).toBe(1);

    service.listarEquipamentos().subscribe((res) => expect(res.length).toBe(1));
    httpMock.expectOne('/api/v1/equipamentos').flush(mockEquips);
    expect(service.equipamentos().length).toBe(1);
  });

  it('cria sala e equipamento com sucesso', () => {
    const payloadSala: SalaCreate = {
      campus_id: 1,
      bloco: 'B',
      numero: '202',
      tipo: 'laboratorio',
      capacidade: 30,
      turnos_disponiveis: ['vespertino'],
    };
    const mockSala: Sala = { id: 2, ...payloadSala, tipo: 'laboratorio', ativo: true };

    service.criarSala(payloadSala).subscribe((res) => expect(res.id).toBe(2));
    httpMock.expectOne('/api/v1/salas').flush(mockSala);
    expect(service.salas().some((s) => s.id === 2)).toBeTrue();

    service
      .criarEquipamento({ nome: 'Caixa de Som' })
      .subscribe((res) => expect(res.nome).toBe('Caixa de Som'));
    httpMock
      .expectOne('/api/v1/equipamentos')
      .flush({ id: 2, nome: 'Caixa de Som', created_at: '2026-09-08' });
    expect(service.equipamentos().some((e) => e.id === 2)).toBeTrue();
  });

  it('associa equipamento a sala com quantidade', () => {
    service
      .associarEquipamento(1, { equipamento_id: 1, quantidade: 2 })
      .subscribe((res) => expect(res.quantidade).toBe(2));
    httpMock
      .expectOne('/api/v1/salas/1/equipamentos')
      .flush({ sala_id: 1, equipamento_id: 1, quantidade: 2 });
  });

  it('trata erro HTTP 409 e atualiza errorMessage', () => {
    service.criarEquipamento({ nome: 'Duplicado' }).subscribe({
      error: () => {
        expect(service.errorMessage()).toBe('Ja existe equipamento com este nome');
        expect(service.isLoading()).toBeFalse();
      },
    });
    httpMock
      .expectOne('/api/v1/equipamentos')
      .flush(
        { detail: 'Ja existe equipamento com este nome' },
        { status: 409, statusText: 'Conflict' },
      );
  });
});
