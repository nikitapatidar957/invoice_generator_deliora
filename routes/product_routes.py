from flask import Blueprint, jsonify, render_template, request

from services.invoice_service import (
    deactivate_product,
    get_settings,
    list_products,
    save_product,
)

product_bp = Blueprint("products", __name__)


@product_bp.get("/products")
def products_page():
    return render_template(
        "products.html",
        business=get_settings(),
        products=list_products(active_only=False),
    )


@product_bp.get("/api/products")
def products_api():
    active_only = request.args.get("active") == "1"
    return jsonify(list_products(active_only=active_only))


@product_bp.post("/api/products")
def create_product():
    try:
        product = save_product(request.get_json(force=True) or {})
        return jsonify(product), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Could not save product. {exc}"}), 400


@product_bp.put("/api/products/<int:product_id>")
def update_product(product_id: int):
    try:
        product = save_product(request.get_json(force=True) or {}, product_id=product_id)
        return jsonify(product)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Could not update product. {exc}"}), 400


@product_bp.post("/api/products/<int:product_id>/deactivate")
def deactivate(product_id: int):
    deactivate_product(product_id)
    return jsonify({"ok": True})
