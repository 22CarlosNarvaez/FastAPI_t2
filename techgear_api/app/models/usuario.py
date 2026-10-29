from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Rol(str, Enum):
    cliente = "cliente"
    admin = "admin"


class UsuarioRegistro(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    rol: Rol = Rol.cliente
    codigo_admin: str | None = None


class UsuarioOut(BaseModel):
    id: str
    nombre: str
    email: EmailStr
    rol: Rol


class RolUpdate(BaseModel):
    rol: Rol


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut