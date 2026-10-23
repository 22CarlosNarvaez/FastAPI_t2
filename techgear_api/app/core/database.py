from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings

_client: AsyncMongoClient | None = None


def connect() -> None:
    global _client
    if _client is None:
        _client = AsyncMongoClient(settings.mongodb_uri)


async def disconnect() -> None:
    global _client
    if _client is not None:
        client = _client
        _client = None
        await client.close()


def get_database() -> AsyncDatabase:
    if _client is None:
        raise RuntimeError("Database client is not initialized.")
    return _client[settings.mongodb_db_name]


async def ping() -> None:
    if _client is None:
        raise RuntimeError("Database client is not initialized.")
    await _client.admin.command("ping")
