import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import close, init_indexes, ping
from app.routers import auth, pedidos, productos, usuarios

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "techgear_web"
for import_root in (PROJECT_ROOT, WEB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "techgear_web.settings")

from django.conf import settings
from django.core.asgi import get_asgi_application

django_application = get_asgi_application()

# --- TEMPORARY DEBUG (remove once the 400 is fixed) ---
print("DJANGO ALLOWED_HOSTS:", settings.ALLOWED_HOSTS, flush=True)
print("DJANGO DEBUG:", settings.DEBUG, flush=True)
print("RENDER_EXTERNAL_HOSTNAME:", os.getenv("RENDER_EXTERNAL_HOSTNAME"), flush=True)
# -------------------------------------------------------


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_indexes()
        yield
    finally:
        close()


app = FastAPI(title="TechGear API", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# --- TEMPORARY DEBUG (remove once the 400 is fixed) ---
@app.middleware("http")
async def log_host(request: Request, call_next):
    print("HOST HEADER:", request.headers.get("host"), request.url.path, flush=True)
    return await call_next(request)
# -------------------------------------------------------


app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(productos.router)
app.include_router(pedidos.router)


@app.get("/health", tags=["Health"])
def health():
    ping()
    return {"status": "ok", "database": "connected"}


app.mount("/", django_application, name="storefront")