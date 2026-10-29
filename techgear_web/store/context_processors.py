from django.conf import settings


def api(request):
    return {"api_url": settings.API_URL.rstrip("/")}