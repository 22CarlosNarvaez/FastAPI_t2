from datetime import datetime, timezone

from app.core.database import get_database
from app.models.pedido import PedidoCreate
from app.services.productos import _a_objectid

COLECCION = "pedidos"


async def crear(datos: PedidoCreate) -> dict:
    documento = datos.model_dump()
    documento["total"] = sum(i["cantidad"] * i["precio_unitario"] for i in documento["items"])
    documento["creado_en"] = datetime.now(timezone.utc)
    resultado = await get_database()[COLECCION].insert_one(documento)
    documento["_id"] = resultado.inserted_id
    return documento


async def listar() -> list[dict]:
    return await get_database()[COLECCION].find().to_list(length=None)


async def obtener(pedido_id: str) -> dict | None:
    oid = _a_objectid(pedido_id)
    if oid is None:
        return None
    return await get_database()[COLECCION].find_one({"_id": oid})