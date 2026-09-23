ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]

TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety",
]


def _two_digits(n: int) -> str:
    if n < 20:
        return ONES[n]
    return (TENS[n // 10] + (" " + ONES[n % 10] if n % 10 else "")).strip()


def _three_digits(n: int) -> str:
    hundred = n // 100
    rest = n % 100
    parts = []
    if hundred:
        parts.append(f"{ONES[hundred]} Hundred")
    if rest:
        parts.append(_two_digits(rest))
    return " ".join(parts)


def _integer_to_words(n: int) -> str:
    if n == 0:
        return "Zero"

    crore = n // 10000000
    n %= 10000000
    lakh = n // 100000
    n %= 100000
    thousand = n // 1000
    rest = n % 1000

    parts = []
    if crore:
        parts.append(f"{_integer_to_words(crore)} Crore")
    if lakh:
        parts.append(f"{_three_digits(lakh) or _two_digits(lakh)} Lakh")
    if thousand:
        parts.append(f"{_three_digits(thousand) or _two_digits(thousand)} Thousand")
    if rest:
        parts.append(_three_digits(rest))
    return " ".join(part for part in parts if part)


def amount_in_words(amount) -> str:
    from decimal import Decimal

    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    rupees = int(value)
    paise = int((value - rupees) * 100)

    words = f"Rupees {_integer_to_words(rupees)}"
    if paise:
        words += f" and {_two_digits(paise)} Paise"
    return f"{words} Only"
