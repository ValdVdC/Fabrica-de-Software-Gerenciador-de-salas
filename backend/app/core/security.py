"""Utilitarios de criptografia e manipulacao de tokens JWT."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import bcrypt
from jose import jwt, JWTError

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Valida correspondencia entre senha plana e hash bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Gera hash seguro bcrypt para a senha informada."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Gera token JWT assinado com algoritmo HS256."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica e valida assinatura de token JWT."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise ValueError("Token invalido ou expirado") from exc
