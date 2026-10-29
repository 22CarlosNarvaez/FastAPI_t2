from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings


client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=8000)
db: Database = client[settings.db_name]

col_usuarios = db["usuarios"]
col_productos = db["productos"]
col_pedidos = db["pedidos"]


def init_indexes() -> None:
    col_usuarios.create_index("email", unique=True)


def ping() -> None:
    client.admin.command("ping")


def close() -> None:
    client.close()
