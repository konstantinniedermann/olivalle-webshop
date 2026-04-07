# Datenschutz — interne Notizen

Diese Datei dokumentiert Personenbezug-relevante Datenverarbeitungen im
Olivalle-Webshop. Grundlage: Schweizer DSG.

## Admin-Log: client_ip

**Speicherort:** Tabelle `admin_log`, Spalte `details` (via
`admin_repo.log_eintrag_schreiben`).

**Daten:** Zeitstempel, `admin_label`, `aktion`, `client_ip`.

**Zweck:**
- Brute-Force-Schutz (Lockout pro IP)
- Audit-Trail für administrative Aktionen

**Rechtsgrundlage:** Berechtigtes Interesse (IT-Sicherheit, Nachvollzieh-
barkeit von Admin-Eingriffen).

**Aufbewahrungsfrist:** 90 Tage (Vorschlag, noch nicht automatisiert).

**Löschkonzept:** Aktuell manuell. TODO: automatischer Cleanup-Job in
einer späteren Iteration (separates Issue tracken).

**Betroffenenrechte:** Auf Anfrage Einsicht/Löschung über den Inhaber
möglich. Da nur Admin-Aktionen geloggt werden und Admins identisch mit
dem Inhaber sind, ist der Personenbezug auf Drittpersonen minimal.
