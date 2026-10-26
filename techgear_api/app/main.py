from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import database

from app.routers import pedidos, productos


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.connect()
    try:
        await database.ping()
        yield
    finally:
        await database.disconnect()


app = FastAPI(title="TechGear API", version="0.1.0", lifespan=lifespan)

app.include_router(productos.router)
app.include_router(pedidos.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    await database.ping()
    return {"status": "ok", "database": "connected"}


# uvicorn app.main:app --reload

