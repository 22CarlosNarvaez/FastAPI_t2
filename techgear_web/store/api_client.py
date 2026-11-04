import requests
from django.conf import settings


class APIError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def _request(method: str, path: str, token: str | None = None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{settings.API_URL.rstrip('/')}{path}"
    try:
        # timeout alto: Render (plan gratis) tarda en despertar
        r = requests.request(method, url, headers=headers, timeout=60, **kwargs)
    except requests.RequestException:
        raise APIError("No se pudo conectar con la API de FastAPI.")
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
        except ValueError:
            detail = None
        if isinstance(detail, list):
            detail = "; ".join(d.get("msg", "") for d in detail)
        raise APIError(detail or f"Error {r.status_code}", r.status_code)
    return None if r.status_code == 204 else r.json()


def login(email, password):
    return _request("POST", "/auth/login", data={"username": email, "password": password})


def registrar(payload):
    return _request("POST", "/usuarios/registro", json=payload)


def listar_productos():
    return _request("GET", "/productos")


def crear_producto(token, payload):
    return _request("POST", "/productos", token, json=payload)


def eliminar_producto(token, producto_id):
    return _request("DELETE", f"/productos/{producto_id}", token)


def crear_pedido(token, items):
    return _request("POST", "/pedidos", token, json={"items": items})


def listar_pedidos(token):
    return _request("GET", "/pedidos", token)


def pagar_pedido(token, pedido_id, metodo_pago, direccion, telefono, codigo_postal):
    return _request(
        "POST",
        f"/pedidos/{pedido_id}/pagar",
        token,
        json={
            "metodo_pago": metodo_pago,
            "direccion": direccion,
            "telefono": telefono,
            "codigo_postal": codigo_postal,
        },
    )


def marcar_pedido_enviado(token, pedido_id):
    return _request("PATCH", f"/pedidos/{pedido_id}/enviar", token)


def marcar_pedido_recibido(token, pedido_id):
    return _request("PATCH", f"/pedidos/{pedido_id}/recibir", token)