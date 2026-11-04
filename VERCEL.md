# Despliegue en Vercel

Configura el proyecto Vercel con el repositorio y deja **Root Directory** en la
raíz del repositorio. El `vercel.json` raíz publica FastAPI y la tienda Django
montada en esa API, igual que el servicio de Render.

Configura estas variables en **Project Settings → Environment Variables**:

- `MONGODB_URI`: cadena de conexión de MongoDB Atlas.
- `SECRET_KEY`: clave secreta que usa FastAPI para firmar tokens.
- `DJANGO_SECRET_KEY`: clave secreta de Django. El nombre debe incluir los dos
  guiones bajos; `DJANGO_SECRETKEY` no es reconocido.

Configura las tres variables para cada entorno que uses (**Production** y/o
**Preview**) y vuelve a desplegar después de guardarlas. Sin ellas, la función
no puede iniciar.

`VERCEL_URL` la proporciona Vercel y la aplicación la usa para que Django llame
a FastAPI en el mismo despliegue, por lo que `API_URL` es opcional en ese caso.
Si alojas la API en otro dominio, configura `API_URL` con la URL base de esa
API. No configures `DJANGO_DEBUG=true` en producción.

Al añadir un dominio propio, agrega su host a `DJANGO_ALLOWED_HOSTS` y su origen
HTTPS a `DJANGO_CSRF_TRUSTED_ORIGINS`.
