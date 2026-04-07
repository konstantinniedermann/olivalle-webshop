# Security-Notizen

Querschnittsdokumentation zu Security-relevanten Entscheidungen und Audits.

## Template-XSS-Audit

**Stand:** 2026-04-07

`grep -rn "|safe\|Markup(" templates/ app/` findet keine Treffer. Es gibt
aktuell keine Stelle, an der Jinja2-Autoescape umgangen wird.

**Regel für die Zukunft:** Bei jeder neuen Verwendung von `|safe` oder
`Markup()` prüfen, ob Userinput in den markupten String fliessen kann.
Nur statische, vertrauenswürdige Strings markupen. Im Zweifel: stattdessen
escapen lassen.
