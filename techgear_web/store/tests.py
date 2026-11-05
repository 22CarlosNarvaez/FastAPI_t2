from unittest.mock import Mock, patch

from django.conf import settings
from django.test import SimpleTestCase
from django.test import override_settings
from django.urls import reverse

from store import api_client


class StoreRoutingTests(SimpleTestCase):
    def test_named_routes_resolve_to_expected_paths(self):
        routes = (
            ("catalogo", (), "/"),
            ("login", (), "/login/"),
            ("registro", (), "/registro/"),
            ("logout", (), "/logout/"),
            ("pedidos", (), "/pedidos/"),
            ("pagar_pedidos", (), "/pedidos/pagar/"),
            ("marcar_pedido_enviado", ("pedido-1",), "/pedidos/pedido-1/enviar/"),
            ("marcar_pedido_recibido", ("pedido-1",), "/pedidos/pedido-1/recibir/"),
            ("pedir", ("producto-1",), "/pedir/producto-1/"),
            ("panel_admin", (), "/panel/"),
            ("eliminar_producto", ("producto-1",), "/panel/eliminar/producto-1/"),
        )

        for name, args, expected_path in routes:
            with self.subTest(route=name):
                self.assertEqual(reverse(name, args=args), expected_path)

    def test_logout_rejects_get_and_accepts_post(self):
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("catalogo"), fetch_redirect_response=False)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class StoreProductSpecificationTests(SimpleTestCase):
    @patch(
        "store.views.api_client.listar_productos",
        return_value=[
            {
                "id": "keyboard-1",
                "nombre": "Teclado inalámbrico",
                "categoria": "Accesorios",
                "descripcion": "",
                "precio": 50000,
                "stock": 2,
            },
            {
                "id": "laptop-1",
                "nombre": "Portátil Lenovo",
                "categoria": "Computadores",
                "descripcion": "",
                "precio": 2500000,
                "stock": 1,
            },
        ],
    )
    def test_catalogo_muestra_especificaciones_genericas(self, _listar_productos):
        response = self.client.get(reverse("catalogo"))

        self.assertContains(response, "Especificaciones generales")
        self.assertContains(response, "Distribución de teclas en español")
        self.assertContains(response, "8 GB de memoria RAM")

    @patch(
        "store.views.api_client.listar_pedidos",
        return_value=[
            {
                "id": "order-1",
                "estado": "pendiente",
                "fecha": "2026-11-05",
                "total": 50000,
                "items": [
                    {
                        "nombre": "Teclado inalámbrico",
                        "cantidad": 1,
                        "precio_unitario": 50000,
                        "subtotal": 50000,
                    }
                ],
            }
        ],
    )
    def test_pedido_muestra_especificaciones_del_producto(self, _listar_pedidos):
        session = self.client.session
        session["token"] = "test-token"
        session["usuario"] = {"rol": "cliente"}
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        response = self.client.get(reverse("pedidos"))

        self.assertContains(response, "Distribución de teclas en español")


class APIClientRoutingTests(SimpleTestCase):
    @override_settings(API_URL="https://api.example.test/")
    @patch("store.api_client.requests.request")
    def test_api_calls_match_fastapi_routes(self, request_mock):
        response = Mock(status_code=200)
        response.json.return_value = {}
        request_mock.return_value = response
        token = "test-token"

        api_client.login("user@example.test", "password")
        api_client.registrar({"nombre": "Test"})
        api_client.listar_productos()
        api_client.crear_producto(token, {})
        api_client.eliminar_producto(token, "product-1")
        api_client.crear_pedido(token, [])
        api_client.listar_pedidos(token)
        api_client.pagar_pedido(token, "order-1", "nequi", "Calle 1", "3001234567", "123456")
        api_client.marcar_pedido_enviado(token, "order-1")
        api_client.marcar_pedido_recibido(token, "order-1")

        routed_requests = [
            (call.args[0], call.args[1].removeprefix("https://api.example.test"))
            for call in request_mock.call_args_list
        ]
        self.assertEqual(
            routed_requests,
            [
                ("POST", "/auth/login"),
                ("POST", "/usuarios/registro"),
                ("GET", "/productos"),
                ("POST", "/productos"),
                ("DELETE", "/productos/product-1"),
                ("POST", "/pedidos"),
                ("GET", "/pedidos"),
                ("POST", "/pedidos/order-1/pagar"),
                ("PATCH", "/pedidos/order-1/enviar"),
                ("PATCH", "/pedidos/order-1/recibir"),
            ],
        )
        for routed_call in request_mock.call_args_list[3:]:
            self.assertEqual(routed_call.kwargs["headers"], {"Authorization": f"Bearer {token}"})
