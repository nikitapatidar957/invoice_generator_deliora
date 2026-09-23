"""Shared MongoDB Atlas connection helpers.

These helpers provide the single Atlas connection used by the application.
"""

import os
from functools import lru_cache

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

from config import BASE_DIR

load_dotenv(BASE_DIR / ".env")

DATABASE_NAME = os.getenv("MONGODB_DATABASE", "deliora")

COLLECTIONS = {
    "settings": "settings",
    "products": "products",
    "invoices": "invoices",
    "invoice_items": "invoice_items",
    "invoice_counters": "invoice_counters",
    "sequences": "sequences",
    "users": "users",
}


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is missing from .env")

    return MongoClient(
        uri,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000,
    )


def get_mongo_database():
    return get_mongo_client()[DATABASE_NAME]


def verify_mongo_connection() -> dict:
    """Ping Atlas and return the server response or raise its real error."""
    return get_mongo_client().admin.command("ping")


def close_mongo_connection() -> None:
    client = get_mongo_client.cache_info()
    if client.currsize:
        get_mongo_client().close()
        get_mongo_client.cache_clear()