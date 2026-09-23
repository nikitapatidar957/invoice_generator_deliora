from datetime import datetime, timezone

from config import (
    BUSINESS_CONFIG,
    DEFAULT_GST_RATE,
    DEFAULT_HSN,
    DEFAULT_PRODUCT_PRICE,
    DEFAULT_SIZE,
    INVOICE_FOOTER_THANK_YOU,
    INVOICE_TAGLINE,
    TERMS_AND_CONDITIONS,
)
from database.db import next_id
from database.mongodb import COLLECTIONS

SEED_PRODUCTS = [
    {"name": "FLEUR", "sku": "DEL-FLEUR"},
    {"name": "ALPHA", "sku": "DEL-ALPHA"},
    {"name": "MISTIQUE", "sku": "DEL-MISTIQUE"},
    {"name": "VELVET", "sku": "DEL-VELVET"},
    {"name": "BLANC", "sku": "DEL-BLANC"},
]


def seed_if_needed(database) -> None:
    now = datetime.now(timezone.utc).isoformat()
    settings = {**BUSINESS_CONFIG}
    settings.update({
        "terms": TERMS_AND_CONDITIONS,
        "footer_thank_you": INVOICE_FOOTER_THANK_YOU,
        "tagline": INVOICE_TAGLINE,
    })

    settings_collection = database[COLLECTIONS["settings"]]
    for key, value in settings.items():
        settings_collection.update_one(
            {"key": key},
            {"$set": {"key": key, "value": str(value)}},
            upsert=True,
        )

    products = database[COLLECTIONS["products"]]
    if products.count_documents({}):
        return

    for product in SEED_PRODUCTS:
        product_id = next_id("products")
        products.insert_one({
            "_id": product_id,
            "id": product_id,
            "name": product["name"],
            "sku": product["sku"],
            "size": DEFAULT_SIZE,
            "price": DEFAULT_PRODUCT_PRICE,
            "gst_rate": DEFAULT_GST_RATE,
            "hsn_sac": DEFAULT_HSN,
            "available_quantity": 100,
            "is_active": 1,
            "created_at": now,
            "updated_at": now,
        })
