SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    size TEXT NOT NULL DEFAULT '',
    price REAL NOT NULL CHECK (price >= 0),
    gst_rate REAL NOT NULL CHECK (gst_rate >= 0),
    hsn_sac TEXT NOT NULL DEFAULT '',
    available_quantity INTEGER NOT NULL DEFAULT 0 CHECK (available_quantity >= 0),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoice_counters (
    year INTEGER PRIMARY KEY,
    last_number INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT NOT NULL UNIQUE,
    invoice_date TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL DEFAULT '',
    customer_email TEXT NOT NULL DEFAULT '',
    customer_address TEXT NOT NULL DEFAULT '',
    customer_gstin TEXT NOT NULL DEFAULT '',
    tax_type TEXT NOT NULL CHECK (tax_type IN ('intra', 'inter')),
    payment_method TEXT NOT NULL,
    payment_status TEXT NOT NULL CHECK (payment_status IN ('paid', 'partial', 'unpaid')),
    customer_upi_id TEXT NOT NULL DEFAULT '',
    transaction_reference TEXT NOT NULL DEFAULT '',
    amount_paid REAL NOT NULL DEFAULT 0,
    balance_due REAL NOT NULL DEFAULT 0,
    subtotal REAL NOT NULL,
    total_discount REAL NOT NULL,
    total_taxable REAL NOT NULL,
    total_gst REAL NOT NULL,
    total_cgst REAL NOT NULL DEFAULT 0,
    total_sgst REAL NOT NULL DEFAULT 0,
    total_igst REAL NOT NULL DEFAULT 0,
    grand_total REAL NOT NULL,
    amount_in_words TEXT NOT NULL,
    pdf_path TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    sku TEXT NOT NULL,
    hsn_sac TEXT NOT NULL DEFAULT '',
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    discount_percent REAL NOT NULL DEFAULT 0,
    discount_fixed REAL NOT NULL DEFAULT 0,
    discount_amount REAL NOT NULL,
    gst_rate REAL NOT NULL,
    taxable_amount REAL NOT NULL,
    gst_amount REAL NOT NULL,
    cgst_amount REAL NOT NULL DEFAULT 0,
    sgst_amount REAL NOT NULL DEFAULT 0,
    igst_amount REAL NOT NULL DEFAULT 0,
    line_total REAL NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_name);
CREATE INDEX IF NOT EXISTS idx_invoices_phone ON invoices(customer_phone);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);
"""
