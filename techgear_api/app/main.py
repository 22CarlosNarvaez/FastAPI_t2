from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import database


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.connect()
    try:
        await database.ping()
        yield
    finally:
        await database.disconnect()


app = FastAPI(title="TechGear API", version="0.1.0", lifespan=lifespan)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    await database.ping()
    return {"status": "ok", "database": "connected"}
