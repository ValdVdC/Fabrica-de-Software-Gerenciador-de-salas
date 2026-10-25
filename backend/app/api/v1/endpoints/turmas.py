"""Endpoints para gestao de Turmas com RBAC e isolamento por campus."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, montar_padrao_ilike, require_campus_access, require_role
from app.db.session import get_db
from app.models.academico import Curso, Disciplina, Turma
from app.models.enums import PerfilUsuario, TipoEventoLog
from app.models.usuario import Usuario
from app.schemas.turma import TurmaCreate, TurmaRead, TurmaUpdate
from app.services.log_service import registrar_evento

router = APIRouter()


@router.get("", response_model=list[TurmaRead])
def listar_turmas(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    disciplina_id: int | None = Query(default=None, gt=0),
    campus_id: int | None = Query(default=None, gt=0),
    q: str | None = Query(default=None, max_length=100, description="Busca textual por periodo letivo ou disciplina"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    stmt = select(Turma).join(Disciplina).join(Curso)
    if current_user.perfil != PerfilUsuario.ADMIN:
        stmt = stmt.where(Curso.campus_id == current_user.campus_id)
    elif campus_id is not None:
        stmt = stmt.where(Curso.campus_id == campus_id)
    if disciplina_id is not None:
        stmt = stmt.where(Turma.disciplina_id == disciplina_id)
    if padrao := montar_padrao_ilike(q):
        stmt = stmt.where(
            or_(
                Turma.periodo_letivo.ilike(padrao, escape="\\"),
                Disciplina.nome.ilike(padrao, escape="\\"),
                Disciplina.codigo.ilike(padrao, escape="\\"),
            )
        )
    return db.scalars(stmt.order_by(Turma.id.asc()).offset(skip).limit(limit)).all()


@router.get("/{turma_id}", response_model=TurmaRead)
def obter_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    turma = db.get(Turma, turma_id)
    if not turma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma nao encontrada")
    require_campus_access(turma.disciplina.curso.campus_id, current_user)
    return turma


@router.post("", response_model=TurmaRead, status_code=status.HTTP_201_CREATED)
def criar_turma(
    payload: TurmaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)),
):
    disciplina = db.get(Disciplina, payload.disciplina_id)
    if not disciplina or (current_user.perfil != PerfilUsuario.ADMIN and disciplina.curso.campus_id != current_user.campus_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disciplina nao encontrada")

    if payload.professor_id:
        prof = db.get(Usuario, payload.professor_id)
        if current_user.perfil != PerfilUsuario.ADMIN:
            if not prof or prof.perfil != PerfilUsuario.PROFESSOR or not prof.ativo or prof.campus_id != current_user.campus_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor invalido, inativo ou inexistente")
        else:
            if not prof or prof.perfil != PerfilUsuario.PROFESSOR or not prof.ativo:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Professor invalido, inativo ou inexistente")
            if prof.campus_id != disciplina.curso.campus_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Professor pertence a campus diferente da disciplina")

    turma = Turma(
        disciplina_id=payload.disciplina_id,
        professor_id=payload.professor_id,
        periodo_letivo=payload.periodo_letivo,
        turno_preferido=payload.turno_preferido,
        num_matriculados=0,
    )
    try:
        db.add(turma)
        db.flush()
        registrar_evento(
            db=db,
            tipo=TipoEventoLog.CRIACAO,
            usuario=current_user,
            campus_id=disciplina.curso.campus_id,
            entidade="turma",
            entidade_id=turma.id,
            detalhes=f"Criacao da turma {turma.id} da disciplina {disciplina.codigo}",
        )
        db.commit()
        db.refresh(turma)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito ao criar turma")
    return turma


@router.patch("/{turma_id}", response_model=TurmaRead)
def atualizar_turma(
    turma_id: int,
    payload: TurmaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)
    ),
):
    """Atualiza professor responsavel ou turno da turma com validacao de campus."""
    turma = db.get(Turma, turma_id)
    if not turma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma nao encontrada")

    require_campus_access(turma.disciplina.curso.campus_id, current_user)

    if "professor_id" in payload.model_fields_set:
        if payload.professor_id is None:
            turma.professor_id = None
        else:
            prof = db.get(Usuario, payload.professor_id)
            if current_user.perfil != PerfilUsuario.ADMIN:
                if not prof or prof.perfil != PerfilUsuario.PROFESSOR or not prof.ativo or prof.campus_id != current_user.campus_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor invalido, inativo ou inexistente")
            else:
                if not prof or prof.perfil != PerfilUsuario.PROFESSOR or not prof.ativo:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Professor invalido, inativo ou inexistente")
                if prof.campus_id != turma.disciplina.curso.campus_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Professor pertence a campus diferente da disciplina")
            turma.professor_id = payload.professor_id

    if payload.turno_preferido is not None:
        turma.turno_preferido = payload.turno_preferido

    try:
        registrar_evento(
            db=db,
            tipo=TipoEventoLog.ALTERACAO,
            usuario=current_user,
            campus_id=turma.disciplina.curso.campus_id,
            entidade="turma",
            entidade_id=turma.id,
            detalhes=f"Atualizacao da turma {turma.id} da disciplina {turma.disciplina.codigo}",
        )
        db.commit()
        db.refresh(turma)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito ao atualizar turma")

    return turma
