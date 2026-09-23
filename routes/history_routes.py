from flask import Blueprint, jsonify, render_template, request

from services.invoice_service import search_invoices, get_invoice, get_settings

history_bp = Blueprint("history", __name__)


@history_bp.get("/history")
def history_page():
    query = request.args.get("q", "")
    invoices = search_invoices(query)
    return render_template(
        "history.html",
        business=get_settings(),
        invoices=invoices,
        query=query,
    )


@history_bp.get("/history/<int:invoice_id>")
def view_invoice(invoice_id: int):
    invoice = get_invoice(invoice_id)
    if not invoice:
        return render_template(
            "history.html",
            business=get_settings(),
            invoices=search_invoices(""),
            query="",
            error="Invoice not found.",
        ), 404
    return render_template("preview.html", business=invoice["business"], invoice=invoice)


@history_bp.get("/api/history")
def history_api():
    query = request.args.get("q", "")
    return jsonify(search_invoices(query))
