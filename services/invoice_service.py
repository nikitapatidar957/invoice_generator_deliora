import re
from datetime import datetime

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from config import INVOICE_PREFIX
from database.db import get_collection, get_database, next_id
from services.calculation_service import calculate_invoice
from services.number_to_words import amount_in_words

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
UPI_RE = re.compile(r"^[\w.\-]{2,256}@[a-zA-Z]{2,64}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PAYMENT_METHODS = {"cash", "upi", "bank", "card", "other"}


def _document(document: dict | None) -> dict | None:
    if not document:
        return None
    document.pop("_id", None)
    return document


def get_settings() -> dict:
    rows = get_collection("settings").find({}, {"_id": 0, "key": 1, "value": 1})
    return {row["key"]: row["value"] for row in rows}


def update_settings(values: dict) -> dict:
    settings = get_collection("settings")
    for key, value in values.items():
        settings.update_one(
            {"key": key},
            {"$set": {"key": key, "value": str(value)}},
            upsert=True,
        )
    return get_settings()


def list_products(active_only: bool = False) -> list[dict]:
    query = {"is_active": 1} if active_only else {}
    products = get_collection("products").find(query, {"_id": 0}).sort("name", 1)
    return [_document(row) for row in products]


def get_product(product_id: int) -> dict | None:
    return _document(get_collection("products").find_one({"id": int(product_id)}, {"_id": 0}))


def save_product(data: dict, product_id: int | None = None) -> dict:
    name = (data.get("name") or "").strip()
    sku = (data.get("sku") or "").strip().upper()
    if not name:
        raise ValueError("Product name is required.")
    if not sku:
        raise ValueError("SKU is required.")
    price = float(data.get("price", 0))
    gst_rate = float(data.get("gst_rate", 0))
    qty = int(data.get("available_quantity", 0))
    if price < 0:
        raise ValueError("Price cannot be negative.")
    if gst_rate < 0:
        raise ValueError("GST rate cannot be negative.")
    if qty < 0:
        raise ValueError("Available quantity cannot be negative.")

    now = datetime.now().isoformat(timespec="seconds")
    fields = {
        "name": name,
        "sku": sku,
        "size": (data.get("size") or "").strip(),
        "price": price,
        "gst_rate": gst_rate,
        "hsn_sac": (data.get("hsn_sac") or "").strip(),
        "available_quantity": qty,
        "is_active": 1 if data.get("is_active", True) else 0,
        "updated_at": now,
    }
    products = get_collection("products")
    try:
        if product_id:
            products.update_one({"id": int(product_id)}, {"$set": fields})
        else:
            product_id = next_id("products")
            fields.update({"_id": product_id, "id": product_id, "created_at": now})
            products.insert_one(fields)
    except DuplicateKeyError as exc:
        raise ValueError("A product with this SKU already exists.") from exc
    return get_product(product_id)


def deactivate_product(product_id: int) -> None:
    get_collection("products").update_one(
        {"id": int(product_id)},
        {"$set": {"is_active": 0, "updated_at": datetime.now().isoformat(timespec="seconds")}},
    )


def _invoice_year(invoice_date: str | None) -> int:
    return datetime.strptime(invoice_date, "%Y-%m-%d").year if invoice_date else datetime.now().year


def peek_next_invoice_number(invoice_date: str | None = None) -> str:
    year = _invoice_year(invoice_date)
    counter = get_collection("invoice_counters").find_one({"_id": year})
    last_number = counter.get("last_number", 0) if counter else 0
    return f"{INVOICE_PREFIX}-{year}-{last_number + 1:04d}"


def _allocate_invoice_number(year: int, session=None) -> str:
    counter = get_collection("invoice_counters").find_one_and_update(
        {"_id": year},
        {"$inc": {"last_number": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
        session=session,
    )
    return f"{INVOICE_PREFIX}-{year}-{counter['last_number']:04d}"


def validate_payload(payload: dict) -> None:
    customer_name = (payload.get("customer_name") or "").strip()
    if not customer_name:
        raise ValueError("Customer name is required.")
    gstin = (payload.get("customer_gstin") or "").strip().upper()
    if gstin and not GSTIN_RE.match(gstin):
        raise ValueError("Customer GSTIN format looks invalid. Leave it blank for a regular consumer.")
    email = (payload.get("customer_email") or "").strip()
    if email and not EMAIL_RE.match(email):
        raise ValueError("Customer email format looks invalid.")
    if payload.get("tax_type") not in {"intra", "inter"}:
        raise ValueError("Select Intra-State or Inter-State tax type.")
    method = (payload.get("payment_method") or "").lower()
    if method not in PAYMENT_METHODS:
        raise ValueError("Select a valid payment method.")
    upi = (payload.get("customer_upi_id") or "").strip()
    if method == "upi":
        if not upi:
            raise ValueError("Enter the customer UPI ID.")
        if not UPI_RE.match(upi):
            raise ValueError("UPI ID format looks invalid. Example: nikita@upi")
    else:
        payload["customer_upi_id"] = ""
    if method not in {"upi", "bank", "card"}:
        payload["transaction_reference"] = payload.get("transaction_reference") or ""


def create_invoice(payload: dict) -> dict:
    validate_payload(payload)
    items_in = payload.get("items") or []
    if not items_in:
        raise ValueError("Add at least one perfume.")

    product_ids = [int(item["product_id"]) for item in items_in]
    products = {
        row["id"]: row
        for row in get_collection("products").find({"id": {"$in": product_ids}}, {"_id": 0})
    }
    enriched = []
    for item in items_in:
        product = products.get(int(item["product_id"]))
        if not product:
            raise ValueError("One of the selected perfumes was not found.")
        if not product["is_active"]:
            raise ValueError(f"{product['name']} is inactive and cannot be billed.")
        enriched.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "sku": product["sku"],
            "hsn_sac": product["hsn_sac"],
            "quantity": int(item["quantity"]),
            "unit_price": float(item.get("unit_price", product["price"])),
            "discount_percent": float(item.get("discount_percent") or 0),
            "discount_fixed": float(item.get("discount_fixed") or 0),
            "gst_rate": float(item.get("gst_rate", product["gst_rate"])),
        })

    totals = calculate_invoice(
        enriched,
        payload["tax_type"],
        payload.get("payment_status"),
        payload.get("amount_paid") or 0,
    )
    invoice_date = payload.get("invoice_date") or datetime.now().strftime("%Y-%m-%d")
    created_at = datetime.now().isoformat(timespec="seconds")
    invoice_id = next_id("invoices")
    invoice = {
        "_id": invoice_id,
        "id": invoice_id,
        "invoice_number": None,
        "invoice_date": invoice_date,
        "customer_name": payload["customer_name"].strip(),
        "customer_phone": (payload.get("customer_phone") or "").strip(),
        "customer_email": (payload.get("customer_email") or "").strip(),
        "customer_address": (payload.get("customer_address") or "").strip(),
        "customer_gstin": (payload.get("customer_gstin") or "").strip().upper(),
        "tax_type": payload["tax_type"],
        "payment_method": payload["payment_method"].lower(),
        "payment_status": totals["payment_status"],
        "customer_upi_id": (payload.get("customer_upi_id") or "").strip(),
        "transaction_reference": (payload.get("transaction_reference") or "").strip(),
        "amount_paid": totals["amount_paid"],
        "balance_due": totals["balance_due"],
        "subtotal": totals["subtotal"],
        "total_discount": totals["total_discount"],
        "total_taxable": totals["total_taxable"],
        "total_gst": totals["total_gst"],
        "total_cgst": totals["total_cgst"],
        "total_sgst": totals["total_sgst"],
        "total_igst": totals["total_igst"],
        "grand_total": totals["grand_total"],
        "amount_in_words": amount_in_words(totals["grand_total"]),
        "footer_enabled": bool(payload.get("footer_enabled", True)),
        "footer_text": (payload.get("footer_text") or "").strip(),
        "tagline": (payload.get("tagline") or "").strip(),
        "terms_enabled": bool(payload.get("terms_enabled", True)),
        "terms_text": (payload.get("terms_text") or "").strip(),
        "created_at": created_at,
    }

    database = get_database()
    invoices = get_collection("invoices")
    items_collection = get_collection("invoice_items")
    with database.client.start_session() as session:
        with session.start_transaction():
            invoice["invoice_number"] = _allocate_invoice_number(_invoice_year(invoice_date), session)
            invoices.insert_one(invoice, session=session)
            for item in totals["items"]:
                item_id = next_id("invoice_items", session)
                items_collection.insert_one(
                    {"_id": item_id, "id": item_id, "invoice_id": invoice_id, **item},
                    session=session,
                )
                get_collection("products").update_one(
                    {"id": item["product_id"]},
                    {
                        "$inc": {"available_quantity": -item["quantity"]},
                        "$set": {"updated_at": created_at},
                    },
                    session=session,
                )
    return get_invoice(invoice_id)


def get_invoice(invoice_id: int) -> dict | None:
    invoice = _document(get_collection("invoices").find_one({"id": int(invoice_id)}, {"_id": 0}))
    if not invoice:
        return None
    items = get_collection("invoice_items").find(
        {"invoice_id": int(invoice_id)}, {"_id": 0}
    ).sort("id", 1)
    invoice["items"] = [_document(item) for item in items]
    invoice["business"] = get_settings()
    return invoice


def search_invoices(query: str = "") -> list[dict]:
    q = (query or "").strip()
    filter_query = {}
    if q:
        escaped = re.escape(q)
        filter_query = {"$or": [
            {"invoice_number": {"$regex": escaped, "$options": "i"}},
            {"customer_name": {"$regex": escaped, "$options": "i"}},
            {"customer_phone": {"$regex": escaped, "$options": "i"}},
            {"invoice_date": {"$regex": escaped, "$options": "i"}},
        ]}
    invoices = get_collection("invoices").find(filter_query, {"_id": 0}).sort([
        ("created_at", -1),
        ("id", -1),
    ])
    return [_document(row) for row in invoices]


