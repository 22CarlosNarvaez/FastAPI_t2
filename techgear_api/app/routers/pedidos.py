from fastapi import APIRouter, Depends, status

from app.core.deps import get_current_user, require_admin
from app.models.pedido import PagoPedido, PedidoCreate, PedidoOut
from app.services import pedidos as svc

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def crear(data: PedidoCreate, user: dict = Depends(get_current_user)):
    return svc.crear(user, data)


@router.get("", response_model=list[PedidoOut])
def listar(user: dict = Depends(get_current_user)):
    return svc.listar_para(user)


@router.post("/{pedido_id}/pagar", response_model=PedidoOut)
def pagar(pedido_id: str, data: PagoPedido, user: dict = Depends(get_current_user)):
    return svc.pagar(pedido_id, user, data)


@router.patch("/{pedido_id}/enviar", response_model=PedidoOut)
def marcar_enviado(pedido_id: str, user: dict = Depends(require_admin)):
    return svc.marcar_enviado(pedido_id, user)


@router.patch("/{pedido_id}/recibir", response_model=PedidoOut)
def marcar_recibido(pedido_id: str, user: dict = Depends(get_current_user)):
    return svc.marcar_recibido(pedido_id, user)