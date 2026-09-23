import re
import sqlite3
from datetime import datetime

from config import INVOICE_PREFIX
from database.db import db_session
from services.calculation_service import calculate_invoice
from services.number_to_words import amount_in_words

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
UPI_RE = re.compile(r"^[\w.\-]{2,256}@[a-zA-Z]{2,64}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PAYMENT_METHODS = {"cash", "upi", "bank", "card", "other"}


def get_settings() -> dict:
    with db_session() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def update_settings(values: dict) -> dict:
    with db_session() as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )
    return get_settings()


def list_products(active_only: bool = False) -> list[dict]:
    sql = "SELECT * FROM products"
    params = []
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY name"
    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def get_product(product_id: int) -> dict | None:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    return dict(row) if row else None


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
    payload = (
        name,
        sku,
        (data.get("size") or "").strip(),
        price,
        gst_rate,
        (data.get("hsn_sac") or "").strip(),
        qty,
        1 if data.get("is_active", True) else 0,
        now,
    )

    try:
        with db_session() as conn:
            if product_id:
                conn.execute(
                    """
                    UPDATE products SET
                        name = ?, sku = ?, size = ?, price = ?, gst_rate = ?,
                        hsn_sac = ?, available_quantity = ?, is_active = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (*payload, product_id),
                )
            else:
                cur = conn.execute(
                    """
                    INSERT INTO products (
                        name, sku, size, price, gst_rate, hsn_sac,
                        available_quantity, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*payload, now),
                )
                product_id = cur.lastrowid
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    except sqlite3.IntegrityError as exc:
        raise ValueError("A product with this SKU already exists.") from exc
    return dict(row)


def deactivate_product(product_id: int) -> None:
    with db_session() as conn:
        conn.execute(
            "UPDATE products SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(timespec="seconds"), product_id),
        )


def peek_next_invoice_number(invoice_date: str | None = None) -> str:
    year = _invoice_year(invoice_date)
    with db_session() as conn:
        row = conn.execute(
            "SELECT last_number FROM invoice_counters WHERE year = ?", (year,)
        ).fetchone()
    nxt = (row["last_number"] if row else 0) + 1
    return f"{INVOICE_PREFIX}-{year}-{nxt:04d}"


def _invoice_year(invoice_date: str | None) -> int:
    if invoice_date:
        return datetime.strptime(invoice_date, "%Y-%m-%d").year
    return datetime.now().year


def _allocate_invoice_number(conn, year: int) -> str:
    row = conn.execute(
        "SELECT last_number FROM invoice_counters WHERE year = ?", (year,)
    ).fetchone()
    nxt = (row["last_number"] if row else 0) + 1
    conn.execute(
        """
        INSERT INTO invoice_counters (year, last_number) VALUES (?, ?)
        ON CONFLICT(year) DO UPDATE SET last_number = excluded.last_number
        """,
        (year, nxt),
    )
    return f"{INVOICE_PREFIX}-{year}-{nxt:04d}"


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

    tax_type = payload.get("tax_type")
    if tax_type not in {"intra", "inter"}:
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
    with db_session() as conn:
        placeholders = ",".join("?" * len(product_ids))
        rows = conn.execute(
            f"SELECT * FROM products WHERE id IN ({placeholders})",
            product_ids,
        ).fetchall()
        products = {row["id"]: dict(row) for row in rows}

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
    words = amount_in_words(totals["grand_total"])
    invoice_date = payload.get("invoice_date") or datetime.now().strftime("%Y-%m-%d")
    year = _invoice_year(invoice_date)
    created_at = datetime.now().isoformat(timespec="seconds")

    with db_session() as conn:
        invoice_number = _allocate_invoice_number(conn, year)
        existing = conn.execute(
            "SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,)
        ).fetchone()
        if existing:
            raise ValueError("Duplicate invoice number generated. Please try saving again.")

        cur = conn.execute(
            """
            INSERT INTO invoices (
                invoice_number, invoice_date, customer_name, customer_phone,
                customer_email, customer_address, customer_gstin, tax_type,
                payment_method, payment_status, customer_upi_id, transaction_reference,
                amount_paid, balance_due, subtotal, total_discount, total_taxable,
                total_gst, total_cgst, total_sgst, total_igst, grand_total,
                amount_in_words, pdf_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?)
            """,
            (
                invoice_number,
                invoice_date,
                payload["customer_name"].strip(),
                (payload.get("customer_phone") or "").strip(),
                (payload.get("customer_email") or "").strip(),
                (payload.get("customer_address") or "").strip(),
                (payload.get("customer_gstin") or "").strip().upper(),
                payload["tax_type"],
                payload["payment_method"].lower(),
                totals["payment_status"],
                (payload.get("customer_upi_id") or "").strip(),
                (payload.get("transaction_reference") or "").strip(),
                totals["amount_paid"],
                totals["balance_due"],
                totals["subtotal"],
                totals["total_discount"],
                totals["total_taxable"],
                totals["total_gst"],
                totals["total_cgst"],
                totals["total_sgst"],
                totals["total_igst"],
                totals["grand_total"],
                words,
                created_at,
            ),
        )
        invoice_id = cur.lastrowid

        for item in totals["items"]:
            conn.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id, product_id, product_name, sku, hsn_sac, quantity,
                    unit_price, discount_percent, discount_fixed, discount_amount,
                    gst_rate, taxable_amount, gst_amount, cgst_amount, sgst_amount,
                    igst_amount, line_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    item["product_id"],
                    item["product_name"],
                    item["sku"],
                    item["hsn_sac"],
                    item["quantity"],
                    item["unit_price"],
                    item["discount_percent"],
                    item["discount_fixed"],
                    item["discount_amount"],
                    item["gst_rate"],
                    item["taxable_amount"],
                    item["gst_amount"],
                    item["cgst_amount"],
                    item["sgst_amount"],
                    item["igst_amount"],
                    item["line_total"],
                ),
            )
            conn.execute(
                """
                UPDATE products
                SET available_quantity = CASE
                    WHEN available_quantity >= ? THEN available_quantity - ?
                    ELSE 0
                END,
                updated_at = ?
                WHERE id = ?
                """,
                (item["quantity"], item["quantity"], created_at, item["product_id"]),
            )

    return get_invoice(invoice_id)


def get_invoice(invoice_id: int) -> dict | None:
    with db_session() as conn:
        invoice = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        if not invoice:
            return None
        items = conn.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY id",
            (invoice_id,),
        ).fetchall()
    data = dict(invoice)
    data["items"] = [dict(item) for item in items]
    data["business"] = get_settings()
    return data


def search_invoices(query: str = "") -> list[dict]:
    q = (query or "").strip()
    sql = "SELECT * FROM invoices"
    params: list = []
    if q:
        sql += """
            WHERE invoice_number LIKE ?
               OR customer_name LIKE ?
               OR customer_phone LIKE ?
               OR invoice_date LIKE ?
        """
        like = f"%{q}%"
        params = [like, like, like, like]
    sql += " ORDER BY created_at DESC, id DESC"
    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def set_invoice_pdf_path(invoice_id: int, pdf_path: str) -> None:
    with db_session() as conn:
        conn.execute("UPDATE invoices SET pdf_path = ? WHERE id = ?", (pdf_path, invoice_id))
