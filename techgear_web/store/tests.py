from unittest.mock import Mock, patch

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
