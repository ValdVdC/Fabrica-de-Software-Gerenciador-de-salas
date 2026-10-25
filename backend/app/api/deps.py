"""Dependencias globais da API: extracao de usuario logado e controle RBAC."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.usuario import Usuario
from app.models.enums import PerfilUsuario
from app.core.security import decode_access_token

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> Usuario:
    """Extrai e valida o usuario ativo a partir do token Bearer JWT."""
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido: identificador ausente",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = int(user_id_str)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas ou token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(Usuario, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario associado ao token nao encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inativo no sistema",
        )
    return user


def require_role(*roles: PerfilUsuario):
    """Fabrica de dependencia para controle de acesso estrito baseado em perfil (RBAC)."""
    def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.perfil not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: privilegio insuficiente",
            )
        return current_user
    return role_checker


def require_campus_access(resource_campus_id: int | None, current_user: Usuario) -> None:
    """Valida permissao de acesso ao campus do recurso para prevencao de BOLA/IDOR.

    Perfil ADMIN possui autorizacao global.
    Demais perfis exigem correspondencia com current_user.campus_id com fail-closed estrito.
    Retorna 404 Not Found em divergencia ou invalidade para mitigar vazamento de existencia.
    """
    if current_user.perfil == PerfilUsuario.ADMIN:
        return
    if (
        resource_campus_id is None
        or current_user.campus_id is None
        or isinstance(resource_campus_id, bool)
        or not isinstance(resource_campus_id, int)
        or resource_campus_id <= 0
        or resource_campus_id != current_user.campus_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso nao encontrado",
        )


def montar_padrao_ilike(q: str | None) -> str | None:
    """Normaliza e escapa curingas SQL (\\, % e _) para busca textual literal via ilike."""
    if q is None:
        return None
    termo = q.strip()
    if not termo:
        return None
    escapado = termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"
