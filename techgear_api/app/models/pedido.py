from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from app.models.producto import ObjectIdStr


class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int = Field(gt=0)
    precio_unitario: float = Field(gt=0)


class PedidoCreate(BaseModel):
    cliente: str = Field(min_length=1)
    documento_cliente: str = Field(min_length=1, max_length=30)
    items: list[ItemPedido] = Field(min_length=1)


class Pedido(PedidoCreate):
    model_config = ConfigDict(populate_by_name=True)

    id: ObjectIdStr = Field(alias="_id")
    total: float
    creado_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
