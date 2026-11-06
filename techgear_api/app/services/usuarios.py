from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password, verify_password
from app.core.database import col_usuarios
from app.models.usuario import Rol, UsuarioRegistro
from app.services.productos import to_object_id

DEFAULT_ADMIN_EMAIL = "admin@gmail.com"
DEFAULT_ADMIN_PASSWORD = "1234567"


def to_out(doc: dict) -> dict:
    return {"id": str(doc["_id"]), "nombre": doc["nombre"], "email": doc["email"], "rol": doc["rol"]}


def _ensure_default_admin() -> dict:
    user = col_usuarios.find_one({"email": DEFAULT_ADMIN_EMAIL.lower()})
    if user:
        return user
    doc = {
        "nombre": "Administrador",
        "email": DEFAULT_ADMIN_EMAIL.lower(),
        "password": hash_password(DEFAULT_ADMIN_PASSWORD),
        "rol": Rol.admin.value,
    }
    res = col_usuarios.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


def crear_usuario(data: UsuarioRegistro) -> dict:
    if data.rol == Rol.admin or data.email.lower() == DEFAULT_ADMIN_EMAIL.lower():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El administrador usa credenciales fijas y no requiere registro.")
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
    cleaned_email = (email or "").lower()
    if cleaned_email == DEFAULT_ADMIN_EMAIL.lower() and password == DEFAULT_ADMIN_PASSWORD:
        return _ensure_default_admin()

    user = col_usuarios.find_one({"email": cleaned_email})
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