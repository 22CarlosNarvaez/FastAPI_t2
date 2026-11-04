from datetime import datetime, timezone

from fastapi import HTTPException, status
from pymongo import ReturnDocument

from app.core.database import col_pedidos, col_productos
from app.models.pedido import PagoPedido, PedidoCreate
from app.services.productos import to_object_id


def to_out(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def crear(usuario: dict, data: PedidoCreate) -> dict:
    descontados: list[tuple] = []
    items: list[dict] = []
    try:
        for it in data.items:
            oid = to_object_id(it.producto_id)
            # Descuento atómico: solo si hay stock suficiente
            prod = col_productos.find_one_and_update(
                {"_id": oid, "stock": {"$gte": it.cantidad}},
                {"$inc": {"stock": -it.cantidad}},
            )
            if prod is None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Stock insuficiente o producto inexistente ({it.producto_id})",
                )
            descontados.append((oid, it.cantidad))
            items.append({
                "producto_id": it.producto_id,
                "nombre": prod["nombre"],
                "precio_unitario": prod["precio"],
                "cantidad": it.cantidad,
                "subtotal": round(prod["precio"] * it.cantidad, 2),
            })
        doc = {
            "usuario_id": str(usuario["_id"]),
            "usuario_email": usuario["email"],
            "items": items,
            "total": round(sum(i["subtotal"] for i in items), 2),
            "estado": "pendiente",
            "fecha": datetime.now(timezone.utc),
        }
        res = col_pedidos.insert_one(doc)
    except Exception:
        for oid, cantidad in descontados:
            col_productos.update_one({"_id": oid}, {"$inc": {"stock": cantidad}})
        raise

    doc["_id"] = res.inserted_id
    return to_out(doc)


def listar_para(usuario: dict) -> list[dict]:
    """Admin ve todos; cliente SOLO los suyos."""
    filtro = {} if usuario["rol"] == "admin" else {"usuario_id": str(usuario["_id"])}
    return [to_out(p) for p in col_pedidos.find(filtro).sort("fecha", -1)]


def pagar(pedido_id: str, usuario: dict, pago: PagoPedido) -> dict:
    if usuario["rol"] != "cliente":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los clientes pueden pagar pedidos")

    filtro = {
        "_id": to_object_id(pedido_id),
        "usuario_id": str(usuario["_id"]),
        "estado": "pendiente",
    }
    pedido = col_pedidos.find_one_and_update(
        filtro,
        {"$set": {
            "estado": "pendiente_envio",
            "metodo_pago": pago.metodo_pago.value,
            "direccion_envio": pago.direccion,
            "telefono_envio": pago.telefono,
            "codigo_postal": pago.codigo_postal,
        }},
        return_document=ReturnDocument.AFTER,
    )
    if pedido is None:
        existente = col_pedidos.find_one({
            "_id": to_object_id(pedido_id),
            "usuario_id": str(usuario["_id"]),
        })
        if existente is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
        raise HTTPException(status.HTTP_409_CONFLICT, "El pedido ya fue pagado")
    return to_out(pedido)


def marcar_enviado(pedido_id: str, usuario: dict) -> dict:
    if usuario["rol"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo administradores pueden actualizar envíos")

    pedido = col_pedidos.find_one_and_update(
        {"_id": to_object_id(pedido_id), "estado": {"$in": ["pendiente_envio", "pagado"]}},
        {"$set": {"estado": "enviado"}},
        return_document=ReturnDocument.AFTER,
    )
    if pedido is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido pendiente de envío no encontrado")
    return to_out(pedido)


def marcar_recibido(pedido_id: str, usuario: dict) -> dict:
    if usuario["rol"] != "cliente":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el cliente puede confirmar la recepción")

    pedido = col_pedidos.find_one_and_update(
        {
            "_id": to_object_id(pedido_id),
            "usuario_id": str(usuario["_id"]),
            "estado": {"$in": ["pendiente_envio", "pagado", "enviado"]},
        },
        {"$set": {"estado": "recibido"}},
        return_document=ReturnDocument.AFTER,
    )
    if pedido is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Pedido pagado o enviado no encontrado o no pertenece al cliente",
        )
    return to_out(pedido)