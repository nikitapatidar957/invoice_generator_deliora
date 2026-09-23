# DeLiora Essence by Patidar — Invoice App

Billing for Fleur, Alpha, Mistique, Velvet and Blanc using MongoDB Atlas. The app does not process online payments.

## Install

```bash
cd invoice_generator_deliora
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and put in GSTIN, address, phone, email, website, state and state code when you have them. Until then the invoice uses placeholders.

The DeLiora logo is taken from `logo.cdr` (this file is already a PNG) and saved as `static/images/deliora-logo.png`. Do not replace it with a generated logo.

## Run

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) on this laptop.

## Daily use

1. Enter the customer. Leave GSTIN blank for a walk-in consumer.
2. Add one or more perfumes. Default selling price is ₹1,499 (editable). Discount % defaults to 0; Disc ₹ is a fixed amount off. Discount is subtracted first, then GST is applied.
3. Choose Intra-State (CGST + SGST) or Inter-State (IGST). GST % is stored per perfume, not hard-coded as a legal rate.
4. Choose payment method. UPI ID appears only for UPI. This app only records payment details; it does not collect money online.
5. Watch the live preview on the same screen, then **Save & Download PDF**.

Invoice numbers look like `DEL-2026-0001` and continue from MongoDB Atlas after restart.

## Pages

- `/` — create invoice with live preview
- `/history` — search, view, download
- `/products` — add, edit, deactivate (no hard delete)

PDFs are written with ReportLab into `invoices/DEL-YYYY-NNNN.pdf`.

## MongoDB Atlas

The application stores settings, products, invoices, invoice items, counters,
and ID sequences in MongoDB Atlas collections. Configure `MONGODB_URI` and
optionally `MONGODB_DATABASE=deliora` in `.env`, then verify the connection with:

```bash
python -c "from database.mongodb import verify_mongo_connection; print(verify_mongo_connection())"
```

