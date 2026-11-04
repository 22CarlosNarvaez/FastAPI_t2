from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.database import col_usuarios
from app.models.usuario import Rol, UsuarioRegistro
from app.services.productos import to_object_id


def to_out(doc: dict) -> dict:
    return {"id": str(doc["_id"]), "nombre": doc["nombre"], "email": doc["email"], "rol": doc["rol"]}


def crear_usuario(data: UsuarioRegistro) -> dict:
    codigo = settings.admin_registration_code
    if data.rol == Rol.admin and (not codigo or data.codigo_admin != codigo):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Código de administrador incorrecto")
    doc = {
        "nombre": data.nombre,
        "email": data.email.lower(),
        "password": hash_password(data.password),
        "rol": data.rol.value,
    }
    try:
        res = col_usuarios.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese correo ya está registrado")
    doc["_id"] = res.inserted_id
    return to_out(doc)


def autenticar(email: str, password: str) -> dict:
    user = col_usuarios.find_one({"email": email.lower()})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos")
    return user


def listar_usuarios() -> list[dict]:
    return [to_out(u) for u in col_usuarios.find().sort("nombre", 1)]


def cambiar_rol(usuario_id: str, rol: Rol) -> dict:
    user = col_usuarios.find_one_and_update(
        {"_id": to_object_id(usuario_id)}, {"$set": {"rol": rol.value}}, return_document=True
    )
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return to_out(user)