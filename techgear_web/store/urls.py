from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("productos/<str:producto_id>/", views.detalle_producto, name="detalle_producto"),
    path("login/", views.login_view, name="login"),
    path("registro/", views.registro_view, name="registro"),
    path("logout/", views.logout_view, name="logout"),
    path("pedidos/", views.pedidos, name="pedidos"),
    path("pedidos/pagar/", views.pagar_pedidos, name="pagar_pedidos"),
    path(
        "carrito/quitar/<str:producto_id>/",
        views.quitar_del_carrito,
        name="quitar_del_carrito",
    ),
    path("pedidos/<str:pedido_id>/enviar/", views.marcar_pedido_enviado, name="marcar_pedido_enviado"),
    path("pedidos/<str:pedido_id>/recibir/", views.marcar_pedido_recibido, name="marcar_pedido_recibido"),
    path("pedir/<str:producto_id>/", views.pedir, name="pedir"),
    path("panel/", views.panel_admin, name="panel_admin"),
    path("panel/eliminar/<str:producto_id>/", views.eliminar_producto, name="eliminar_producto"),
]