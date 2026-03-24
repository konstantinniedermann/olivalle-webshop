from io import StringIO

from qrbill import QRBill

from app.config import settings


def generiere_qr_rechnung(
    betrag: float,
    bestell_id: int,
    kunde_name: str,
    kunde_adresse: str,
    kunde_plz: str,
    kunde_ort: str,
) -> bytes:
    bill = QRBill(
        account=settings.qr_iban,
        creditor={
            "name": settings.qr_name,
            "street": settings.qr_address,
            "pcode": settings.qr_zip,
            "city": settings.qr_city,
            "country": "CH",
        },
        debtor={
            "name": kunde_name,
            "street": kunde_adresse,
            "pcode": kunde_plz,
            "city": kunde_ort,
            "country": "CH",
        },
        amount=f"{betrag:.2f}",
        currency="CHF",
        additional_information=f"Bestellung #{bestell_id}",
    )
    buffer = StringIO()
    bill.as_svg(buffer)
    return buffer.getvalue().encode("utf-8")
