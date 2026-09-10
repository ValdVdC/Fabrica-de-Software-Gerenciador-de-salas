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

  listarCursos(campusId?: number): Observable<Curso[]> {
    let params: HttpParams | undefined;
    if (campusId !== undefined && campusId !== null) {
      if (!Number.isInteger(campusId) || campusId <= 0)
        throw new Error('Identificador de campus invalido');
      params = new HttpParams().set('campus_id', campusId.toString());
    }
    return this.executar(this.http.get<Curso[]>('/api/v1/cursos', { params }), (d) =>
      this._cursos.set(d),
    );
  }

  criarCurso(payload: CursoCreate): Observable<Curso> {
    if (
      !payload ||
      !Number.isInteger(payload.campus_id) ||
      payload.campus_id <= 0 ||
      !payload.nome?.trim() ||
      !payload.codigo?.trim()
    ) {
      throw new Error('Dados de curso invalidos');
    }
    return this.executar(this.http.post<Curso>('/api/v1/cursos', payload), (n) =>
      this._cursos.update((l) => [...l, n]),
    );
  }

  listarDisciplinas(cursoId?: number, campusId?: number): Observable<Disciplina[]> {
    let params = new HttpParams();
    if (cursoId !== undefined && cursoId !== null) {
      if (!Number.isInteger(cursoId) || cursoId <= 0)
        throw new Error('Identificador de curso invalido');
      params = params.set('curso_id', cursoId.toString());
    }
    if (campusId !== undefined && campusId !== null) {
      if (!Number.isInteger(campusId) || campusId <= 0)
        throw new Error('Identificador de campus invalido');
      params = params.set('campus_id', campusId.toString());
    }
    return this.executar(
      this.http.get<Disciplina[]>('/api/v1/disciplinas', {
        params: params.keys().length > 0 ? params : undefined,
      }),
      (d) => this._disciplinas.set(d),
    );
  }

  criarDisciplina(payload: DisciplinaCreate): Observable<Disciplina> {
    if (
      !payload ||
      !Number.isInteger(payload.curso_id) ||
      payload.curso_id <= 0 ||
      !payload.nome?.trim() ||
      !payload.codigo?.trim() ||
      !Number.isInteger(payload.carga_horaria) ||
      payload.carga_horaria <= 0
    ) {
      throw new Error('Dados de disciplina invalidos');
    }
    return this.executar(this.http.post<Disciplina>('/api/v1/disciplinas', payload), (n) =>
      this._disciplinas.update((l) => [...l, n]),
    );
  }

  listarTurmas(disciplinaId?: number, campusId?: number): Observable<Turma[]> {
    let params = new HttpParams();
    if (disciplinaId !== undefined && disciplinaId !== null) {
      if (!Number.isInteger(disciplinaId) || disciplinaId <= 0)
        throw new Error('Identificador de disciplina invalido');
      params = params.set('disciplina_id', disciplinaId.toString());
    }
    if (campusId !== undefined && campusId !== null) {
      if (!Number.isInteger(campusId) || campusId <= 0)
        throw new Error('Identificador de campus invalido');
      params = params.set('campus_id', campusId.toString());
    }
    return this.executar(
      this.http.get<Turma[]>('/api/v1/turmas', {
        params: params.keys().length > 0 ? params : undefined,
      }),
      (d) => this._turmas.set(d),
    );
  }

  obterTurma(turmaId: number): Observable<Turma> {
    if (!Number.isInteger(turmaId) || turmaId <= 0)
      throw new Error('Identificador de turma invalido');
    return this.executar(this.http.get<Turma>(`/api/v1/turmas/${turmaId}`));
  }

  criarTurma(payload: TurmaCreate): Observable<Turma> {
    if (
      !payload ||
      !Number.isInteger(payload.disciplina_id) ||
      payload.disciplina_id <= 0 ||
      !payload.periodo_letivo?.trim() ||
      !payload.turno_preferido
    ) {
      throw new Error('Dados de turma invalidos');
    }
    if (
      payload.professor_id !== undefined &&
      payload.professor_id !== null &&
      (!Number.isInteger(payload.professor_id) || payload.professor_id <= 0)
    ) {
      throw new Error('Identificador de professor invalido');
    }
    return this.executar(this.http.post<Turma>('/api/v1/turmas', payload), (n) =>
      this._turmas.update((l) => [...l, n]),
    );
  }

  listarMatriculas(turmaId?: number): Observable<Matricula[]> {
    let params: HttpParams | undefined;
    if (turmaId !== undefined && turmaId !== null) {
      if (!Number.isInteger(turmaId) || turmaId <= 0)
        throw new Error('Identificador de turma invalido');
      params = new HttpParams().set('turma_id', turmaId.toString());
    }
    return this.executar(this.http.get<Matricula[]>('/api/v1/matriculas', { params }), (d) =>
      this._matriculas.set(d),
    );
  }

  matricularAluno(payload: MatriculaCreate): Observable<Matricula> {
    if (
      !payload ||
      !Number.isInteger(payload.aluno_id) ||
      payload.aluno_id <= 0 ||
      !Number.isInteger(payload.turma_id) ||
      payload.turma_id <= 0
    ) {
      throw new Error('Dados de matricula invalidos');
    }
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
    const detail = err.error?.detail;
    if (detail) {
      if (Array.isArray(detail)) {
        const msgs = detail
          .map((d: any) => (d && typeof d === 'object' && d.msg ? String(d.msg) : null))
          .filter(Boolean);
        return msgs.length > 0 ? msgs.join('; ') : 'Dados de entrada invalidos';
      }
      if (typeof detail === 'object') return detail.message || detail.msg || 'Requisicao invalida';
      return String(detail);
    }
    return err.statusText || 'Erro na requisicao';
  }
}
