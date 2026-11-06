from unittest.mock import Mock, patch

import requests
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase
from django.test import override_settings
from django.urls import reverse

from store import api_client, error_views
from store.api_client import APIError
from store.templatetags.store_formatting import cop


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class StoreRoutingTests(SimpleTestCase):
    def test_named_routes_resolve_to_expected_paths(self):
        routes = (
            ("inicio", (), "/"),
            ("catalogo", (), "/catalogo/"),
            ("login", (), "/login/"),
            ("registro", (), "/registro/"),
            ("logout", (), "/logout/"),
            ("pedidos", (), "/pedidos/"),
            ("pagar_pedidos", (), "/pedidos/pagar/"),
            ("quitar_del_carrito", ("product-1",), "/carrito/quitar/product-1/"),
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

    @patch("store.views.api_client.login")
    def test_login_incompleto_muestra_un_error_de_validacion(self, login_mock):
        response = self.client.post(reverse("login"), {"email": "", "password": ""})

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Ingresa tu correo y contraseña.", status_code=400)
        login_mock.assert_not_called()


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class StoreLandingTests(SimpleTestCase):
    def test_portada_describe_techgear_y_muestra_contactos_de_demostracion(self):
        response = self.client.get(reverse("inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "En TechGear acercamos accesorios y dispositivos")
        self.assertContains(response, "https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=hola.techgear.demo@gmail.com")
        self.assertContains(response, "https://www.instagram.com/techgear.demo/")
        self.assertContains(response, "https://wa.me/573000000000")
        self.assertContains(response, "reemplázalos por los canales oficiales")
        self.assertContains(response, 'alt="Computador portátil abierto sobre un escritorio de trabajo"')
        self.assertContains(response, 'alt="Personas colaborando con computadores en un espacio de trabajo"')
        self.assertContains(response, 'alt="Reloj inteligente de diseño moderno"')
        self.assertContains(response, "/static/store/img/landing-hero.jpg")


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
        self.assertContains(response, "$2.500.000")

    @patch(
        "store.views.api_client.listar_productos",
        return_value=[
            {
                "id": "mouse-1",
                "nombre": "Mouse inalámbrico",
                "categoria": "Accesorios",
                "descripcion": "Promesa de batería de larga duración",
                "precio": 50000,
                "stock": 2,
            },
            {
                "id": "keyboard-1",
                "nombre": "Teclado",
                "categoria": "Accesorios",
                "descripcion": "Teclas cómodas",
                "precio": 80000,
                "stock": 2,
            },
        ],
    )
    def test_busqueda_filtra_catalogo_y_usa_descripcion_fiable_para_mouse(self, _listar_productos):
        response = self.client.get(reverse("catalogo"), {"q": "mouse"})

        self.assertContains(response, "Mouse de uso diario para controlar el cursor")
        self.assertNotContains(response, "Promesa de batería de larga duración")
        self.assertNotContains(response, "Teclado")

    @patch("store.views.api_client.listar_productos", return_value=[])
    def test_busqueda_sin_resultados_muestra_estado_vacio(self, _listar_productos):
        response = self.client.get(reverse("catalogo"), {"q": "no existe"})

        self.assertContains(response, "No encontramos productos para")

    @patch("store.views.api_client.listar_productos", return_value=[])
    def test_catalogo_busca_tambien_por_categoria_y_descripcion(self, listar_productos):
        listar_productos.return_value = [
            {
                "id": "one",
                "nombre": "Periférico",
                "categoria": "Audio",
                "descripcion": "Sonido envolvente",
                "precio": 50000,
                "stock": 1,
            },
            {
                "id": "two",
                "nombre": "Accesorio",
                "categoria": "Oficina",
                "descripcion": "Uso diario",
                "precio": 80000,
                "stock": 1,
            },
        ]

        response = self.client.get(reverse("catalogo"), {"q": "sonido"})

        self.assertContains(response, "Periférico")
        self.assertNotContains(response, "Uso diario")

        response = self.client.get(reverse("catalogo"), {"q": "audio"})

        self.assertContains(response, "Periférico")
        self.assertNotContains(response, "Uso diario")

    @patch(
        "store.views.api_client.listar_productos",
        return_value=[
            {
                "id": "out-of-stock",
                "nombre": "Producto agotado",
                "categoria": "Accesorios",
                "precio": 50000,
                "stock": 0,
            }
        ],
    )
    def test_producto_sin_stock_muestra_controles_desactivados(self, _listar_productos):
        session = self.client.session
        session["token"] = "test-token"
        session["usuario"] = {"rol": "cliente"}
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        response = self.client.get(reverse("catalogo"))

        self.assertContains(response, "Agotado")
        self.assertContains(response, 'name="cantidad"')
        self.assertContains(response, "disabled aria-describedby")

    @patch(
        "store.views.api_client.listar_productos",
        return_value=[
            {
                "id": "limited-stock",
                "nombre": "Producto limitado",
                "precio": 25000,
                "stock": 1,
            }
        ],
    )
    def test_no_agrega_mas_unidades_que_el_stock_disponible(self, _listar_productos):
        session = self.client.session
        session["token"] = "test-token"
        session["usuario"] = {"rol": "cliente"}
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        response = self.client.post(
            reverse("pedir", args=["limited-stock"]),
            {"cantidad": "2"},
            follow=True,
        )

        self.assertContains(response, "Solo hay 1 unidad(es) disponibles")
        self.assertEqual(self.client.session.get("carrito"), [])

    @override_settings(API_URL="https://api.example.test/v1/")
    @patch("store.views.api_client.listar_productos", return_value=[])
    def test_enlace_api_apunta_a_la_url_configurada(self, _listar_productos):
        response = self.client.get(reverse("catalogo"))

        self.assertContains(response, 'href="https://api.example.test/v1/docs"')

    @patch("store.views.api_client.listar_productos", return_value=[])
    @patch(
        "store.views.api_client.listar_pedidos",
        return_value=[
            {
                "id": "order-1",
                "estado": "pendiente_envio",
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
    def test_pedido_muestra_especificaciones_del_producto(self, _listar_pedidos, _productos):
        session = self.client.session
        session["token"] = "test-token"
        session["usuario"] = {"rol": "cliente"}
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        response = self.client.get(reverse("pedidos"))

        self.assertContains(response, "Distribución de teclas en español")

    @patch(
        "store.views.api_client.listar_pedidos",
        return_value=[
            {
                "id": "pending-1",
                "estado": "pendiente",
                "usuario_email": "cliente@example.test",
                "total": 2500000,
                "items": [
                    {
                        "nombre": "Portátil",
                        "cantidad": 1,
                        "subtotal": 2500000,
                    }
                ],
            },
            {
                "id": "shipping-1",
                "estado": "pendiente_envio",
                "usuario_email": "cliente@example.test",
                "total": 50000,
                "direccion_envio": "Calle 1",
                "telefono_envio": "3001234567",
                "codigo_postal": "050001",
                "items": [
                    {
                        "nombre": "Teclado",
                        "cantidad": 1,
                        "subtotal": 50000,
                    }
                ],
            },
            {
                "id": "sent-1",
                "estado": "enviado",
                "usuario_email": "cliente@example.test",
                "total": 50000,
                "direccion_envio": "Calle 1",
                "telefono_envio": "3001234567",
                "codigo_postal": "050001",
                "items": [
                    {
                        "nombre": "Teclado",
                        "cantidad": 1,
                        "subtotal": 50000,
                    }
                ],
            },
        ],
    )
    def test_admin_puede_revisar_pedidos_organizados_y_en_pesos(self, _listar_pedidos):
        session = self.client.session
        session["token"] = "test-token"
        session["usuario"] = {"rol": "admin"}
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        response = self.client.get(reverse("pedidos"))

        self.assertContains(response, "Resumen de pedidos")
        self.assertContains(response, "Pendientes de pago")
        self.assertContains(response, "Pendientes por enviar")
        self.assertContains(response, "Enviados")
        self.assertContains(response, "$2.500.000")
        self.assertContains(response, "050001")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class StoreCartTests(SimpleTestCase):
    def setUp(self):
        session = self.client.session
        session["token"] = "test-token"
        session["usuario"] = {"rol": "cliente"}
        session["carrito"] = [{"producto_id": "product-1", "cantidad": 2}]
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    @patch("store.views.api_client.listar_pedidos", return_value=[])
    @patch(
        "store.views.api_client.listar_productos",
        return_value=[
            {
                "id": "product-1",
                "nombre": "Teclado",
                "precio": 50000,
                "stock": 4,
            }
        ],
    )
    def test_carrito_muestra_resumen_metodos_visuales_y_contador(self, _productos, _pedidos):
        response = self.client.get(reverse("pedidos"))

        self.assertContains(response, "Carrito de compras")
        self.assertContains(response, "Teclado")
        self.assertContains(response, "$100.000")
        self.assertContains(response, 'aria-label="Carrito de compras, 2 productos"')
        self.assertContains(response, 'class="bi bi-cart3"')
        self.assertContains(response, 'name="metodo_pago" value="tarjeta"')
        self.assertContains(response, 'name="metodo_pago" value="nequi"')
        self.assertContains(response, 'name="metodo_pago" value="transferencia"')
        self.assertContains(response, 'name="producto_seleccionado"')
        self.assertContains(response, 'value="product-1"')
        self.assertContains(response, 'form="checkout-form" checked')
        self.assertContains(response, "no se solicitan datos financieros")
        self.assertNotContains(response, "tarjeta-numero")
        self.assertNotContains(response, "nequi-clave")

    def test_quitar_producto_remueve_item_del_carrito(self):
        response = self.client.post(
            reverse("quitar_del_carrito", args=["product-1"]),
            follow=True,
        )

        self.assertContains(response, "Producto eliminado del carrito.")
        self.assertEqual(self.client.session.get("carrito"), [])

    @patch(
        "store.views.api_client.listar_productos",
        return_value=[
            {
                "id": "product-1",
                "nombre": "Teclado",
                "precio": 50000,
                "stock": 4,
            }
        ],
    )
    def test_agregar_producto_acumula_cantidad_en_el_carrito(self, _listar_productos):
        response = self.client.post(
            reverse("pedir", args=["product-1"]),
            {"cantidad": "1"},
        )

        self.assertRedirects(response, reverse("catalogo"), fetch_redirect_response=False)
        self.assertEqual(
            self.client.session.get("carrito"),
            [{"producto_id": "product-1", "cantidad": 3}],
        )

    @patch("store.views.api_client.listar_pedidos", return_value=[
        {
            "id": "preparing-1",
            "estado": "pendiente_envio",
            "items": [{"nombre": "Mouse", "cantidad": 1, "subtotal": 25000}],
        },
        {
            "id": "shipped-1",
            "estado": "enviado",
            "items": [{"nombre": "Teclado", "cantidad": 1, "subtotal": 50000}],
        },
        {
            "id": "received-1",
            "estado": "recibido",
            "items": [{"nombre": "Audífonos", "cantidad": 1, "subtotal": 75000}],
        },
    ])
    @patch("store.views.api_client.listar_productos", return_value=[])
    def test_pedidos_separan_en_preparacion_pendientes_y_recibidos(
        self, _productos, _pedidos
    ):
        response = self.client.get(reverse("pedidos"))

        self.assertContains(response, "En preparación")
        self.assertContains(response, "Pendientes por recibir")
        self.assertContains(response, "Ya recibidos")
        self.assertContains(response, "Mouse")
        self.assertContains(response, "Teclado")
        self.assertContains(response, "Audífonos")
        self.assertContains(response, "Confirmar recepción", count=1)
        self.assertContains(response, "Recepción confirmada")

    @patch("store.views.api_client.pagar_pedido")
    @patch("store.views.api_client.crear_pedido", return_value={"id": "order-1"})
    def test_confirmar_checkout_crea_pedido_y_solo_envia_el_metodo_seleccionado(
        self, crear_pedido, pagar_pedido
    ):
        session = self.client.session
        session["carrito"].append({"producto_id": "product-2", "cantidad": 1})
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        response = self.client.post(
            reverse("pagar_pedidos"),
            {
                "producto_seleccionado": "product-1",
                "direccion": "Calle 1 # 2-3",
                "telefono": "3001234567",
                "codigo_postal": "050001",
                "metodo_pago": "nequi",
            },
        )

        self.assertRedirects(response, reverse("pedidos"), fetch_redirect_response=False)
        crear_pedido.assert_called_once_with(
            "test-token",
            [{"producto_id": "product-1", "cantidad": 2}],
        )
        pagar_pedido.assert_called_once_with(
            "test-token",
            "order-1",
            "nequi",
            "Calle 1 # 2-3",
            "3001234567",
            "050001",
        )
        self.assertEqual(
            self.client.session.get("carrito"),
            [{"producto_id": "product-2", "cantidad": 1}],
        )

    @patch("store.views.api_client.crear_pedido")
    def test_checkout_sin_productos_seleccionados_no_crea_pedido(self, crear_pedido):
        response = self.client.post(
            reverse("pagar_pedidos"),
            {
                "direccion": "Calle 1 # 2-3",
                "telefono": "3001234567",
                "codigo_postal": "050001",
                "metodo_pago": "nequi",
            },
            follow=True,
        )

        self.assertContains(response, "Selecciona al menos un producto para pagar.")
        crear_pedido.assert_not_called()
        self.assertEqual(
            self.client.session.get("carrito"),
            [{"producto_id": "product-1", "cantidad": 2}],
        )

    @patch("store.views.api_client.crear_pedido")
    def test_checkout_rechaza_productos_que_no_pertenecen_al_carrito(self, crear_pedido):
        response = self.client.post(
            reverse("pagar_pedidos"),
            {
                "producto_seleccionado": "product-outside-cart",
                "direccion": "Calle 1 # 2-3",
                "telefono": "3001234567",
                "codigo_postal": "050001",
                "metodo_pago": "nequi",
            },
            follow=True,
        )

        self.assertContains(response, "La selección contiene productos que no están en tu carrito.")
        crear_pedido.assert_not_called()
        self.assertEqual(
            self.client.session.get("carrito"),
            [{"producto_id": "product-1", "cantidad": 2}],
        )


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


class APIClientErrorTests(SimpleTestCase):
    @patch("store.api_client.requests.request")
    def test_timeout_se_convierte_en_error_amigable(self, request_mock):
        request_mock.side_effect = requests.Timeout

        with self.assertRaisesRegex(APIError, "tardó demasiado") as error:
            api_client.listar_productos()

        self.assertIsNone(error.exception.status)

    @patch("store.api_client.requests.request")
    def test_error_interno_no_expone_detalles_del_servidor(self, request_mock):
        response = Mock(status_code=500)
        response.json.return_value = {"detail": "traceback confidencial"}
        request_mock.return_value = response

        with self.assertRaisesRegex(APIError, "error interno") as error:
            api_client.listar_productos()

        self.assertEqual(error.exception.status, 500)
        self.assertNotIn("traceback", str(error.exception))

    @patch("store.api_client.requests.request")
    def test_respuesta_json_invalida_se_informa_como_error_de_api(self, request_mock):
        response = Mock(status_code=200)
        response.json.side_effect = ValueError
        request_mock.return_value = response

        with self.assertRaisesRegex(APIError, "respuesta inválida"):
            api_client.listar_productos()


class MoneyFormattingTests(SimpleTestCase):
    def test_precio_invalido_no_interrumpe_el_renderizado(self):
        for value in (None, "no es un precio", float("nan"), -1):
            with self.subTest(value=value):
                self.assertEqual(cop(value), "Precio no disponible")

    def test_precio_valido_se_muestra_en_pesos_colombianos(self):
        self.assertEqual(cop("2500000.50"), "$2.500.001")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ErrorPageTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_paginas_de_error_responden_con_estado_y_texto_correspondientes(self):
        cases = (
            (error_views.bad_request, 400, "Solicitud no válida"),
            (error_views.permission_denied, 403, "Acceso restringido"),
            (error_views.page_not_found, 404, "No encontramos esta página"),
            (error_views.server_error, 500, "Tuvimos un problema"),
        )
        request = self.factory.get("/")
        request.session = {}
        request.user = AnonymousUser()
        request._messages = []

        for handler, status_code, title in cases:
            with self.subTest(status=status_code):
                response = handler(request)
                self.assertEqual(response.status_code, status_code)
                self.assertContains(response, title, status_code=status_code)

    def test_ruta_inexistente_usa_la_pagina_404_personalizada(self):
        response = self.client.get("/ruta-que-no-existe/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "No encontramos esta página", status_code=404)
