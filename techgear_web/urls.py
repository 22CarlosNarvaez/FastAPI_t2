from django.contrib import admin
from django.urls import include, path

from store import error_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("store.urls")),
]

handler400 = error_views.bad_request
handler403 = error_views.permission_denied
handler404 = error_views.page_not_found
handler500 = error_views.server_error