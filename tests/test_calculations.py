import unittest
from decimal import Decimal

from services.calculation_service import calculate_invoice, calculate_line, format_inr
from services.number_to_words import amount_in_words


class CalculationTests(unittest.TestCase):
    def test_line_without_discount(self):
        line = calculate_line(2, 1499, 0, 0, 18, "intra")
        self.assertEqual(line["gross_amount"], 2998.00)
        self.assertEqual(line["discount_amount"], 0.00)
        self.assertEqual(line["taxable_amount"], 2998.00)
        self.assertEqual(line["gst_amount"], 539.64)
        self.assertEqual(line["cgst_amount"], 269.82)
        self.assertEqual(line["sgst_amount"], 269.82)
        self.assertEqual(line["igst_amount"], 0.00)
        self.assertEqual(line["line_total"], 3537.64)

    def test_percent_and_fixed_discount(self):
        # 1 x 1499, 10% + ₹100 fixed => discount 149.90 + 100 = 249.90
        line = calculate_line(1, 1499, 10, 100, 18, "inter")
        self.assertEqual(line["discount_amount"], 249.90)
        self.assertEqual(line["taxable_amount"], 1249.10)
        self.assertEqual(line["igst_amount"], 224.84)
        self.assertEqual(line["cgst_amount"], 0.00)
        self.assertEqual(line["line_total"], 1473.94)

    def test_invoice_totals_and_partial_payment(self):
        items = [
            {"product_id": 1, "quantity": 2, "unit_price": 1499, "discount_percent": 0, "discount_fixed": 0, "gst_rate": 18},
            {"product_id": 2, "quantity": 1, "unit_price": 1499, "discount_percent": 0, "discount_fixed": 50, "gst_rate": 18},
        ]
        totals = calculate_invoice(items, "intra", "partial", 1000)
        self.assertEqual(totals["subtotal"], 4497.00)
        self.assertEqual(totals["total_discount"], 50.00)
        self.assertEqual(totals["total_taxable"], 4447.00)
        self.assertEqual(totals["grand_total"], 5247.46)
        self.assertEqual(totals["amount_paid"], 1000.00)
        self.assertEqual(totals["balance_due"], 4247.46)

    def test_duplicate_product_rejected(self):
        items = [
            {"product_id": 1, "quantity": 1, "unit_price": 1499, "gst_rate": 18},
            {"product_id": 1, "quantity": 1, "unit_price": 1499, "gst_rate": 18},
        ]
        with self.assertRaises(ValueError):
            calculate_invoice(items, "intra", "paid", 0)

    def test_amount_paid_cannot_exceed_total(self):
        items = [{"product_id": 1, "quantity": 1, "unit_price": 1499, "gst_rate": 18}]
        with self.assertRaises(ValueError):
            calculate_invoice(items, "intra", "partial", 99999)

    def test_indian_words_and_currency(self):
        self.assertEqual(amount_in_words(5310), "Rupees Five Thousand Three Hundred Ten Only")
        self.assertEqual(format_inr(5310), "₹5,310.00")
        self.assertEqual(format_inr(Decimal("124249.10")), "₹1,24,249.10")


if __name__ == "__main__":
    unittest.main()
