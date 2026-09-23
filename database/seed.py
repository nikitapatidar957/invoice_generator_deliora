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

SEED_PRODUCTS = [
    {"name": "FLEUR", "sku": "DEL-FLEUR"},
    {"name": "ALPHA", "sku": "DEL-ALPHA"},
    {"name": "MISTIQUE", "sku": "DEL-MISTIQUE"},
    {"name": "VELVET", "sku": "DEL-VELVET"},
    {"name": "BLANC", "sku": "DEL-BLANC"},
]


def seed_if_needed(conn) -> None:
    now = datetime.now(timezone.utc).isoformat()

    setting_rows = {**BUSINESS_CONFIG}
    setting_rows["terms"] = TERMS_AND_CONDITIONS
    setting_rows["footer_thank_you"] = INVOICE_FOOTER_THANK_YOU
    setting_rows["tagline"] = INVOICE_TAGLINE

    for key, value in setting_rows.items():
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, str(value)),
        )

    existing = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    if existing:
        return

    for product in SEED_PRODUCTS:
        conn.execute(
            """
            INSERT INTO products (
                name, sku, size, price, gst_rate, hsn_sac,
                available_quantity, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                product["name"],
                product["sku"],
                DEFAULT_SIZE,
                DEFAULT_PRODUCT_PRICE,
                DEFAULT_GST_RATE,
                DEFAULT_HSN,
                100,
                now,
                now,
            ),
        )
