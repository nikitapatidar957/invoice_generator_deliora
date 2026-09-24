from flask import Blueprint, jsonify, render_template, request, send_file

from services.calculation_service import calculate_invoice
from services.invoice_service import (
    create_invoice,
    get_invoice,
    get_settings,
    list_products,
    peek_next_invoice_number,
)
from services.number_to_words import amount_in_words
from services.pdf_service import generate_invoice_pdf

invoice_bp = Blueprint("invoice", __name__)


@invoice_bp.get("/")
def create_page():
    return render_template(
        "invoice.html",
        business=get_settings(),
        products=list_products(active_only=True),
        next_invoice_number=peek_next_invoice_number(),
    )


@invoice_bp.get("/api/next-invoice-number")
def next_number():
    return jsonify({"invoice_number": peek_next_invoice_number()})


@invoice_bp.get("/api/business")
def business():
    return jsonify(get_settings())


@invoice_bp.post("/api/calculate")
def calculate():
    payload = request.get_json(force=True) or {}
    try:
        totals = calculate_invoice(
            payload.get("items") or [],
            payload.get("tax_type") or "intra",
            payload.get("payment_status") or "paid",
            payload.get("amount_paid") or 0,
            payload.get("previous_due") or 0,
            bool(payload.get("due_payment_only")),
        )
        totals["amount_in_words"] = amount_in_words(totals["grand_total"])
        return jsonify(totals)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@invoice_bp.post("/api/invoices")
def save_invoice():
    payload = request.get_json(force=True) or {}
    try:
        invoice = create_invoice(payload)
        invoice["download_name"] = f"{invoice['invoice_number']}.pdf"
        return jsonify(invoice)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@invoice_bp.get("/api/invoices/<int:invoice_id>")
def invoice_detail(invoice_id: int):
    invoice = get_invoice(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found."}), 404
    return jsonify(invoice)


@invoice_bp.get("/invoices/<int:invoice_id>/pdf")
def download_pdf(invoice_id: int):
    invoice = get_invoice(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found."}), 404
    pdf_path = generate_invoice_pdf(invoice_id)
    response = send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{invoice['invoice_number']}.pdf",
    )
    response.call_on_close(lambda: pdf_path.unlink(missing_ok=True))
    return response
