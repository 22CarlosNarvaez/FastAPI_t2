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


def crear(usuario: dict | None, data: PedidoCreate, guest_id: str | None = None) -> dict:
    if usuario is not None and usuario["rol"] != "cliente":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los clientes pueden crear pedidos")
    if usuario is None and not guest_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Se requiere una sesión de invitado")

    items: list[dict] = []
    for it in data.items:
        oid = to_object_id(it.producto_id)
        prod = col_productos.find_one({"_id": oid})
        if prod is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Producto inexistente ({it.producto_id})",
            )
        if prod.get("stock", 0) < it.cantidad:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Stock insuficiente o producto inexistente ({it.producto_id})",
            )
        items.append({
            "producto_id": it.producto_id,
            "nombre": prod["nombre"],
            "precio_unitario": prod["precio"],
            "cantidad": it.cantidad,
            "subtotal": round(prod["precio"] * it.cantidad, 2),
        })

    doc = {
        "usuario_id": str(usuario["_id"]) if usuario else None,
        "usuario_email": usuario["email"] if usuario else None,
        "guest_id": guest_id,
        "items": items,
        "total": round(sum(i["subtotal"] for i in items), 2),
        "estado": "pendiente",
        "fecha": datetime.now(timezone.utc),
    }
    res = col_pedidos.insert_one(doc)

    doc["_id"] = res.inserted_id
    return to_out(doc)


def listar_para(usuario: dict | None, guest_id: str | None = None) -> list[dict]:
    """Admin ve todos; clientes e invitados solo ven sus propios pedidos."""
    if usuario is None:
        if not guest_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Se requiere una sesión de invitado")
        filtro = {"guest_id": guest_id}
    else:
        filtro = {} if usuario["rol"] == "admin" else {"usuario_id": str(usuario["_id"])}
    return [to_out(p) for p in col_pedidos.find(filtro).sort("fecha", -1)]


def pagar(
    pedido_id: str,
    usuario: dict | None,
    pago: PagoPedido,
    guest_id: str | None = None,
) -> dict:
    if usuario is not None and usuario["rol"] != "cliente":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los clientes pueden pagar pedidos")
    if usuario is None and not guest_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Se requiere una sesión de invitado")

    propietario = (
        {"usuario_id": str(usuario["_id"])}
        if usuario is not None
        else {"guest_id": guest_id}
    )
    filtro_pedido = {
        "_id": to_object_id(pedido_id),
        "estado": "pendiente",
        **propietario,
    }
    pedido = col_pedidos.find_one(filtro_pedido)
    if pedido is None:
        existente = col_pedidos.find_one({"_id": to_object_id(pedido_id), **propietario})
        if existente is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
        raise HTTPException(status.HTTP_409_CONFLICT, "El pedido ya fue pagado")

    for item in pedido["items"]:
        oid = to_object_id(item["producto_id"])
        producto = col_productos.find_one({"_id": oid})
        if producto is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Producto inexistente ({item['producto_id']})")
        if producto.get("stock", 0) < item["cantidad"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Stock insuficiente para {producto.get('nombre', item['producto_id'])}")

    for item in pedido["items"]:
        oid = to_object_id(item["producto_id"])
        col_productos.update_one({"_id": oid}, {"$inc": {"stock": -item["cantidad"]}})

    pedido = col_pedidos.find_one_and_update(
        filtro_pedido,
        {"$set": {
            "estado": "pendiente_envio",
            "metodo_pago": pago.metodo_pago.value,
            "direccion_envio": pago.direccion,
            "telefono_envio": pago.telefono,
            "codigo_postal": pago.codigo_postal,
        }},
        return_document=ReturnDocument.AFTER,
    )
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


def marcar_recibido(
    pedido_id: str,
    usuario: dict | None,
    guest_id: str | None = None,
) -> dict:
    if usuario is not None and usuario["rol"] != "cliente":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el cliente puede confirmar la recepción")
    if usuario is None and not guest_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Se requiere una sesión de invitado")

    propietario = (
        {"usuario_id": str(usuario["_id"])}
        if usuario is not None
        else {"guest_id": guest_id}
    )
    pedido = col_pedidos.find_one_and_update(
        {
            "_id": to_object_id(pedido_id),
            "estado": "enviado",
            **propietario,
        },
        {"$set": {"estado": "recibido"}},
        return_document=ReturnDocument.AFTER,
    )
    if pedido is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Pedido enviado no encontrado o no pertenece al cliente",
        )
    return to_out(pedido)