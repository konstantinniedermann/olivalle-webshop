from pydantic import BaseModel, Field


class Produkt(BaseModel):
    id: int
    name: str
    menge_ml: int
    preis_chf: float
    beschreibung: str
    bild_pfad: str
    aktiv: bool = True


class KundeInput(BaseModel):
    vorname: str = Field(max_length=100)
    nachname: str = Field(max_length=100)
    email: str = Field(max_length=254)
    telefon: str = Field(default="", max_length=30)
    strasse: str = Field(max_length=200)
    plz: str = Field(max_length=10)
    ort: str = Field(max_length=100)


class WarenkorbItem(BaseModel):
    produkt_id: int
    menge: int = Field(ge=1, le=100)


class BestellungInput(BaseModel):
    kunde: KundeInput
    items: list[WarenkorbItem]
    versandart: str  # "versand" oder "abholung"
    zahlungsart: str  # "stripe" oder "rechnung"
    kommentar: str = Field(default="", max_length=1000)
