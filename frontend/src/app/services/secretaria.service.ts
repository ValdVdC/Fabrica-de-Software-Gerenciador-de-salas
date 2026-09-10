import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, defer, tap, finalize } from 'rxjs';

export interface Curso {
  id: number;
  campus_id: number;
  nome: string;
  codigo: string;
}

export interface CursoCreate {
  campus_id: number;
  nome: string;
  codigo: string;
}

export interface Disciplina {
  id: number;
  curso_id: number;
  nome: string;
  codigo: string;
  carga_horaria: number;
}

export interface DisciplinaCreate {
  curso_id: number;
  nome: string;
  codigo: string;
  carga_horaria: number;
}

export type TurnoType = 'matutino' | 'vespertino' | 'noturno' | 'integral';

export interface Turma {
  id: number;
  disciplina_id: number;
  professor_id: number | null;
  periodo_letivo: string;
  turno_preferido: TurnoType;
  num_matriculados: number;
}

export interface TurmaCreate {
  disciplina_id: number;
  professor_id?: number | null;
  periodo_letivo: string;
  turno_preferido: TurnoType;
}

export interface Matricula {
  id: number;
  aluno_id: number;
  turma_id: number;
  data_matricula: string;
  status: string;
}

export interface MatriculaCreate {
  aluno_id: number;
  turma_id: number;
}

@Injectable({ providedIn: 'root' })
export class SecretariaService {
  private readonly http = inject(HttpClient);

  private readonly _cursos = signal<Curso[]>([]);
  readonly cursos = this._cursos.asReadonly();

  private readonly _disciplinas = signal<Disciplina[]>([]);
  readonly disciplinas = this._disciplinas.asReadonly();

  private readonly _turmas = signal<Turma[]>([]);
  readonly turmas = this._turmas.asReadonly();

  private readonly _matriculas = signal<Matricula[]>([]);
  readonly matriculas = this._matriculas.asReadonly();

  private readonly _activeRequests = signal<number>(0);
  readonly isLoading = computed(() => this._activeRequests() > 0);

  private readonly _errorMessage = signal<string | null>(null);
  readonly errorMessage = this._errorMessage.asReadonly();

  private validarId(id: unknown, msg: string): void {
    if (!Number.isInteger(id) || (id as number) <= 0) throw new Error(msg);
  }

  private buildParams(entries: [string, number | undefined, string][]): HttpParams | undefined {
    let p = new HttpParams();
    for (const [key, val, label] of entries) {
      if (val !== undefined && val !== null) {
        this.validarId(val, `Identificador de ${label} invalido`);
        p = p.set(key, val.toString());
      }
    }
    return p.keys().length ? p : undefined;
  }

  private reqGet<T>(
    url: string,
    params: HttpParams | undefined,
    onSucesso: (d: T) => void,
  ): Observable<T> {
    return this.executar(this.http.get<T>(url, { params }), onSucesso);
  }

  listarCursos(campusId?: number): Observable<Curso[]> {
    return this.reqGet(
      '/api/v1/cursos',
      this.buildParams([['campus_id', campusId, 'campus']]),
      (d) => this._cursos.set(d),
    );
  }

  criarCurso(payload: CursoCreate): Observable<Curso> {
    this.validarId(payload?.campus_id, 'Dados de curso invalidos');
    if (!payload.nome?.trim() || !payload.codigo?.trim())
      throw new Error('Dados de curso invalidos');
    return this.executar(this.http.post<Curso>('/api/v1/cursos', payload), (n) =>
      this._cursos.update((l) => [...l, n]),
    );
  }

  listarDisciplinas(cursoId?: number, campusId?: number): Observable<Disciplina[]> {
    const params = this.buildParams([
      ['curso_id', cursoId, 'curso'],
      ['campus_id', campusId, 'campus'],
    ]);
    return this.reqGet('/api/v1/disciplinas', params, (d) => this._disciplinas.set(d));
  }

  criarDisciplina(payload: DisciplinaCreate): Observable<Disciplina> {
    this.validarId(payload?.curso_id, 'Dados de disciplina invalidos');
    this.validarId(payload?.carga_horaria, 'Dados de disciplina invalidos');
    if (!payload.nome?.trim() || !payload.codigo?.trim())
      throw new Error('Dados de disciplina invalidos');
    return this.executar(this.http.post<Disciplina>('/api/v1/disciplinas', payload), (n) =>
      this._disciplinas.update((l) => [...l, n]),
    );
  }

  listarTurmas(disciplinaId?: number, campusId?: number): Observable<Turma[]> {
    const params = this.buildParams([
      ['disciplina_id', disciplinaId, 'disciplina'],
      ['campus_id', campusId, 'campus'],
    ]);
    return this.reqGet('/api/v1/turmas', params, (d) => this._turmas.set(d));
  }

  obterTurma(turmaId: number): Observable<Turma> {
    this.validarId(turmaId, 'Identificador de turma invalido');
    return this.executar(this.http.get<Turma>(`/api/v1/turmas/${turmaId}`));
  }

  criarTurma(payload: TurmaCreate): Observable<Turma> {
    this.validarId(payload?.disciplina_id, 'Dados de turma invalidos');
    if (!payload?.periodo_letivo?.trim() || !payload.turno_preferido)
      throw new Error('Dados de turma invalidos');
    if (payload.professor_id !== undefined && payload.professor_id !== null) {
      this.validarId(payload.professor_id, 'Identificador de professor invalido');
    }
    return this.executar(this.http.post<Turma>('/api/v1/turmas', payload), (n) =>
      this._turmas.update((l) => [...l, n]),
    );
  }

  listarMatriculas(turmaId?: number): Observable<Matricula[]> {
    return this.reqGet(
      '/api/v1/matriculas',
      this.buildParams([['turma_id', turmaId, 'turma']]),
      (d) => this._matriculas.set(d),
    );
  }

  matricularAluno(payload: MatriculaCreate): Observable<Matricula> {
    this.validarId(payload?.aluno_id, 'Dados de matricula invalidos');
    this.validarId(payload?.turma_id, 'Dados de matricula invalidos');
    return this.executar(this.http.post<Matricula>('/api/v1/matriculas', payload), (n) => {
      this._matriculas.update((l) => [...l, n]);
      this._turmas.update((l) =>
        l.map((t) =>
          t.id === n.turma_id ? { ...t, num_matriculados: t.num_matriculados + 1 } : t,
        ),
      );
    });
  }

  limparErro(): void {
    this._errorMessage.set(null);
  }

  resetState(): void {
    this._cursos.set([]);
    this._disciplinas.set([]);
    this._turmas.set([]);
    this._matriculas.set([]);
    this._activeRequests.set(0);
    this._errorMessage.set(null);
  }

  private executar<T>(source: Observable<T>, onSucesso?: (data: T) => void): Observable<T> {
    return defer(() => {
      this._activeRequests.update((c) => c + 1);
      this._errorMessage.set(null);
      return source.pipe(
        tap({
          next: (res) => {
            if (onSucesso) onSucesso(res);
          },
          error: (err) => this._errorMessage.set(this.extrairErro(err)),
        }),
        finalize(() => this._activeRequests.update((c) => Math.max(0, c - 1))),
      );
    });
  }

  private extrairErro(err: any): string {
    if (!err) return 'Erro desconhecido na requisicao';
    if (err.status === 0) return 'Nao foi possivel conectar ao servidor';
    if (err.status >= 500) return 'Erro interno no servidor. Tente novamente mais tarde.';
    const d = err.error?.detail;
    if (Array.isArray(d)) {
      const m = d.map((x: any) => x?.msg).filter(Boolean);
      return m.length ? m.join('; ') : 'Dados de entrada invalidos';
    }
    if (typeof d === 'object' && d !== null) return d.message || d.msg || 'Requisicao invalida';
    return d ? String(d) : err.statusText || 'Erro na requisicao';
  }
}
