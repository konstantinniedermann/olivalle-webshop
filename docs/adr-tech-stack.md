[← Übersicht](index.md)

# ADR: Tech-Stack-Wahl

**Status:** Entschieden · **Datum:** 2026-04 (rückwirkend dokumentiert) · **Bezug:** arc42 §4 Lösungsstrategie

## Kontext

Olivalle ersetzt einen manuellen Bestellprozess (Tally-Formular + manuelle Rechnung) durch einen Webshop für einen Schweizer Einzelunternehmer mit ~100 Bestellungen/Monat. Der Entwickler ist Python-/SQL-erfahren, in JavaScript/React aber Anfänger. Wartbarkeit durch eine Einzelperson, tiefe Betriebskosten und Schweizer Rechtskonformität (MWST, DSG) sind ausschlaggebend.

## Entscheidung

| Bereich | Wahl | Kernbegründung |
|---|---|---|
| Sprache/Framework | Python + FastAPI | Entwickler kennt Python; FastAPI ist schlank, typsicher, gut dokumentiert |
| UI | Jinja2-Templates + Tailwind CSS (server-rendered) | Kein zweites Framework/Sprachkontext; alles in Python |
| Datenbank | SQLite (Datei auf fly.io-Volume) | Eine Datei, kein DB-Service; reicht für ~100 Bestellungen/Mt |
| Payments | Stripe | TWINT (CH) + Kreditkarte nativ; etablierte Webhook-Integration |
| QR-Rechnung | swiss-qr-bill (`qrbill`) | Open Source, direkt im Code, kein Bexio-Abo |
| Hosting | fly.io (1 Docker-Container) | Günstig (~$2/Mt real), kommerziell erlaubt, einfaches Deploy |
| E-Mail | Brevo | EU/DSG-konform, Free Tier deckt das Volumen (siehe [E-Mail-Provider-ADR](adr-email-provider.md)) |

## Verworfene Alternativen

- **React/Next.js-SPA** — verworfen: zweiter Sprach-/Build-Kontext, für einen Anfänger und einen simplen Shop unnötige Komplexität (KISS/YAGNI). Server-rendered HTML genügt.
- **PostgreSQL** — verworfen: eigener Service + Betrieb/Backup-Aufwand, der bei diesem Volumen keinen Nutzen bringt. SQLite + Litestream-Replikation deckt Persistenz und Backup ab.
- **Bexio/SaaS-Rechnung** — verworfen: laufende Kosten; QR-Rechnung lässt sich Open Source direkt erzeugen.
- **PaaS wie Heroku/Render** — verworfen zugunsten fly.io wegen Preis und Docker-Kontrolle.

## Konsequenzen

- **Positiv:** Ein einziger Sprach-/Tooling-Kontext (Python); minimale Fixkosten; geringe Betriebslast für eine Einzelperson; volle Kontrolle über QR-Rechnung und Daten.
- **Negativ / Grenzen:** SQLite skaliert nicht für hohe Parallel-Schreiblast (für dieses Volumen irrelevant); server-rendered UI bietet weniger clientseitige Interaktivität — bewusst akzeptiert.
- **Folge-ADRs:** Domain-Registrar, E-Mail-Provider und Backup-Strategie sind separat dokumentiert (siehe [ADR-Index](adr-index.md)).
