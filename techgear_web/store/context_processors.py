from django.conf import settings


def api(request):
    carrito = request.session.get("carrito", [])
    cantidad_carrito = 0
    if isinstance(carrito, list):
        for item in carrito:
            if not isinstance(item, dict):
                continue
            try:
                cantidad = int(item.get("cantidad", 0))
            except (TypeError, ValueError):
                continue
            if cantidad > 0:
                cantidad_carrito += cantidad

    return {
        "api_url": settings.API_URL.rstrip("/"),
        "cantidad_carrito": cantidad_carrito,
    }