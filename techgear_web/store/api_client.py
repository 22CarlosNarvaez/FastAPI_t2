import requests
from django.conf import settings


class APIError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def _request(method: str, path: str, token: str | None = None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{settings.API_URL.rstrip('/')}{path}"
    guest_id = kwargs.pop("guest_id", None)
    if guest_id:
        headers["X-Guest-ID"] = guest_id
    try:
        response = requests.request(method, url, headers=headers, timeout=60, **kwargs)
    except requests.Timeout as error:
        raise APIError("La API tardó demasiado en responder. Intenta de nuevo.") from error
    except requests.ConnectionError as error:
        raise APIError("No se pudo conectar con la API. Comprueba el servicio e inténtalo de nuevo.") from error
    except requests.RequestException as error:
        raise APIError("Ocurrió un problema de comunicación con la API.") from error

    if response.status_code >= 400:
        try:
            body = response.json()
        except ValueError:
            body = {}
        detail = body.get("detail") if isinstance(body, dict) else None
        if isinstance(detail, list):
            detail = "; ".join(
                str(item.get("msg", ""))
                for item in detail
                if isinstance(item, dict) and item.get("msg")
            )
        if response.status_code >= 500:
            message = "La API tuvo un error interno. Intenta de nuevo más tarde."
        else:
            message = detail or {
                401: "Tu sesión no es válida. Inicia sesión de nuevo.",
                403: "No tienes permiso para realizar esta acción.",
                404: "No encontramos el recurso solicitado.",
                409: "La operación entra en conflicto con el estado actual.",
                422: "Revisa los datos ingresados e inténtalo de nuevo.",
                429: "Hay demasiadas solicitudes. Espera un momento e inténtalo de nuevo.",
            }.get(response.status_code, f"La API respondió con el error {response.status_code}.")
        raise APIError(str(message), response.status_code)

    if response.status_code == 204:
        return None
    try:
        return response.json()
    except ValueError as error:
        raise APIError("La API devolvió una respuesta inválida.") from error


def login(email, password):
    return _request("POST", "/auth/login", data={"username": email, "password": password})


def registrar(payload):
    return _request("POST", "/usuarios/registro", json=payload)


def listar_productos():
    return _request("GET", "/productos")


def obtener_producto(producto_id):
    return _request("GET", f"/productos/{producto_id}")


def crear_producto(token, payload):
    return _request("POST", "/productos", token, json=payload)


def eliminar_producto(token, producto_id):
    return _request("DELETE", f"/productos/{producto_id}", token)


def crear_pedido(token, items, guest_id=None):
    return _request("POST", "/pedidos", token, guest_id=guest_id, json={"items": items})


def listar_pedidos(token, guest_id=None):
    return _request("GET", "/pedidos", token, guest_id=guest_id)


def pagar_pedido(token, pedido_id, metodo_pago, direccion, telefono, codigo_postal, guest_id=None):
    return _request(
        "POST",
        f"/pedidos/{pedido_id}/pagar",
        token,
        guest_id=guest_id,
        json={
            "metodo_pago": metodo_pago,
            "direccion": direccion,
            "telefono": telefono,
            "codigo_postal": codigo_postal,
        },
    )


def marcar_pedido_enviado(token, pedido_id):
    return _request("PATCH", f"/pedidos/{pedido_id}/enviar", token)


def marcar_pedido_recibido(token, pedido_id, guest_id=None):
    return _request("PATCH", f"/pedidos/{pedido_id}/recibir", token, guest_id=guest_id)