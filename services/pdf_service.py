from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import BASE_DIR, INVOICES_DIR, LOGO_ABS_PATH
from services.calculation_service import format_inr
from services.invoice_service import get_invoice, set_invoice_pdf_path

BURGUNDY = colors.HexColor("#2B0F12")
GOLD = colors.HexColor("#B8924A")
CREAM = colors.HexColor("#F6F1E8")
BROWN = colors.HexColor("#211817")
LINE = colors.HexColor("#D9CDB8")


def generate_invoice_pdf(invoice_id: int) -> Path:
    invoice = get_invoice(invoice_id)
    if not invoice:
        raise ValueError("Invoice not found.")

    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = INVOICES_DIR / f"{invoice['invoice_number']}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=invoice["invoice_number"],
        author=invoice["business"].get("business_name", "DeLiora"),
    )

    styles = getSampleStyleSheet()
    brand = ParagraphStyle(
        "Brand",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=16,
        textColor=BURGUNDY,
        alignment=TA_LEFT,
        leading=20,
    )
    muted = ParagraphStyle(
        "Muted",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=8.5,
        textColor=BROWN,
        leading=12,
    )
    heading = ParagraphStyle(
        "InvHead",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=14,
        textColor=GOLD,
        alignment=TA_RIGHT,
        leading=18,
    )
    small_bold = ParagraphStyle(
        "SmallBold",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=9,
        textColor=BURGUNDY,
        leading=12,
    )
    small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=8.5,
        textColor=BROWN,
        leading=11,
    )
    center_small = ParagraphStyle(
        "CenterSmall",
        parent=small,
        alignment=TA_CENTER,
        fontName="Times-Italic",
        textColor=GOLD,
    )
    right = ParagraphStyle("Right", parent=small, alignment=TA_RIGHT)
    right_bold = ParagraphStyle("RightBold", parent=small_bold, alignment=TA_RIGHT)
    white_head = ParagraphStyle(
        "WhiteHead",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=9,
        textColor=colors.white,
        leading=12,
    )

    business = invoice["business"]
    story = []

    logo_cell = ""
    logo_file = Path(LOGO_ABS_PATH)
    if not logo_file.exists():
        logo_file = BASE_DIR / business.get("logo", "static/images/deliora-logo.png")
    if logo_file.exists():
        logo_cell = Image(str(logo_file), width=28 * mm, height=28 * mm)

    seller_lines = [
        Paragraph(business.get("business_name", "DeLiora Essence by Patidar"), brand),
        Paragraph(business.get("address", ""), muted),
        Paragraph(
            f"GSTIN: {business.get('gstin', '')} &nbsp;&nbsp; State: {business.get('state', '')} "
            f"({business.get('state_code', '')})",
            muted,
        ),
        Paragraph(
            f"Phone: {business.get('phone', '')} &nbsp;&nbsp; Email: {business.get('email', '')}",
            muted,
        ),
        Paragraph(f"Website: {business.get('website', '')}", muted),
    ]
    header = Table(
        [[logo_cell, seller_lines, Paragraph("TAX INVOICE", heading)]],
        colWidths=[32 * mm, 105 * mm, 45 * mm],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), CREAM),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 6 * mm))

    gstin_line = invoice["customer_gstin"] or "Unregistered / Consumer"
    invoice_dt = _format_date(invoice["invoice_date"])
    meta = Table(
        [
            [
                Paragraph("Bill To", white_head),
                Paragraph("Invoice Details", white_head),
            ],
            [
                Paragraph(
                    f"<b>{invoice['customer_name']}</b><br/>"
                    f"{invoice['customer_phone']}<br/>"
                    f"{invoice['customer_email']}<br/>"
                    f"{invoice['customer_address']}<br/>"
                    f"GSTIN: {gstin_line}",
                    small,
                ),
                Paragraph(
                    f"Invoice No: <b>{invoice['invoice_number']}</b><br/>"
                    f"Invoice Date: {invoice_dt}<br/>"
                    f"Tax Type: {_tax_label(invoice['tax_type'])}<br/>"
                    f"Payment: {_payment_label(invoice['payment_method'])}<br/>"
                    f"Status: {invoice['payment_status'].replace('partial', 'Partially Paid').title()}",
                    small,
                ),
            ],
        ],
        colWidths=[91 * mm, 91 * mm],
    )
    meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BURGUNDY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    # Header cells need white text - Paragraphs have their own color. Rebuild header labels.
    story.append(meta)
    story.append(Spacer(1, 5 * mm))

    table_header = [
        Paragraph("Sr.", small_bold),
        Paragraph("Product", small_bold),
        Paragraph("SKU", small_bold),
        Paragraph("Qty", small_bold),
        Paragraph("Rate", small_bold),
        Paragraph("Discount", small_bold),
        Paragraph("Taxable", small_bold),
        Paragraph("GST", small_bold),
        Paragraph("Total", small_bold),
    ]
    rows = [table_header]
    for idx, item in enumerate(invoice["items"], start=1):
        gst_cell = f"{item['gst_rate']:.0f}% {format_inr(item['gst_amount'])}"
        rows.append(
            [
                Paragraph(str(idx), small),
                Paragraph(item["product_name"], small),
                Paragraph(item["sku"], small),
                Paragraph(str(item["quantity"]), small),
                Paragraph(format_inr(item["unit_price"]), small),
                Paragraph(format_inr(item["discount_amount"]), small),
                Paragraph(format_inr(item["taxable_amount"]), small),
                Paragraph(gst_cell, small),
                Paragraph(format_inr(item["line_total"]), small),
            ]
        )

    items_table = Table(
        rows,
        colWidths=[10 * mm, 32 * mm, 26 * mm, 12 * mm, 20 * mm, 20 * mm, 22 * mm, 22 * mm, 18 * mm],
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), CREAM),
                ("BOX", (0, 0), (-1, -1), 0.4, GOLD),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 5 * mm))

    tax_rows = [[Paragraph("Tax Summary", small_bold), Paragraph("", small)]]
    if invoice["tax_type"] == "intra":
        tax_rows += [
            [Paragraph("CGST", small), Paragraph(format_inr(invoice["total_cgst"]), right)],
            [Paragraph("SGST", small), Paragraph(format_inr(invoice["total_sgst"]), right)],
        ]
    else:
        tax_rows.append(
            [Paragraph("IGST", small), Paragraph(format_inr(invoice["total_igst"]), right)]
        )

    totals_rows = [
        [Paragraph("Subtotal", small), Paragraph(format_inr(invoice["subtotal"]), right)],
        [Paragraph("Discount", small), Paragraph(format_inr(invoice["total_discount"]), right)],
        [Paragraph("Taxable Amount", small), Paragraph(format_inr(invoice["total_taxable"]), right)],
        [Paragraph("GST", small), Paragraph(format_inr(invoice["total_gst"]), right)],
        [Paragraph("GRAND TOTAL", small_bold), Paragraph(format_inr(invoice["grand_total"]), right_bold)],
        [Paragraph("Amount Paid", small), Paragraph(format_inr(invoice["amount_paid"]), right)],
        [Paragraph("Balance Due", small_bold), Paragraph(format_inr(invoice["balance_due"]), right_bold)],
    ]

    bottom = Table(
        [[Table(tax_rows, colWidths=[40 * mm, 40 * mm]), Table(totals_rows, colWidths=[45 * mm, 40 * mm])]],
        colWidths=[91 * mm, 91 * mm],
    )
    bottom.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(bottom)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(f"Amount in words: <b>{invoice['amount_in_words']}</b>", small))

    extra = []
    if invoice["customer_upi_id"]:
        extra.append(f"UPI ID: {invoice['customer_upi_id']}")
    if invoice["transaction_reference"]:
        extra.append(f"Transaction / Reference: {invoice['transaction_reference']}")
    if extra:
        story.append(Paragraph(" &nbsp;|&nbsp; ".join(extra), small))

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(business.get("footer_thank_you", ""), center_small))
    story.append(Paragraph(business.get("tagline", "A scent that lingers."), center_small))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Terms &amp; Conditions", small_bold))
    story.append(Paragraph(business.get("terms", ""), small))

    def _footer(canvas, _doc):
        canvas.saveState()
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(1)
        canvas.line(14 * mm, 10 * mm, A4[0] - 14 * mm, 10 * mm)
        canvas.setFont("Times-Italic", 8)
        canvas.setFillColor(BURGUNDY)
        canvas.drawString(14 * mm, 6 * mm, "DeLiora Essence by Patidar")
        canvas.drawRightString(A4[0] - 14 * mm, 6 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    set_invoice_pdf_path(invoice_id, str(pdf_path.relative_to(BASE_DIR)))
    return pdf_path


def _format_date(value: str) -> str:
    try:
        return datetime_from_iso(value).strftime("%d/%m/%Y")
    except Exception:
        return value


def datetime_from_iso(value: str):
    from datetime import datetime

    return datetime.strptime(value[:10], "%Y-%m-%d")


def _tax_label(tax_type: str) -> str:
    return "Intra-State (CGST/SGST)" if tax_type == "intra" else "Inter-State (IGST)"


def _payment_label(method: str) -> str:
    return {
        "cash": "Cash",
        "upi": "UPI",
        "bank": "Bank Transfer",
        "card": "Card",
        "other": "Other",
    }.get(method, method)
