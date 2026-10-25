"""
Endpoints para gestao de Usuarios.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.campus import Campus
from app.models.usuario import Usuario
from app.models.enums import PerfilUsuario, TipoEventoLog
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.core.security import get_password_hash
from app.api.deps import get_current_user, montar_padrao_ilike, require_role
from app.services.log_service import registrar_evento

router = APIRouter()


@router.get("", response_model=list[UsuarioRead])
def listar_usuarios(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    campus_id: int | None = Query(default=None, gt=0, description="Filtro por ID do campus"),
    q: str | None = Query(default=None, max_length=100, description="Busca textual por nome ou email"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)
    ),
):
    """Lista usuarios respeitando o escopo de campus do usuario autenticado e busca textual."""
    stmt = select(Usuario)
    if current_user.perfil == PerfilUsuario.ADMIN:
        if campus_id is not None:
            stmt = stmt.where(Usuario.campus_id == campus_id)
    else:
        stmt = stmt.where(Usuario.campus_id == current_user.campus_id)

    if padrao := montar_padrao_ilike(q):
        stmt = stmt.where(
            or_(
                Usuario.nome.ilike(padrao, escape="\\"),
                Usuario.email.ilike(padrao, escape="\\"),
            )
        )

    stmt = stmt.order_by(Usuario.id.asc()).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{usuario_id}", response_model=UsuarioRead)
def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    usuario = db.get(Usuario, usuario_id)
    if not usuario or (current_user.perfil != PerfilUsuario.ADMIN and usuario.campus_id != current_user.campus_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")
    if current_user.perfil in (PerfilUsuario.ALUNO, PerfilUsuario.PROFESSOR) and usuario.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: privilegio insuficiente")
    return usuario


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA)),
):
    """Cadastra novo usuario institucional com hash de senha Bcrypt e validacoes de unicidade."""
    # 1. Validacao hierarquica contra escalacao de privilegios (BFLA)
    if current_user.perfil == PerfilUsuario.SECRETARIA:
        if payload.perfil in (PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR, PerfilUsuario.SECRETARIA):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Privilegio insuficiente para conceder este perfil",
            )
    elif current_user.perfil == PerfilUsuario.COORDENADOR:
        if payload.perfil in (PerfilUsuario.ADMIN, PerfilUsuario.COORDENADOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Privilegio insuficiente para conceder este perfil",
            )

    # 2. Validacao de escopo de campus do solicitante (previne oraculo de enumeracao e queries desnecessarias)
    if current_user.perfil != PerfilUsuario.ADMIN and payload.campus_id != current_user.campus_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: restrito ao seu campus")

    # 3. Verificacao de existencia do campus no banco
    campus = db.get(Campus, payload.campus_id)
    if not campus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus nao encontrado")

    stmt = select(Usuario).where(Usuario.email == payload.email)
    if db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ja cadastrado no sistema")

    usuario = Usuario(
        campus_id=payload.campus_id,
        nome=payload.nome,
        email=payload.email,
        senha_hash=get_password_hash(payload.senha),
        perfil=payload.perfil,
        ativo=True,
    )
    try:
        db.add(usuario)
        db.flush()
        registrar_evento(
            db=db,
            tipo=TipoEventoLog.CRIACAO,
            usuario=current_user,
            campus_id=usuario.campus_id,
            entidade="usuario",
            entidade_id=usuario.id,
            detalhes=f"Criacao do usuario {usuario.nome} ({usuario.email})",
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito de unicidade ao cadastrar usuario")
    db.refresh(usuario)
    return usuario
