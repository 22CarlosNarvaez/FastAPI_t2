from django.shortcuts import render


def _error_page(request, status_code: int, title: str, message: str):
    return render(
        request,
        "store/error.html",
        {"status_code": status_code, "title": title, "message": message},
        status=status_code,
    )


def bad_request(request, exception=None):
    return _error_page(
        request,
        400,
        "Solicitud no válida",
        "No pudimos procesar esta solicitud. Revisa los datos e inténtalo de nuevo.",
    )


def permission_denied(request, exception=None):
    return _error_page(
        request,
        403,
        "Acceso restringido",
        "No tienes permiso para ver este contenido. Regresa a la tienda y continúa desde allí.",
    )


def csrf_failure(request, reason=""):
    return _error_page(
        request,
        403,
        "No pudimos validar la solicitud",
        "Recarga la página e inténtalo de nuevo. Si el problema continúa, vuelve al inicio.",
    )


def page_not_found(request, exception=None):
    return _error_page(
        request,
        404,
        "No encontramos esta página",
        "Puede que el enlace haya cambiado o que la dirección esté incompleta.",
    )


def server_error(request):
    return _error_page(
        request,
        500,
        "Tuvimos un problema",
        "Ocurrió un error inesperado. Inténtalo de nuevo en unos minutos.",
    )
