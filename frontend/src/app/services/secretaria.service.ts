import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, finalize } from 'rxjs';

export interface Curso {
  id: number;
  campus_id: number;
  nome: string;
  codigo: string;
  ativo: boolean;
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
  ativo: boolean;
}

export interface DisciplinaCreate {
  curso_id: number;
  nome: string;
  codigo: string;
  carga_horaria: number;
}

export interface Turma {
  id: number;
  disciplina_id: number;
  professor_id: number | null;
  periodo_letivo: string;
  turno_preferido: 'matutino' | 'vespertino' | 'noturno';
  num_matriculados: number;
}

export interface TurmaCreate {
  disciplina_id: number;
  professor_id?: number | null;
  periodo_letivo: string;
  turno_preferido: 'matutino' | 'vespertino' | 'noturno';
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
      if (!Number.isInteger(campusId) || campusId <= 0) {
        throw new Error('Identificador de campus invalido');
      }
      params = new HttpParams().set('campus_id', campusId.toString());
    }
    return this.executar(this.http.get<Curso[]>('/api/v1/cursos', { params }), (dados) =>
      this._cursos.set(dados),
    );
  }

  criarCurso(payload: CursoCreate): Observable<Curso> {
    return this.executar(this.http.post<Curso>('/api/v1/cursos', payload), (novo) =>
      this._cursos.update((lista) => [...lista, novo]),
    );
  }

  listarDisciplinas(cursoId?: number, campusId?: number): Observable<Disciplina[]> {
    let params = new HttpParams();
    if (cursoId !== undefined && cursoId !== null) {
      if (!Number.isInteger(cursoId) || cursoId <= 0) {
        throw new Error('Identificador de curso invalido');
      }
      params = params.set('curso_id', cursoId.toString());
    }
    if (campusId !== undefined && campusId !== null) {
      if (!Number.isInteger(campusId) || campusId <= 0) {
        throw new Error('Identificador de campus invalido');
      }
      params = params.set('campus_id', campusId.toString());
    }
    return this.executar(
      this.http.get<Disciplina[]>('/api/v1/disciplinas', {
        params: params.keys().length > 0 ? params : undefined,
      }),
      (dados) => this._disciplinas.set(dados),
    );
  }

  criarDisciplina(payload: DisciplinaCreate): Observable<Disciplina> {
    return this.executar(this.http.post<Disciplina>('/api/v1/disciplinas', payload), (nova) =>
      this._disciplinas.update((lista) => [...lista, nova]),
    );
  }

  listarTurmas(disciplinaId?: number, campusId?: number): Observable<Turma[]> {
    let params = new HttpParams();
    if (disciplinaId !== undefined && disciplinaId !== null) {
      if (!Number.isInteger(disciplinaId) || disciplinaId <= 0) {
        throw new Error('Identificador de disciplina invalido');
      }
      params = params.set('disciplina_id', disciplinaId.toString());
    }
    if (campusId !== undefined && campusId !== null) {
      if (!Number.isInteger(campusId) || campusId <= 0) {
        throw new Error('Identificador de campus invalido');
      }
      params = params.set('campus_id', campusId.toString());
    }
    return this.executar(
      this.http.get<Turma[]>('/api/v1/turmas', {
        params: params.keys().length > 0 ? params : undefined,
      }),
      (dados) => this._turmas.set(dados),
    );
  }

  obterTurma(turmaId: number): Observable<Turma> {
    if (!Number.isInteger(turmaId) || turmaId <= 0) {
      throw new Error('Identificador de turma invalido');
    }
    return this.executar(this.http.get<Turma>(`/api/v1/turmas/${turmaId}`));
  }

  criarTurma(payload: TurmaCreate): Observable<Turma> {
    return this.executar(this.http.post<Turma>('/api/v1/turmas', payload), (nova) =>
      this._turmas.update((lista) => [...lista, nova]),
    );
  }

  listarMatriculas(turmaId?: number): Observable<Matricula[]> {
    let params: HttpParams | undefined;
    if (turmaId !== undefined && turmaId !== null) {
      if (!Number.isInteger(turmaId) || turmaId <= 0) {
        throw new Error('Identificador de turma invalido');
      }
      params = new HttpParams().set('turma_id', turmaId.toString());
    }
    return this.executar(this.http.get<Matricula[]>('/api/v1/matriculas', { params }), (dados) =>
      this._matriculas.set(dados),
    );
  }

  matricularAluno(payload: MatriculaCreate): Observable<Matricula> {
    return this.executar(this.http.post<Matricula>('/api/v1/matriculas', payload), (nova) =>
      this._matriculas.update((lista) => [...lista, nova]),
    );
  }

  limparErro(): void {
    this._errorMessage.set(null);
  }

  private executar<T>(obs: Observable<T>, onSuccess?: (data: T) => void): Observable<T> {
    this._activeRequests.update((v) => v + 1);
    this._errorMessage.set(null);
    return obs.pipe(
      tap({
        next: (res) => {
          if (onSuccess) onSuccess(res);
        },
        error: (err) => {
          if (err.status >= 500) {
            this._errorMessage.set('Erro interno no servidor. Tente novamente mais tarde.');
          } else {
            const detail = err.error?.detail;
            this._errorMessage.set(typeof detail === 'string' ? detail : 'Erro na requisicao.');
          }
        },
      }),
      finalize(() => this._activeRequests.update((v) => Math.max(0, v - 1))),
    );
  }
}
