from fastapi import APIRouter
from pydantic import BaseModel

from app.database import get_db
from app.services.rabattcode_service import pruefe_rabattcode

router = APIRouter()


class RabattcodeRequest(BaseModel):
    code: str
    email: str
    subtotal: float


@router.post("/api/rabattcode/pruefen")
def rabattcode_pruefen(req: RabattcodeRequest):
    conn = get_db()
    try:
        result = pruefe_rabattcode(conn, req.code, req.email, req.subtotal)
        if result["gueltig"]:
            if result["rabattart"] == "prozent":
                beschreibung = f"{result['rabattwert']:.0f}% Rabatt"
            else:
                beschreibung = f"CHF {result['rabattbetrag']:.2f} Rabatt"
            return {
                "gueltig": True,
                "rabattbetrag": result["rabattbetrag"],
                "rabattart": result["rabattart"],
                "beschreibung": beschreibung,
                "code": result["code"],
            }
        return {"gueltig": False, "fehler": result["fehler"]}
    finally:
        conn.close()
