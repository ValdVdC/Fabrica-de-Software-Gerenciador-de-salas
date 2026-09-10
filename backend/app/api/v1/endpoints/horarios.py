"""Endpoints para gestao e consulta de Horarios e Grade Semanal."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.alocacao import Horario
from app.models.academico import Turma, Disciplina, Matricula
from app.models.sala import Sala
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.horario import HorarioRead, HorarioMeuRead

router = APIRouter()


@router.get("/meus", response_model=list[HorarioMeuRead])
def listar_meus_horarios(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna a grade semanal e horarios contextuais de acordo com o perfil autenticado."""
    stmt = (
        select(Horario, Sala, Turma, Disciplina, Usuario)
        .join(Sala, Horario.sala_id == Sala.id)
        .join(Turma, Horario.turma_id == Turma.id)
        .join(Disciplina, Turma.disciplina_id == Disciplina.id)
        .outerjoin(Usuario, Turma.professor_id == Usuario.id)
    )

    if current_user.perfil == PerfilUsuario.PROFESSOR:
        stmt = stmt.where(Turma.professor_id == current_user.id)
    elif current_user.perfil == PerfilUsuario.ALUNO:
        stmt = stmt.join(Matricula, Matricula.turma_id == Turma.id).where(
            Matricula.aluno_id == current_user.id,
            Matricula.status == "ativa",
        )
    elif current_user.perfil in [PerfilUsuario.SECRETARIA, PerfilUsuario.COORDENADOR]:
        stmt = stmt.where(Horario.campus_id == current_user.campus_id)
    elif current_user.perfil == PerfilUsuario.ADMIN and current_user.campus_id:
        stmt = stmt.where(Horario.campus_id == current_user.campus_id)

    stmt = stmt.order_by(Horario.dia_semana.asc(), Horario.hora_inicio.asc(), Horario.id.asc()).offset(skip).limit(limit)
    rows = db.execute(stmt).all()

    resultado = []
    for h, s, t, d, prof in rows:
        turno_val = t.turno_preferido.value if hasattr(t.turno_preferido, "value") else str(t.turno_preferido)
        tipo_val = s.tipo.value if hasattr(s.tipo, "value") else str(s.tipo)
        resultado.append(
            HorarioMeuRead(
                id=h.id,
                campus_id=h.campus_id,
                turma_id=h.turma_id,
                disciplina_nome=d.nome,
                disciplina_codigo=d.codigo,
                periodo_letivo=t.periodo_letivo,
                turno=turno_val,
                dia_semana=h.dia_semana,
                hora_inicio=h.hora_inicio,
                hora_fim=h.hora_fim,
                sala_id=s.id,
                sala_bloco=s.bloco,
                sala_numero=s.numero,
                sala_tipo=tipo_val,
                professor_id=prof.id if prof else None,
                professor_nome=prof.nome if prof else None,
            )
        )
    return resultado


@router.get("", response_model=list[HorarioRead])
def listar_horarios(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Horario).order_by(Horario.id.asc()).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{horario_id}", response_model=HorarioRead)
def obter_horario(horario_id: int, db: Session = Depends(get_db)):
    horario = db.get(Horario, horario_id)
    if not horario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horario nao encontrado")
    return horario
