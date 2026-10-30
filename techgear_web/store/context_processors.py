def api(request):
    return {"api_url": request.build_absolute_uri("/").rstrip("/")}