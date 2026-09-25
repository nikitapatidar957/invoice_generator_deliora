const alertBox = document.getElementById("alert");

function showAlert(message, ok) {
    alertBox.textContent = message;
    alertBox.classList.remove("hidden");
    alertBox.classList.toggle("ok", Boolean(ok));
}

function rowPayload(row) {
    return {
        name: row.querySelector(".name").value.trim(),
        sku: row.querySelector(".sku").value.trim(),
        size: row.querySelector(".size").value.trim(),
        price: row.querySelector(".price").value,
        ptr: row.querySelector(".ptr").value,
        ptr_percent: row.querySelector(".ptr-percent").value,
        gst_rate: row.querySelector(".gst").value,
        scheme_discount: row.querySelector(".scheme-discount").value,
        hsn_sac: row.querySelector(".hsn").value.trim(),
        available_quantity: row.querySelector(".qty").value,
        is_active: true,
    };
}

function updatePtrFromPercent(row) {
    const mrp = Number(row.querySelector(".price").value) || 0;
    const percent = Number(row.querySelector(".ptr-percent").value) || 0;
    row.querySelector(".ptr").value = (mrp - mrp * percent / 100).toFixed(2);
}

function updatePercentFromPtr(row) {
    const mrp = Number(row.querySelector(".price").value) || 0;
    const ptr = Number(row.querySelector(".ptr").value) || 0;
    row.querySelector(".ptr-percent").value = mrp ? ((mrp - ptr) / mrp * 100).toFixed(2) : "0.00";
}

document.querySelectorAll("#productTable tr[data-id]").forEach((row) => {
    row.querySelector(".price").addEventListener("input", () => updatePtrFromPercent(row));
    row.querySelector(".ptr-percent").addEventListener("input", () => updatePtrFromPercent(row));
    row.querySelector(".ptr").addEventListener("input", () => updatePercentFromPtr(row));
});

document.getElementById("productTable").addEventListener("click", async (event) => {
    const row = event.target.closest("tr");
    if (!row) return;
    const id = row.dataset.id;
    try {
        if (event.target.classList.contains("save")) {
            const response = await fetch("/api/products/" + id, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(rowPayload(row)),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Save failed");
            showAlert(data.name + " updated.", true);
        }
        if (event.target.classList.contains("deactivate")) {
            const response = await fetch("/api/products/" + id + "/deactivate", { method: "POST" });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Could not deactivate");
            showAlert("Product deactivated. Historical invoices are unchanged.", true);
            setTimeout(() => location.reload(), 600);
        }
    } catch (err) {
        showAlert(err.message);
    }
});

document.getElementById("newProduct").addEventListener("click", async () => {
    const name = prompt("Perfume name");
    if (!name) return;
    const sku = prompt("SKU", "DEL-" + name.toUpperCase().replace(/\s+/g, "-"));
    if (!sku) return;
    try {
        const response = await fetch("/api/products", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name,
                sku,
                size: "100 ml",
                price: 1499,
                ptr_percent: 34.36,
                gst_rate: 18,
                scheme_discount: 35.5,
                hsn_sac: "3303",
                available_quantity: 0,
            }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Could not add product");
        location.reload();
    } catch (err) {
        showAlert(err.message);
    }
});
