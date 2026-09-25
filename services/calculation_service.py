from decimal import Decimal, ROUND_HALF_UP

TWOPLACES = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def format_inr(value) -> str:
    amount = money(value)
    negative = amount < 0
    amount = abs(amount)
    whole, frac = f"{amount:.2f}".split(".")
    last_three = whole[-3:]
    rest = whole[:-3]
    if rest:
        groups = []
        while rest:
            groups.append(rest[-2:])
            rest = rest[:-2]
        formatted = ",".join(reversed(groups)) + "," + last_three
    else:
        formatted = last_three
    sign = "-" if negative else ""
    return f"{sign}₹{formatted}.{frac}"


def calculate_line(
    quantity,
    unit_price,
    discount_percent,
    discount_fixed,
    gst_rate,
    tax_type,
    inclusive_gst=False,
    calculation_price=None,
) -> dict:
    qty = Decimal(str(quantity))
    price = money(unit_price)
    percent = Decimal(str(discount_percent or 0))
    fixed = money(discount_fixed or 0)
    rate = Decimal(str(gst_rate or 0))

    if qty <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if price < 0:
        raise ValueError("Unit price cannot be negative.")
    if percent < 0:
        raise ValueError("Discount percent cannot be negative.")
    if fixed < 0:
        raise ValueError("Fixed discount cannot be negative.")
    if rate < 0:
        raise ValueError("GST rate cannot be negative.")

    base_price = money(calculation_price if calculation_price is not None else price)
    gross = money(qty * base_price)
    percent_discount = money(gross * percent / Decimal("100"))
    discount_amount = money(percent_discount + fixed)
    if discount_amount > gross:
        raise ValueError("Discount cannot be greater than the line amount.")

    net_amount = money(gross - discount_amount)
    taxable = net_amount
    gst_amount = money(taxable * rate / Decimal("100"))
    line_total = money(taxable + gst_amount)

    cgst = sgst = igst = money(0)
    if tax_type == "intra":
        cgst = money(gst_amount / Decimal("2"))
        sgst = money(gst_amount - cgst)
    elif tax_type == "inter":
        igst = gst_amount
    else:
        raise ValueError("Tax type must be intra-state or inter-state.")

    return {
        "quantity": int(qty),
        "unit_price": float(price),
        "discount_percent": float(percent),
        "discount_fixed": float(fixed),
        "discount_amount": float(discount_amount),
        "gst_rate": float(rate),
        "gross_amount": float(gross),
        "taxable_amount": float(taxable),
        "gst_amount": float(gst_amount),
        "cgst_amount": float(cgst),
        "sgst_amount": float(sgst),
        "igst_amount": float(igst),
        "line_total": float(line_total),
    }


def calculate_invoice(
    items: list[dict],
    tax_type: str,
    payment_status: str,
    amount_paid,
    previous_due=0,
    due_payment_only=False,
    inclusive_gst=False,
) -> dict:
    if not items and not due_payment_only:
        raise ValueError("Add at least one perfume to the invoice.")
    if due_payment_only and money(previous_due or 0) <= 0:
        raise ValueError("Enter the outstanding balance being collected.")

    seen = set()
    calculated_items = []
    for item in items:
        product_id = item.get("product_id")
        if product_id in seen:
            raise ValueError("The same perfume was added twice. Merge the quantity instead.")
        seen.add(product_id)
        calculated_items.append({**item, **calculate_line(
            item["quantity"],
            item["unit_price"],
            item.get("discount_percent", 0),
            item.get("discount_fixed", 0),
            item["gst_rate"],
            tax_type,
            inclusive_gst,
            item.get("ptr"),
        )})

    subtotal = money(sum(Decimal(str(i["gross_amount"])) for i in calculated_items))
    total_quantity = sum(i["quantity"] for i in calculated_items)
    total_discount = money(sum(Decimal(str(i["discount_amount"])) for i in calculated_items))
    total_taxable = money(sum(Decimal(str(i["taxable_amount"])) for i in calculated_items))
    total_gst = money(sum(Decimal(str(i["gst_amount"])) for i in calculated_items))
    total_cgst = money(sum(Decimal(str(i["cgst_amount"])) for i in calculated_items))
    total_sgst = money(sum(Decimal(str(i["sgst_amount"])) for i in calculated_items))
    total_igst = money(sum(Decimal(str(i["igst_amount"])) for i in calculated_items))
    grand_total = money(total_taxable + total_gst)

    previous = money(previous_due or 0)
    if previous < 0:
        raise ValueError("Previous due cannot be negative.")

    paid = money(amount_paid or 0)
    if paid < 0:
        raise ValueError("Amount paid cannot be negative.")

    status = (payment_status or "").lower()
    payment_base = previous if due_payment_only else grand_total
    if status == "paid":
        paid = payment_base
    elif status == "unpaid":
        paid = money(0)
    elif status == "partial":
        if paid == 0:
            raise ValueError("Enter the amount paid for a partially paid invoice.")
        if paid > payment_base:
            raise ValueError("Amount paid cannot be greater than the amount due.")
        if paid == payment_base:
            status = "paid"
    else:
        raise ValueError("Select a valid payment status.")

    current_balance = money(grand_total - paid) if not due_payment_only else money(0)
    balance = money(previous - paid) if due_payment_only else money(previous + current_balance)

    return {
        "items": calculated_items,
        "subtotal": float(subtotal),
        "total_quantity": total_quantity,
        "total_discount": float(total_discount),
        "total_taxable": float(total_taxable),
        "total_gst": float(total_gst),
        "total_cgst": float(total_cgst),
        "total_sgst": float(total_sgst),
        "total_igst": float(total_igst),
        "grand_total": float(grand_total),
        "payment_status": status,
        "amount_paid": float(paid),
        "previous_due": float(previous),
        "current_balance_due": float(current_balance),
        "balance_due": float(balance),
        "tax_type": tax_type,
        "due_payment_only": bool(due_payment_only),
    }
