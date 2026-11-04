import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_token
from app.core.database import col_usuarios

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise error
    user = col_usuarios.find_one({"email": payload.get("sub")})
    if not user:
        raise error
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["rol"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo administradores")
    return user