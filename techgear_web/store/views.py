import re

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from . import api_client
from .api_client import APIError
from .decorators import admin_required, login_required


def _get_carrito(request):
    carrito = request.session.get("carrito", [])
    datos_invalidos = False
    if not isinstance(carrito, list):
        datos_invalidos = True
        carrito = []
    limpio = []
    for item in carrito:
        if not isinstance(item, dict):
            datos_invalidos = True
            continue
        producto_id = str(item.get("producto_id") or "").strip()
        try:
            cantidad = int(item.get("cantidad"))
        except (TypeError, ValueError):
            datos_invalidos = True
            continue
        if not producto_id or cantidad < 1:
            datos_invalidos = True
            continue
        limpio.append({"producto_id": producto_id, "cantidad": cantidad})
    request.session["carrito"] = limpio
    if datos_invalidos:
        messages.warning(request, "Se corrigieron datos incompletos o inválidos del carrito.")
    return limpio


def _carrito_resumen(request):
    carrito = _get_carrito(request)
    productos = []
    catalogo = api_client.listar_productos()
    catalogo_por_id = {str(p["id"]): p for p in catalogo}
    for item in carrito:
        producto = catalogo_por_id.get(item["producto_id"], {})
        cantidad = max(1, int(item.get("cantidad", 1)))
        productos.append({
            "producto_id": item["producto_id"],
            "nombre": producto.get("nombre") or item["producto_id"],
            "precio_unitario": float(producto.get("precio", 0) or 0),
            "cantidad": cantidad,
            "subtotal": float(producto.get("precio", 0) or 0) * cantidad,
            "stock": int(producto.get("stock", 0) or 0),
        })
    return productos


def _agregar_especificaciones_genericas(producto):
    descripcion = f"{producto.get('nombre', '')} {producto.get('categoria', '')}".casefold()
    if "mouse" in descripcion or "ratón" in descripcion:
        producto["descripcion"] = (
            "Mouse de uso diario para controlar el cursor y navegar en tu equipo. "
            "La conectividad y las funciones dependen del modelo; consulta su ficha "
            "para confirmar los detalles antes de comprar."
        )
    elif "teclad" in descripcion:
        producto["especificaciones"] = [
            "Conexión USB compatible con equipos estándar",
            "Distribución de teclas en español",
            "Diseño cómodo para uso diario",
        ]
    elif "lenovo" in descripcion:
        producto["especificaciones"] = [
            "Pantalla de 15,6 pulgadas Full HD",
            "Procesador Intel Core i5",
            "8 GB de memoria RAM y unidad SSD de 512 GB",
            "Características genéricas; pueden variar según el modelo exacto.",
        ]
    return producto


def _sesion_expirada(request):
    request.session.flush()
    messages.warning(request, "Tu sesión expiró. Inicia sesión de nuevo.")
    return redirect("login")


def inicio(request):
    return render(request, "store/inicio.html")


def catalogo(request):
    productos, error = [], None
    busqueda = request.GET.get("q", "").strip()
    try:
        productos = [
            _agregar_especificaciones_genericas(producto)
            for producto in api_client.listar_productos()
        ]
        if busqueda:
            termino = busqueda.casefold()
            productos = [
                producto
                for producto in productos
                if any(
                    termino in str(producto.get(campo) or "").casefold()
                    for campo in ("nombre", "descripcion", "categoria")
                )
            ]
    except APIError as e:
        error = str(e)
    return render(
        request,
        "store/catalogo.html",
        {"productos": productos, "error": error, "busqueda": busqueda},
    )


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        if not email or not password:
            messages.error(request, "Ingresa tu correo y contraseña.")
            return render(request, "store/login.html", status=400)
        try:
            data = api_client.login(email, password)
        except APIError as e:
            messages.error(request, str(e))
        else:
            request.session["token"] = data["access_token"]
            request.session["usuario"] = data["usuario"]
            messages.success(request, f"Bienvenido, {data['usuario']['nombre']}")
            return redirect("catalogo")
    return render(request, "store/login.html")


@require_http_methods(["GET", "POST"])
def registro_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        nombre = (request.POST.get("nombre") or "").strip()
        password = request.POST.get("password") or ""
        rol = request.POST.get("rol", "cliente")
        if len(nombre) < 2 or not email or len(password) < 6:
            messages.error(request, "Ingresa un nombre válido, correo y contraseña de al menos 6 caracteres.")
            return render(request, "store/registro.html", status=400)
        if rol == "admin" or email == "admin@gmail.com":
            messages.error(
                request,
                "El administrador usa la cuenta fija admin@gmail.com con contraseña 1234567. No requiere registro.",
            )
            return redirect("login")

        payload = {
            "nombre": nombre,
            "email": email,
            "password": password,
            "rol": rol,
            "codigo_admin": request.POST.get("codigo_admin") or None,
        }
        try:
            api_client.registrar(payload)
        except APIError as e:
            messages.error(request, str(e))
        else:
            messages.success(request, "Cuenta creada. Ya puedes iniciar sesión.")
            return redirect("login")
    return render(request, "store/registro.html")


@require_POST
def logout_view(request):
    request.session.flush()
    messages.info(request, "Sesión cerrada.")
    return redirect("catalogo")


@login_required
@require_POST
def pedir(request, producto_id):
    if request.session.get("usuario", {}).get("rol") != "cliente":
        messages.error(request, "Solo los clientes pueden agregar productos al carrito.")
        return redirect("catalogo")
    try:
        cantidad = int(request.POST.get("cantidad", ""))
    except (TypeError, ValueError):
        messages.error(request, "Ingresa una cantidad válida.")
        return redirect("catalogo")
    if cantidad < 1:
        messages.error(request, "La cantidad debe ser al menos una unidad.")
        return redirect("catalogo")

    try:
        producto = next(
            (item for item in api_client.listar_productos() if str(item.get("id")) == producto_id),
            None,
        )
    except APIError as e:
        messages.error(request, str(e))
        return redirect("catalogo")
    if producto is None:
        messages.error(request, "El producto ya no está disponible.")
        return redirect("catalogo")

    carrito = _get_carrito(request)
    existente = next((item for item in carrito if item["producto_id"] == producto_id), None)
    cantidad_actual = existente["cantidad"] if existente else 0
    disponible = int(producto.get("stock", 0) or 0) - cantidad_actual
    if cantidad > disponible:
        messages.error(
            request,
            f"Solo hay {max(0, disponible)} unidad(es) disponibles para agregar al carrito.",
        )
        return redirect("catalogo")
    if existente is None:
        carrito.append({"producto_id": producto_id, "cantidad": cantidad})
    else:
        existente["cantidad"] += cantidad
    request.session["carrito"] = carrito
    messages.success(request, "Producto agregado al carrito.")
    return redirect("catalogo")


@login_required
def pedidos(request):
    lista, error = [], None
    carrito = []
    try:
        carrito = _carrito_resumen(request)
    except APIError as e:
        error = str(e)
    total_carrito = sum(item["subtotal"] for item in carrito)
    try:
        lista = api_client.listar_pedidos(request.session["token"])
        for pedido in lista:
            for item in pedido.get("items", []):
                _agregar_especificaciones_genericas(item)
    except APIError as e:
        if e.status == 401:
            return _sesion_expirada(request)
        error = f"{error} {e}".strip()
    return render(
        request,
        "store/pedidos.html",
        {
            "pedidos": lista,
            "pedidos_pendientes": [p for p in lista if p.get("estado") == "pendiente"],
            "pedidos_por_enviar": [
                p for p in lista if p.get("estado") in {"pendiente_envio", "pagado"}
            ],
            "pedidos_enviados": [p for p in lista if p.get("estado") == "enviado"],
            "error": error,
            "carrito": carrito,
            "total_carrito": total_carrito,
        },
    )


@login_required
@require_POST
def marcar_pedido_recibido(request, pedido_id):
    if request.session.get("usuario", {}).get("rol") != "cliente":
        messages.error(request, "Solo el cliente puede confirmar la recepción.")
        return redirect("pedidos")
    try:
        api_client.marcar_pedido_recibido(request.session["token"], pedido_id)
    except APIError as e:
        if e.status == 401:
            return _sesion_expirada(request)
        messages.error(request, str(e))
    else:
        messages.success(request, "Pedido marcado como recibido.")
    return redirect("pedidos")


@login_required
@require_POST
def pagar_pedidos(request):
    if request.session.get("usuario", {}).get("rol") != "cliente":
        messages.error(request, "Solo los clientes pueden pagar pedidos.")
        return redirect("pedidos")

    carrito = _get_carrito(request)
    if not carrito:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("catalogo")

    metodo_pago = request.POST.get("metodo_pago", "")
    direccion = request.POST.get("direccion", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    codigo_postal = request.POST.get("codigo_postal", "").strip()
    if (
        metodo_pago not in {"tarjeta", "nequi", "transferencia"}
        or not 5 <= len(direccion) <= 180
        or not re.fullmatch(r"\+?[0-9][0-9\s-]{6,15}", telefono)
        or not re.fullmatch(r"[0-9]{6}", codigo_postal)
    ):
        messages.error(
            request,
            "Revisa método de pago, dirección, celular y código postal de 6 dígitos.",
        )
        return redirect("pedidos")

    try:
        pedido = api_client.crear_pedido(
            request.session["token"],
            [{"producto_id": item["producto_id"], "cantidad": item["cantidad"]} for item in carrito],
        )
        api_client.pagar_pedido(
            request.session["token"],
            pedido["id"],
            metodo_pago,
            direccion,
            telefono,
            codigo_postal,
        )
    except ValueError:
        messages.error(request, "Cantidad inválida.")
    except APIError as e:
        if e.status == 401:
            return _sesion_expirada(request)
        messages.error(request, str(e))
    else:
        request.session["carrito"] = []
        messages.success(request, "¡Pedido pagado con éxito! El stock se actualizó al confirmar el pago.")
        return redirect("pedidos")
    return redirect("catalogo")


@admin_required
@require_POST
def marcar_pedido_enviado(request, pedido_id):
    try:
        api_client.marcar_pedido_enviado(request.session["token"], pedido_id)
    except APIError as e:
        if e.status == 401:
            return _sesion_expirada(request)
        messages.error(request, str(e))
    else:
        messages.success(request, "Pedido marcado como enviado.")
    return redirect("pedidos")


@admin_required
def panel_admin(request):
    token = request.session["token"]
    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        try:
            precio = float(request.POST.get("precio", ""))
            stock = int(request.POST.get("stock", ""))
        except (TypeError, ValueError):
            messages.error(request, "El precio debe ser numérico y el stock un número entero.")
            return redirect("panel_admin")
        if not nombre or precio <= 0 or stock < 0:
            messages.error(request, "Ingresa un nombre, un precio mayor que cero y un stock no negativo.")
            return redirect("panel_admin")
        try:
            api_client.crear_producto(token, {
                "nombre": nombre,
                "descripcion": request.POST.get("descripcion", ""),
                "precio": precio,
                "stock": stock,
                "categoria": request.POST.get("categoria") or "General",
                "imagen_url": request.POST.get("imagen_url") or None,
            })
        except (ValueError, KeyError):
            messages.error(request, "Revisa precio y stock.")
        except APIError as e:
            if e.status == 401:
                return _sesion_expirada(request)
            if e.status == 401:
                return _sesion_expirada(request)
            messages.error(request, str(e))
        else:
            messages.success(request, "Producto publicado.")
        return redirect("panel_admin")

    productos, error = [], None
    try:
        productos = api_client.listar_productos()
    except APIError as e:
        error = str(e)
    return render(request, "store/panel_admin.html", {"productos": productos, "error": error})


@admin_required
@require_POST
def eliminar_producto(request, producto_id):
    try:
        api_client.eliminar_producto(request.session["token"], producto_id)
    except APIError as e:
        if e.status == 401:
            return _sesion_expirada(request)
        messages.error(request, str(e))
    else:
        messages.success(request, "Producto eliminado.")
    return redirect("panel_admin")