from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.deps import get_current_user, get_optional_user, require_admin
from app.models.pedido import PagoPedido, PedidoCreate, PedidoOut
from app.services import pedidos as svc

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def crear(
    data: PedidoCreate,
    user: dict | None = Depends(get_optional_user),
    guest_id: UUID | None = Header(None, alias="X-Guest-ID"),
):
    if user is None and guest_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inicia sesión o continúa como invitado")
    return svc.crear(user, data, str(guest_id) if guest_id else None)


@router.get("", response_model=list[PedidoOut])
def listar(
    user: dict | None = Depends(get_optional_user),
    guest_id: UUID | None = Header(None, alias="X-Guest-ID"),
):
    if user is None and guest_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inicia sesión o continúa como invitado")
    return svc.listar_para(user, str(guest_id) if guest_id else None)


@router.post("/{pedido_id}/pagar", response_model=PedidoOut)
def pagar(
    pedido_id: str,
    data: PagoPedido,
    user: dict | None = Depends(get_optional_user),
    guest_id: UUID | None = Header(None, alias="X-Guest-ID"),
):
    if user is None and guest_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inicia sesión o continúa como invitado")
    return svc.pagar(pedido_id, user, data, str(guest_id) if guest_id else None)


@router.patch("/{pedido_id}/enviar", response_model=PedidoOut)
def marcar_enviado(pedido_id: str, user: dict = Depends(require_admin)):
    return svc.marcar_enviado(pedido_id, user)


@router.patch("/{pedido_id}/recibir", response_model=PedidoOut)
def marcar_recibido(
    pedido_id: str,
    user: dict | None = Depends(get_optional_user),
    guest_id: UUID | None = Header(None, alias="X-Guest-ID"),
):
    if user is None and guest_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inicia sesión o continúa como invitado")
    return svc.marcar_recibido(pedido_id, user, str(guest_id) if guest_id else None)