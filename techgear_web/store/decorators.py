from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("token"):
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("login")
        return view(request, *args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.session.get("usuario", {}).get("rol") != "admin":
            messages.error(request, "Acceso solo para administradores.")
            return redirect("catalogo")
        return view(request, *args, **kwargs)
    return wrapper