from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status

from app.core.database import col_productos
from app.models.producto import ProductoCreate, ProductoUpdate


def to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ID inválido")


def to_out(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def listar() -> list[dict]:
    return [to_out(p) for p in col_productos.find().sort("nombre", 1)]


def obtener(producto_id: str) -> dict:
    doc = col_productos.find_one({"_id": to_object_id(producto_id)})
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return to_out(doc)


def crear(data: ProductoCreate) -> dict:
    doc = data.model_dump()
    res = col_productos.insert_one(doc)
    doc["_id"] = res.inserted_id
    return to_out(doc)


def actualizar(producto_id: str, data: ProductoUpdate) -> dict:
    cambios = data.model_dump(exclude_unset=True)
    if cambios:
        col_productos.update_one({"_id": to_object_id(producto_id)}, {"$set": cambios})
    return obtener(producto_id)


def eliminar(producto_id: str) -> None:
    res = col_productos.delete_one({"_id": to_object_id(producto_id)})
    if res.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")