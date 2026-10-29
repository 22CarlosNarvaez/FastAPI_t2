from django.urls import path

from . import views

urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("login/", views.login_view, name="login"),
    path("registro/", views.registro_view, name="registro"),
    path("logout/", views.logout_view, name="logout"),
    path("pedidos/", views.pedidos, name="pedidos"),
    path("pedidos/pagar/", views.pagar_pedidos, name="pagar_pedidos"),
    path("pedidos/<str:pedido_id>/enviar/", views.marcar_pedido_enviado, name="marcar_pedido_enviado"),
    path("pedidos/<str:pedido_id>/recibir/", views.marcar_pedido_recibido, name="marcar_pedido_recibido"),
    path("pedir/<str:producto_id>/", views.pedir, name="pedir"),
    path("panel/", views.panel_admin, name="panel_admin"),
    path("panel/eliminar/<str:producto_id>/", views.eliminar_producto, name="eliminar_producto"),
]