const products = window.DELIORA.products || [];
const business = window.DELIORA.business || {};
const GSTIN_RE = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
const UPI_RE = /^[\w.\-]{2,256}@[a-zA-Z]{2,64}$/;

const lineBody = document.getElementById("lineBody");
const template = document.getElementById("lineTemplate");
const alertBox = document.getElementById("alert");
const dateInput = document.getElementById("invoiceDate");
dateInput.value = new Date().toISOString().slice(0, 10);

function money(n) {
    return Math.round((Number(n) || 0) * 100) / 100;
}

function formatINR(n) {
    return "₹" + money(n).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

function showAlert(message, ok) {
    alertBox.textContent = message;
    alertBox.classList.remove("hidden");
    alertBox.classList.toggle("ok", Boolean(ok));
}

function hideAlert() {
    alertBox.classList.add("hidden");
}

function availableProducts(exceptSelect) {
    const used = new Set(
        [...document.querySelectorAll(".product-select")]
            .filter((el) => el !== exceptSelect)
            .map((el) => el.value)
            .filter(Boolean)
    );
    return products.filter((p) => !used.has(String(p.id)));
}

function fillProductOptions(select, keepId) {
    const available = availableProducts(select);
    const current = keepId || select.value;
    select.innerHTML = '<option value="">Select perfume</option>';
    products.forEach((p) => {
        if (available.some((a) => String(a.id) === String(p.id)) || String(p.id) === String(current)) {
            const opt = document.createElement("option");
            opt.value = p.id;
            opt.textContent = p.name;
            opt.dataset.price = p.price;
            opt.dataset.ptrPercent = p.ptr_percent || 34.36;
            opt.dataset.schemeDiscount = p.scheme_discount || 35.5;
            opt.dataset.gst = p.gst_rate;
            opt.dataset.sku = p.sku;
            opt.dataset.hsn = p.hsn_sac || "";
            select.appendChild(opt);
        }
    });
    if (current) select.value = current;
}

function addRow(prefillId) {
    if (availableProducts(null).length === 0 && lineBody.children.length) {
        showAlert("All five perfumes are already on this invoice. Increase quantity instead of adding the same bottle twice.");
        return;
    }
    const row = template.content.firstElementChild.cloneNode(true);
    const select = row.querySelector(".product-select");
    fillProductOptions(select, prefillId || "");
    row.querySelector(".price").value = "1499.00";
    row.dataset.ptrPercent = "34.36";
    row.dataset.schemeDiscount = "35.5";
    row.querySelector(".price").addEventListener("input", () => {
        row.querySelector(".price").dataset.touched = "1";
    });
    row.querySelector(".remove").addEventListener("click", () => {
        row.remove();
        refreshProductOptions();
        recalc();
    });
    ["change", "input"].forEach((evt) => {
        row.addEventListener(evt, (e) => {
            if (e.target.classList.contains("product-select")) {
                onProductChange(row, select);
            }
            recalc();
        });
    });
    lineBody.appendChild(row);
    if (prefillId) {
        select.value = String(prefillId);
        onProductChange(row, select);
    }
    refreshProductOptions();
    recalc();
}

function onProductChange(row, select) {
    const chosen = products.find((p) => String(p.id) === select.value);
    if (!chosen) return;
    const price = row.querySelector(".price");
    if (!price.dataset.touched) price.value = Number(chosen.price).toFixed(2);
    const ptrPercent = Number(chosen.ptr_percent || 34.36);
    const ptr = money(Number(chosen.price) - Number(chosen.price) * ptrPercent / 100);
    row.querySelector(".ptr").textContent = formatINR(ptr);
    row.querySelector(".hsn").textContent = chosen.hsn_sac || "";
    row.querySelector(".disc-pct").value = Number(chosen.scheme_discount || 35.5).toFixed(2);
    row.dataset.ptr = String(ptr);
    row.dataset.ptrPercent = String(ptrPercent);
    row.dataset.schemeDiscount = String(chosen.scheme_discount || 35.5);
    refreshProductOptions();
}

function refreshProductOptions() {
    document.querySelectorAll(".product-select").forEach((select) => {
        fillProductOptions(select, select.value);
    });
}

function lineCalc(row) {
    const qty = Number(row.querySelector(".qty").value);
    const price = Number(row.querySelector(".price").value);
    const pctInput = row.querySelector(".disc-pct");
    const pct = Number(pctInput.value) || 0;
    const fixed = 0;
    const gst = 18;
    const ptr = Number(row.dataset.ptr || 984);
    const gross = money(qty * ptr);
    const discount = money(gross * pct / 100 + fixed);
    const netAmount = money(Math.max(gross - discount, 0));
    const taxable = netAmount;
    const gstAmt = money(taxable * gst / 100);
    const total = money(taxable + gstAmt);
    row.querySelector(".taxable").textContent = formatINR(taxable);
    const select = row.querySelector(".product-select");
    const opt = select.selectedOptions[0];
    return {
        product_id: Number(select.value),
        product_name: opt ? opt.textContent : "",
        sku: opt ? opt.dataset.sku : "",
        hsn_sac: opt ? opt.dataset.hsn : "",
        quantity: qty,
        unit_price: price,
        ptr,
        discount_percent: pct,
        discount_fixed: fixed,
        discount_amount: discount,
        gst_rate: gst,
        taxable_amount: taxable,
        gst_amount: gstAmt,
        line_total: total,
        valid: select.value && qty > 0 && price >= 0 && discount <= gross,
    };
}

function toWords(amount) {
    const ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"];
    const tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];
    function two(n) { return n < 20 ? ones[n] : (tens[Math.floor(n / 10)] + (n % 10 ? " " + ones[n % 10] : "")).trim(); }
    function three(n) {
        const h = Math.floor(n / 100);
        const r = n % 100;
        return [h ? ones[h] + " Hundred" : "", r ? two(r) : ""].filter(Boolean).join(" ");
    }
    function intWords(n) {
        if (n === 0) return "Zero";
        const crore = Math.floor(n / 10000000); n %= 10000000;
        const lakh = Math.floor(n / 100000); n %= 100000;
        const thousand = Math.floor(n / 1000); const rest = n % 1000;
        return [
            crore ? intWords(crore) + " Crore" : "",
            lakh ? (lakh < 100 ? two(lakh) : three(lakh)) + " Lakh" : "",
            thousand ? (thousand < 100 ? two(thousand) : three(thousand)) + " Thousand" : "",
            rest ? three(rest) : "",
        ].filter(Boolean).join(" ");
    }
    const rupees = Math.floor(amount + 1e-9);
    const paise = Math.round((amount - rupees) * 100);
    let words = "Rupees " + intWords(rupees);
    if (paise) words += " and " + two(paise) + " Paise";
    return words + " Only";
}

function collectState() {
    const items = [...lineBody.querySelectorAll(".line-row")].map(lineCalc);
    const duePaymentOnly = document.getElementById("transactionType").value === "due_payment";
    const taxType = document.getElementById("taxType").value;
    const status = document.getElementById("paymentStatus").value;
    const method = document.getElementById("paymentMethod").value;
    const validItems = items.filter((i) => i.product_id);
    const subtotal = money(validItems.reduce((s, i) => s + i.quantity * i.ptr, 0));
    const totalDiscount = money(validItems.reduce((s, i) => s + i.discount_amount, 0));
    const totalTaxable = money(validItems.reduce((s, i) => s + i.taxable_amount, 0));
    const totalGst = money(validItems.reduce((s, i) => s + i.gst_amount, 0));
    const grand = money(totalTaxable + totalGst);
    const cgst = taxType === "intra" ? money(totalGst / 2) : 0;
    const sgst = taxType === "intra" ? money(totalGst - cgst) : 0;
    const igst = taxType === "inter" ? totalGst : 0;
    let paid = money(document.getElementById("amountPaid").value);
    const previousDue = money(document.getElementById("previousDue").value);
    if (status === "paid") paid = duePaymentOnly ? previousDue : grand;
    if (status === "unpaid") paid = 0;
    return {
        customer_name: document.getElementById("customerName").value.trim(),
        customer_phone: document.getElementById("customerPhone").value.trim(),
        customer_email: document.getElementById("customerEmail").value.trim(),
        customer_address: document.getElementById("customerAddress").value.trim(),
        customer_gstin: document.getElementById("customerGstin").value.trim().toUpperCase(),
        invoice_date: dateInput.value,
        tax_type: taxType,
        payment_method: method,
        payment_status: status,
        customer_upi_id: document.getElementById("upiId").value.trim(),
        transaction_reference: document.getElementById("txnRef").value.trim(),
        due_payment_only: duePaymentOnly,
        amount_paid: paid,
        previous_due: previousDue,
        current_balance_due: money(grand - paid),
        balance_due: money(previousDue + (grand - paid)),
        items: validItems,
        subtotal,
        total_discount: totalDiscount,
        total_taxable: totalTaxable,
        total_gst: totalGst,
        total_cgst: cgst,
        total_sgst: sgst,
        total_igst: igst,
        grand_total: grand,
        amount_in_words: toWords(grand),
        invoice_number: document.getElementById("invoiceNumber").textContent,
        footer_enabled: document.getElementById("footerEnabled").checked,
        footer_text: document.getElementById("footerText").value.trim(),
        tagline: document.getElementById("taglineText").value.trim(),
        terms_enabled: document.getElementById("termsEnabled").checked,
        terms_text: document.getElementById("termsText").value.trim(),
        gst_inclusive: true,
    };
}

function togglePaymentFields() {
    const method = document.getElementById("paymentMethod").value;
    const status = document.getElementById("paymentStatus").value;
    const duePaymentOnly = document.getElementById("transactionType").value === "due_payment";
    document.getElementById("productSection").classList.toggle("hidden", duePaymentOnly);
    document.getElementById("upiField").classList.toggle("hidden", method !== "upi");
    document.getElementById("refField").classList.toggle("hidden", !["upi", "bank", "card"].includes(method));
    document.getElementById("paidField").classList.toggle("hidden", status !== "partial" && !duePaymentOnly);
    document.querySelector("#paidField").childNodes[0].textContent = duePaymentOnly ? "Payment Received" : "Amount Paid";
    const intra = document.getElementById("taxType").value === "intra";
    document.getElementById("cgstRow").classList.toggle("hidden", !intra);
    document.getElementById("sgstRow").classList.toggle("hidden", !intra);
    document.getElementById("igstRow").classList.toggle("hidden", intra);
}

function renderPreview(state) {
    const b = business;
    const gstin = state.customer_gstin || "Unregistered / Consumer";
    const taxRows = state.tax_type === "intra"
        ? `<p>CGST (9%) ${formatINR(state.total_cgst)}</p><p>SGST (9%) ${formatINR(state.total_sgst)}</p>`
        : `<p>IGST ${formatINR(state.total_igst)}</p>`;
    const itemRows = state.items.map((item, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${item.product_name}</td>
            <td>${item.quantity}</td>
            <td>${formatINR(item.unit_price)}</td>
            <td>${item.hsn_sac}</td>
            <td>${formatINR(item.unit_price)}/PCS</td>
            <td>${item.quantity} PCS</td>
            <td>${formatINR(item.ptr)}/PCS</td>
            <td>PCS</td>
            <td>${item.discount_percent.toFixed(2)}%</td>
            <td>${formatINR(item.taxable_amount)}</td>
        </tr>
    `).join("") || `<tr><td colspan="9" class="empty">Select perfumes to preview the invoice.</td></tr>`;
    const extra = [
        state.customer_upi_id ? `UPI: ${state.customer_upi_id}` : "",
        state.transaction_reference ? `Ref: ${state.transaction_reference}` : "",
    ].filter(Boolean).join(" · ");
    document.getElementById("previewSheet").innerHTML = `
        <header class="sheet-head">
            <img src="/static/images/deliora-logo.png" alt="Rudhi Cosmetics">
            <div>
                <h2>${b.business_name || "Rudhi Cosmetics"}</h2>
                <p>${b.address || ""}</p>
                <p>${b.phone || ""} · ${b.email || ""} · ${b.website || ""}</p>
                <p>GSTIN: ${b.gstin || "23EOUPP3879A1ZI"} · ${(b.state || "").trim()} (${b.state_code || ""})</p>
            </div>
            <div class="sheet-title">
                <strong>INVOICE</strong>
                <p>${state.invoice_number}</p>
                <p>${state.invoice_date.split("-").reverse().join("/")}</p>
            </div>
        </header>
        <section class="sheet-grid">
            <div>
                <h3>Bill To</h3>
                <p><strong>${state.customer_name || "Customer name"}</strong></p>
                ${state.customer_gstin ? `<p>GSTIN: ${state.customer_gstin}</p>` : ""}
                <p>${state.customer_phone}</p>
                <p>${state.customer_email}</p>
                <p>${state.customer_address}</p>
            </div>
            <div>
                <h3>Payment</h3>
                <p>Method: ${state.payment_method}</p>
                <p>Status: ${state.payment_status}</p>
                <p>Previous Due: ${formatINR(state.previous_due)}</p>
                <p>${extra}</p>
                <p>Tax: ${state.tax_type === "intra" ? "Intra-State (CGST 9%/SGST 9%)" : "Inter-State (IGST)"}</p>
            </div>
        </section>
        <div class="sheet-items-scroll">
            <table class="sheet-items">
                <thead>
                    <tr>
                        <th>Sl. No.</th><th>Product</th><th>HSN/SAC</th><th>MRP/Marginal</th>
                        <th>Quantity</th><th>PTR/Rate</th><th>Per</th><th>Scheme Disc. %</th><th>Amount</th>
                    </tr>
                </thead>
                <tbody>${itemRows}</tbody>
            </table>
        </div>
        <section class="sheet-bottom">
            <div>
                <h3>Tax Summary</h3>
                ${taxRows}
                <p class="words">Amount in words: ${state.amount_in_words}</p>
            </div>
            <div class="sheet-totals">
                <p><span>Subtotal</span><strong>${formatINR(state.subtotal)}</strong></p>
                <p><span>Round-off</span><strong>${formatINR(0)}</strong></p>
                <p><span>Taxable Amount</span><strong>${formatINR(state.total_taxable)}</strong></p>
                <p><span>GST (18%)</span><strong>${formatINR(state.total_gst)}</strong></p>
                <p class="grand"><span>GRAND TOTAL</span><strong>${formatINR(state.grand_total)}</strong></p>
                <p><span>Previous Due</span><strong>${formatINR(state.previous_due)}</strong></p>
                <p><span>Amount Paid</span><strong>${formatINR(state.amount_paid)}</strong></p>
                <p><span>Balance Due</span><strong>${formatINR(state.balance_due)}</strong></p>
            </div>
        </section>
        ${state.footer_enabled ? `<footer class="sheet-foot">
            <p>${state.footer_text}</p>
            <p class="tagline">${state.tagline}</p>
            ${state.terms_enabled ? `<h4>Terms &amp; Conditions</h4><p>${state.terms_text}</p>` : ""}
        </footer>` : ""}
    `;
}

function recalc() {
    togglePaymentFields();
    const state = collectState();
    document.getElementById("tSubtotal").textContent = formatINR(state.subtotal);
    document.getElementById("tTaxable").textContent = formatINR(state.total_taxable);
    document.getElementById("tCgst").textContent = formatINR(state.total_cgst);
    document.getElementById("tSgst").textContent = formatINR(state.total_sgst);
    document.getElementById("tIgst").textContent = formatINR(state.total_igst);
    document.getElementById("tGst").textContent = formatINR(state.total_gst);
    document.getElementById("tGrand").textContent = formatINR(state.grand_total);
    document.getElementById("tPreviousDue").textContent = formatINR(state.previous_due);
    document.getElementById("tPaid").textContent = formatINR(state.amount_paid);
    document.getElementById("tBalance").textContent = formatINR(state.balance_due);
    renderPreview(state);
    return state;
}

function validate(state, { requireCustomer } = { requireCustomer: true }) {
    if (requireCustomer && !state.customer_name) return "Customer name is required.";
    if (state.customer_gstin && !GSTIN_RE.test(state.customer_gstin)) {
        return "Customer GSTIN format looks invalid. Leave it blank for a regular consumer.";
    }
    if (!state.items.length && !state.due_payment_only) return "Add at least one perfume.";
    for (const item of state.items) {
        if (item.quantity <= 0) return "Quantity must be greater than zero.";
        if (item.unit_price < 0) return "Unit price cannot be negative.";
        if (item.discount_amount > money(item.quantity * item.unit_price)) {
            return "Discount cannot exceed the line amount.";
        }
    }
    const ids = state.items.map((i) => i.product_id);
    if (new Set(ids).size !== ids.length) return "The same perfume cannot appear twice. Increase quantity instead.";
    if (state.payment_method === "upi") {
        if (!state.customer_upi_id) return "Enter the customer UPI ID.";
        if (!UPI_RE.test(state.customer_upi_id)) return "UPI ID format looks invalid. Example: nikita@upi";
    }
    if (state.due_payment_only && state.previous_due <= 0) {
        return "Enter the outstanding balance before collecting a due payment.";
    }
    if (state.payment_status === "partial" || state.due_payment_only) {
        const typed = Number(document.getElementById("amountPaid").value);
        if (typed < 0) return "Amount paid cannot be negative.";
        const maximum = state.due_payment_only ? state.previous_due : state.grand_total;
        if (typed > maximum) return "Payment cannot be greater than the amount due.";
        if (typed === 0) return "Enter the payment amount.";
    }
    if (state.previous_due < 0) return "Previous due cannot be negative.";
    return null;
}

async function saveInvoice(download) {
    hideAlert();
    const state = recalc();
    const error = validate(state);
    if (error) {
        showAlert(error);
        return;
    }
    const response = await fetch("/api/invoices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state),
    });
    const data = await response.json();
    if (!response.ok) {
        showAlert(data.error || "Could not save invoice.");
        return;
    }
    showAlert("Invoice " + data.invoice_number + " saved.", true);
    document.getElementById("invoiceNumber").textContent = data.invoice_number;
    if (download) {
        window.location.href = "/invoices/" + data.id + "/pdf";
    }
    const next = await fetch("/api/next-invoice-number").then((r) => r.json());
    setTimeout(() => {
        document.getElementById("invoiceNumber").textContent = next.invoice_number;
    }, download ? 1500 : 0);
}

document.getElementById("addProduct").addEventListener("click", () => addRow());
document.getElementById("invoiceForm").addEventListener("submit", (e) => {
    e.preventDefault();
    saveInvoice(true);
});
document.getElementById("saveOnly").addEventListener("click", () => saveInvoice(false));
document.getElementById("invoiceForm").addEventListener("input", recalc);
document.getElementById("invoiceForm").addEventListener("change", recalc);
document.querySelectorAll(".price").forEach((el) => {
    el.addEventListener("input", () => { el.dataset.touched = "1"; });
});

addRow();
recalc();
