from io import BytesIO, StringIO

from fpdf import FPDF
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
    svg_buffer = StringIO()
    bill.as_svg(svg_buffer, full_page=True)

    pdf = FPDF()
    pdf.add_page()
    pdf.image(BytesIO(svg_buffer.getvalue().encode("utf-8")), x=0, y=0, w=210)
    return bytes(pdf.output())
