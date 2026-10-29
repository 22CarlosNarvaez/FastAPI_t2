from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MetodoPago(str, Enum):
    tarjeta = "tarjeta"
    nequi = "nequi"
    transferencia = "transferencia"


class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int = Field(gt=0)


class PedidoCreate(BaseModel):
    items: list[ItemPedido] = Field(min_length=1)


class PagoPedido(BaseModel):
    metodo_pago: MetodoPago
    direccion: str = Field(min_length=5, max_length=180)
    telefono: str = Field(pattern=r"^\+?[0-9][0-9\s-]{6,15}$")
    codigo_postal: str = Field(pattern=r"^[0-9]{6}$")


class ItemPedidoOut(BaseModel):
    producto_id: str
    nombre: str
    precio_unitario: float
    cantidad: int
    subtotal: float


class PedidoOut(BaseModel):
    id: str
    usuario_id: str
    usuario_email: str
    items: list[ItemPedidoOut]
    total: float
    estado: str
    fecha: datetime
    metodo_pago: MetodoPago | None = None
    direccion_envio: str | None = None
    telefono_envio: str | None = None
    codigo_postal: str | None = None