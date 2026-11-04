# 🛒 TechGear

Aplicación web de comercio electrónico para explorar productos tecnológicos,
crear y gestionar pedidos, y administrar el catálogo. Está construida con
**FastAPI**, **Django** y **MongoDB**: FastAPI ofrece la API y Django sirve la
tienda web que consume esa API.

> 💳 Los pagos que presenta la aplicación son **simulados**. No se realiza
> ningún cobro real ni se procesan datos de tarjetas.

## ✨ Funcionalidades

- 🧑‍💻 Registro e inicio de sesión de clientes y administradores.
- 🔐 Autenticación de la API con tokens Bearer (JWT).
- 🛍️ Catálogo de productos con consulta de detalle.
- 📦 Creación y consulta de pedidos asociados al usuario.
- 💳 Simulación del pago de pedidos con tarjeta, Nequi o transferencia.
- 🚚 Flujo de pedidos: pago, envío y confirmación de recepción.
- 🧰 Panel para que administradores publiquen y eliminen productos, y gestionen
  pedidos.
- 📚 Documentación interactiva de la API generada por FastAPI.

## 🧱 Tecnologías

| Área | Tecnología |
| --- | --- |
| API y lógica de negocio | Python, FastAPI, Pydantic |
| Sitio web y plantillas | Django |
| Base de datos | MongoDB |
| Autenticación | JWT y contraseñas con hash |
| Archivos estáticos | WhiteNoise |
| Despliegue | Render y Vercel |

## 🗂️ Estructura del proyecto

```text
.
├── api/
│   └── index.py                 # Punto de entrada serverless de Vercel
├── techgear_api/
│   ├── app/
│   │   ├── core/                # Configuración, seguridad y conexión a MongoDB
│   │   ├── models/              # Esquemas de entrada y salida
│   │   ├── routers/             # Rutas de la API
│   │   ├── services/            # Lógica de usuarios, productos y pedidos
│   │   └── main.py              # Aplicación FastAPI y montaje de Django
│   └── requirements.txt
├── techgear_web/
│   ├── store/
│   │   ├── templates/           # Plantillas de la tienda
│   │   ├── static/              # Recursos estáticos de la tienda
│   │   ├── api_client.py        # Cliente Django para consumir FastAPI
│   │   ├── tests.py             # Pruebas de rutas y del cliente de API
│   │   ├── urls.py              # Rutas del sitio web
│   │   └── views.py             # Vistas de catálogo, pedidos y administración
│   ├── settings.py              # Configuración Django
│   └── manage.py                # Comandos de Django
├── render.yaml                  # Configuración de despliegue en Render
├── requirements.txt             # Dependencias para el despliegue combinado
├── vercel.json                  # Enrutamiento de Vercel a FastAPI
└── VERCEL.md                    # Instrucciones específicas de Vercel
```

## ⚙️ Requisitos

- Python 3.
- Una instancia accesible de MongoDB, por ejemplo MongoDB Atlas.
- `pip` para instalar las dependencias.

### 🚀 Ejecución local

1. Clona el repositorio y entra en su directorio:

   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd FastAPI_T2
   ```

2. Crea y activa un entorno virtual:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   En Windows PowerShell, actívalo con:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

3. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Configura las variables de entorno necesarias. No publiques estos valores ni
   los guardes en el repositorio:

   ```bash
   export MONGODB_URI='tu_uri_de_mongodb'
   export SECRET_KEY='una_clave_secreta_larga_y_aleatoria'
   export DJANGO_SECRET_KEY='otra_clave_secreta_larga_y_aleatoria'
   ```

   `MONGODB_URI` y `SECRET_KEY` son necesarios para FastAPI. Para desarrollo
   local, la configuración de Django proporciona una clave de desarrollo si
   `DJANGO_SECRET_KEY` no está definida; en despliegues siempre debe definirse.
   También puedes colocar las variables que consume FastAPI en
   `techgear_api/.env`, que está excluido del control de versiones.

5. Inicia FastAPI desde la raíz del proyecto:

   ```bash
   uvicorn app.main:app --app-dir techgear_api --reload
   ```

   La API y la tienda Django montada estarán disponibles en
   `http://127.0.0.1:8000`.

## 📡 Rutas principales

### API FastAPI

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/health` | Comprueba la conexión con MongoDB. |
| `POST` | `/auth/login` | Inicia sesión y entrega un token. |
| `POST` | `/usuarios/registro` | Registra un cliente o administrador. |
| `GET` | `/usuarios/me` | Consulta el usuario autenticado. |
| `GET` | `/productos` | Lista el catálogo. |
| `GET` | `/productos/{producto_id}` | Consulta un producto. |
| `POST` | `/productos` | Crea un producto (administrador). |
| `PUT` | `/productos/{producto_id}` | Actualiza un producto (administrador). |
| `DELETE` | `/productos/{producto_id}` | Elimina un producto (administrador). |
| `POST` | `/pedidos` | Crea un pedido (usuario autenticado). |
| `GET` | `/pedidos` | Lista los pedidos del usuario autenticado. |
| `POST` | `/pedidos/{pedido_id}/pagar` | Registra un pago simulado. |
| `PATCH` | `/pedidos/{pedido_id}/enviar` | Marca un pedido como enviado (administrador). |
| `PATCH` | `/pedidos/{pedido_id}/recibir` | Confirma la recepción de un pedido. |

La documentación interactiva está disponible en `/docs`; el esquema OpenAPI
está en `/openapi.json`.

### Tienda Django

| Ruta | Uso |
| --- | --- |
| `/` | Catálogo de productos. |
| `/login/` y `/registro/` | Acceso y creación de cuenta. |
| `/pedidos/` | Consulta y seguimiento de pedidos. |
| `/pedidos/pagar/` | Pago simulado de pedidos pendientes. |
| `/panel/` | Administración del catálogo (requiere rol administrador). |
| `/admin/` | Interfaz administrativa de Django. |

Las operaciones que modifican pedidos y productos se envían a FastAPI. Las
rutas que realizan acciones, como crear pedidos o pagar, requieren `POST`.

## 🧪 Pruebas

Para ejecutar las pruebas de la aplicación Django:

```bash
python techgear_web/manage.py test store
```

## ☁️ Despliegue

### Render

El archivo [`render.yaml`](./render.yaml) define el servicio web, el comando de
instalación y arranque, y la ruta de comprobación de salud `/health`. Configura
en el servicio las variables `MONGODB_URI`, `SECRET_KEY` y
`DJANGO_SECRET_KEY`. Para permitir el registro de administradores también se
puede configurar `ADMIN_REGISTRATION_CODE`.

### Vercel

Configura el proyecto para usar la **raíz del repositorio** como Root Directory.
En **Project Settings → Environment Variables**, agrega `MONGODB_URI`,
`SECRET_KEY` y `DJANGO_SECRET_KEY` en cada entorno que despliegues. El nombre
de esta última variable debe incluir los dos guiones bajos: `DJANGO_SECRETKEY`
no se reconoce. Guarda los cambios y vuelve a desplegar.

`VERCEL_URL` es proporcionada automáticamente por Vercel. `API_URL` es opcional
cuando Django consume FastAPI desde el mismo despliegue; úsala si la API se
encuentra en otro dominio. Consulta [`VERCEL.md`](./VERCEL.md) para más detalles.

## 🔒 Seguridad y configuración

- No subas archivos `.env`, claves, tokens ni credenciales de MongoDB.
- Usa claves aleatorias, únicas y distintas para producción.
- Define variables sensibles desde el panel de entorno del proveedor de
  despliegue.
- El alta de cuentas con rol administrador requiere `ADMIN_REGISTRATION_CODE`.
- Las contraseñas se almacenan con hash; los accesos protegidos usan tokens.
- Los pagos son de demostración y no deben considerarse una integración de pago
  real.

## 📄 Licencia

No se especifica una licencia en este repositorio. Antes de reutilizar o
redistribuir el proyecto, confirma los permisos con sus responsables.
