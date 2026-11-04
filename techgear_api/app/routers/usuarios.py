from fastapi import APIRouter, Depends, status

from app.core.deps import get_current_user, require_admin
from app.models.usuario import RolUpdate, UsuarioOut, UsuarioRegistro
from app.services import usuarios as svc

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("/registro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registro(data: UsuarioRegistro):
    return svc.crear_usuario(data)


@router.get("/me", response_model=UsuarioOut)
def me(user: dict = Depends(get_current_user)):
    return svc.to_out(user)


@router.get("", response_model=list[UsuarioOut], dependencies=[Depends(require_admin)])
def listar():
    return svc.listar_usuarios()


@router.patch("/{usuario_id}/rol", response_model=UsuarioOut, dependencies=[Depends(require_admin)])
def cambiar_rol(usuario_id: str, data: RolUpdate):
    return svc.cambiar_rol(usuario_id, data.rol)