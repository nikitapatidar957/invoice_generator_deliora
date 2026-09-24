import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BUSINESS_CONFIG = {
    "business_name": os.getenv("BUSINESS_NAME", "DeLiora Essence by Patidar"),
    "brand_name": os.getenv("BRAND_NAME", "DeLiora Essence by Patidar"),
    "address": os.getenv("BUSINESS_ADDRESS", "[Business Address — configure in .env]"),
    "gstin": os.getenv("BUSINESS_GSTIN", "[GSTIN — configure in .env]"),
    "phone": os.getenv("BUSINESS_PHONE", "[Phone — configure in .env]"),
    "email": os.getenv("BUSINESS_EMAIL", "[Email — configure in .env]"),
    "website": os.getenv("BUSINESS_WEBSITE", "[Website — configure in .env]"),
    "state": os.getenv("BUSINESS_STATE", "[State — configure in .env]"),
    "state_code": os.getenv("BUSINESS_STATE_CODE", "[State Code — configure in .env]"),
    "logo": os.getenv("LOGO_PATH", "static/images/deliora-logo.png"),
}

TERMS_AND_CONDITIONS = os.getenv(
    "TERMS_AND_CONDITIONS",
    "Goods once sold cannot be returned unless damaged in transit. "
    "GST rates and HSN codes should be verified before production use. "
    "This invoice records payment details only and does not process online payments.",
)

INVOICE_FOOTER_THANK_YOU = os.getenv(
    "INVOICE_FOOTER_THANK_YOU",
    "Thank you for choosing DeLiora Essence by Patidar.",
)

INVOICE_TAGLINE = os.getenv("INVOICE_TAGLINE", "A scent that lingers.")

# Placeholder default — each product stores its own rate in MongoDB Atlas.
DEFAULT_GST_RATE = float(os.getenv("DEFAULT_GST_RATE", "18"))
DEFAULT_PRODUCT_PRICE = float(os.getenv("DEFAULT_PRODUCT_PRICE", "1499"))
DEFAULT_HSN = os.getenv("DEFAULT_HSN", "3303")
DEFAULT_SIZE = os.getenv("DEFAULT_SIZE", "100 ml")

INVOICE_PREFIX = os.getenv("INVOICE_PREFIX", "DEL")
SECRET_KEY = os.getenv("SECRET_KEY", "deliora-offline-dev-key")

LOGO_ABS_PATH = BASE_DIR / BUSINESS_CONFIG["logo"]
