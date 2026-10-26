from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import get_database
from app.models.producto import ProductoCreate

COLECCION = "productos"


def _a_objectid(producto_id: str) -> ObjectId | None:
    try:
        return ObjectId(producto_id)
    except (InvalidId, TypeError):
        return None


async def crear(datos: ProductoCreate) -> dict:
    coleccion = get_database()[COLECCION]
    documento = datos.model_dump()
    resultado = await coleccion.insert_one(documento)
    documento["_id"] = resultado.inserted_id
    return documento


async def listar() -> list[dict]:
    coleccion = get_database()[COLECCION]
    return await coleccion.find().to_list(length=None)


async def obtener(producto_id: str) -> dict | None:
    oid = _a_objectid(producto_id)
    if oid is None:
        return None
    return await get_database()[COLECCION].find_one({"_id": oid})


async def actualizar(producto_id: str, datos: ProductoCreate) -> dict | None:
    oid = _a_objectid(producto_id)
    if oid is None:
        return None
    return await get_database()[COLECCION].find_one_and_update(
        {"_id": oid},
        {"$set": datos.model_dump()},
        return_document=True,
    )


async def eliminar(producto_id: str) -> bool:
    oid = _a_objectid(producto_id)
    if oid is None:
        return False
    resultado = await get_database()[COLECCION].delete_one({"_id": oid})
    return resultado.deleted_count == 1