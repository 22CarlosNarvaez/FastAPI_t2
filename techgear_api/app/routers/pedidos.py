from fastapi import APIRouter, HTTPException, status

from app.models.pedido import Pedido, PedidoCreate
from app.services import pedidos as servicio

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.post("/", response_model=Pedido, status_code=status.HTTP_201_CREATED)
async def crear_pedido(datos: PedidoCreate):
    return await servicio.crear(datos)


@router.get("/", response_model=list[Pedido])
async def listar_pedidos():
    return await servicio.listar()


@router.get("/{pedido_id}", response_model=Pedido)
async def obtener_pedido(pedido_id: str):
    pedido = await servicio.obtener(pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido