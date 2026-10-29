import re

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import api_client
from .api_client import APIError
from .decorators import admin_required, login_required


def _sesion_expirada(request):
    request.session.flush()
    messages.warning(request, "Tu sesión expiró. Inicia sesión de nuevo.")
    return redirect("login")


def catalogo(request):
    productos, error = [], None
    try:
        productos = api_client.listar_productos()
    except APIError as e:
        error = str(e)
    return render(request, "store/catalogo.html", {"productos": productos, "error": error})


def login_view(request):
    if request.method == "POST":
        try:
            data = api_client.login(request.POST["email"], request.POST["password"])
        except APIError as e:
            messages.error(request, str(e))
        else:
            request.session["token"] = data["access_token"]
            request.session["usuario"] = data["usuario"]
            messages.success(request, f"Bienvenido, {data['usuario']['nombre']}")
            return redirect("catalogo")
    return render(request, "store/login.html")


def registro_view(request):
    if request.method == "POST":
        payload = {
            "nombre": request.POST["nombre"],
            "email": request.POST["email"],
            "password": request.POST["password"],
            "rol": request.POST.get("rol", "cliente"),
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


def logout_view(request):
    request.session.flush()
    messages.info(request, "Sesión cerrada.")
    return redirect("catalogo")


@login_required
@require_POST
def pedir(request, producto_id):
    try:
        cantidad = max(1, int(request.POST.get("cantidad", 1)))
        api_client.crear_pedido(
            request.session["token"], [{"producto_id": producto_id, "cantidad": cantidad}]
        )
    except ValueError:
        messages.error(request, "Cantidad inválida.")
    except APIError as e:
        if e.status == 401:
            return _sesion_expirada(request)
        messages.error(request, str(e))
    else:
        messages.success(request, "¡Pedido realizado!")
        return redirect("pedidos")
    return redirect("catalogo")


@login_required
def pedidos(request):
    lista, error = [], None
    try:
        lista = api_client.listar_pedidos(request.session["token"])
    except APIError as e:
        if e.status == 401:
            return _sesion_expirada(request)
        error = str(e)
    return render(
        request,
        "store/pedidos.html",
        {
            "pedidos": lista,
            "pedidos_pendientes": [p for p in lista if p["estado"] == "pendiente"],
            "pedidos_por_enviar": [
                p for p in lista if p["estado"] in {"pendiente_envio", "pagado"}
            ],
            "pedidos_enviados": [p for p in lista if p["estado"] == "enviado"],
            "error": error,
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

    pedido_ids = list(dict.fromkeys(request.POST.getlist("pedido_id")))
    if not pedido_ids:
        messages.error(request, "Selecciona al menos un pedido pendiente.")
        return redirect("pedidos")

    metodos_validos = {"tarjeta", "nequi", "transferencia"}
    metodo_pago = request.POST.get("metodo_pago", "")
    referencia = request.POST.get("referencia_prueba", "").strip().upper()
    direccion = request.POST.get("direccion", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    codigo_postal = request.POST.get("codigo_postal", "").strip()
    referencia_valida = re.fullmatch(r"DEMO-[A-Z0-9]{4,12}", referencia)
    if (
        metodo_pago not in metodos_validos
        or not referencia_valida
        or not 5 <= len(direccion) <= 180
        or not re.fullmatch(r"\+?[0-9][0-9\s-]{6,15}", telefono)
        or not re.fullmatch(r"[0-9]{6}", codigo_postal)
    ):
        messages.error(
            request,
            "Revisa método de pago, dirección, celular, código postal de 6 dígitos "
            "y referencia ficticia.",
        )
        return redirect("pedidos")

    pagos_registrados = 0
    errores = []
    for pedido_id in pedido_ids:
        try:
            api_client.pagar_pedido(
                request.session["token"],
                pedido_id,
                metodo_pago,
                direccion,
                telefono,
                codigo_postal,
            )
        except APIError as e:
            if e.status == 401:
                return _sesion_expirada(request)
            errores.append(str(e))
        else:
            pagos_registrados += 1

    if errores:
        if pagos_registrados:
            messages.warning(
                request,
                f"Se registraron {pagos_registrados} pagos simulados; "
                f"{len(errores)} pedido(s) no se pudieron pagar. No se realizó ningún cobro real.",
            )
        for error in errores:
            messages.error(request, error)
    elif pagos_registrados:
        messages.success(
            request,
            f"Cobro simulado exitoso para {pagos_registrados} pedido(s). "
            "Ahora aparecen en «Pendientes por enviar». No se realizó ningún cobro real.",
        )

    return redirect("pedidos")


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
        try:
            api_client.crear_producto(token, {
                "nombre": request.POST["nombre"],
                "descripcion": request.POST.get("descripcion", ""),
                "precio": float(request.POST["precio"]),
                "stock": int(request.POST["stock"]),
                "categoria": request.POST.get("categoria") or "General",
                "imagen_url": request.POST.get("imagen_url") or None,
            })
        except (ValueError, KeyError):
            messages.error(request, "Revisa precio y stock.")
        except APIError as e:
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
        messages.error(request, str(e))
    else:
        messages.success(request, "Producto eliminado.")
    return redirect("panel_admin")