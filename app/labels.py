"""Zentrale Labels für Zahlungs- und Versandarten.

Zwei separate Label-Sets, weil die Zielgruppen unterschiedliche Texte brauchen:
- ADMIN: kurz, für die Admin-Tabelle (Stakeholder kennt die Begriffe)
- EMAIL: ausführlich, selbsterklärend für Kunden
"""

ZAHLUNGSART_LABELS_ADMIN: dict[str, str] = {
    "stripe": "Stripe",
    "rechnung": "Rechnung",
    "abholung_bar": "Bar bei Abholung",
}

ZAHLUNGSART_LABELS_EMAIL: dict[str, str] = {
    "stripe": "Twint / Kreditkarte",
    "rechnung": "Rechnung (QR)",
    "abholung_bar": "Bezahlung bei Abholung",
}

VERSANDART_LABELS: dict[str, str] = {
    "versand": "Postversand",
    "abholung": "Abholung in der Region Olten",
}


def zahlungsart_admin(value: str) -> str:
    return ZAHLUNGSART_LABELS_ADMIN.get(value, value)
