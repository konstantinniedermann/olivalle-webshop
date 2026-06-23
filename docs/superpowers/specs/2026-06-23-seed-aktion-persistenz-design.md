# Design: Seed überschreibt Admin-Aktionen nicht mehr (Bug #137, Fix zu #134)

> Status: genehmigt 2026-06-23 · Bug #137 · wird auf `feat/134-aktionspreise` vor dem Merge umgesetzt

## Problem

`init_db()` (`app/database.py`) führt bei **jedem** Container-Start alle Migrationen
neu aus. Der Produkt-Seed in `migrations/001_initial.sql` nutzt dabei
`INSERT OR REPLACE`, was die **gesamte** Produktzeile ersetzt.

#134 hat der Tabelle `produkte` vier admin-editierbare Spalten hinzugefügt
(`aktionspreis_chf`, `aktionstext`, `aktion_von`, `aktion_bis`), die der Inhaber
über die Admin-Oberfläche setzt. Der Seed listet diese Spalten **nicht** auf →
bei jedem Neustart fallen sie auf `NULL` zurück. **Eine im Admin gesetzte Aktion
verschwindet damit stillschweigend** bei jedem Deploy, fly.io-Maschinenneustart
oder Litestream-Restore.

Der Fehler entsteht erst mit #134 (vorher hatte `produkte` keine
admin-editierbaren Spalten) und war **nie in Produktion**, da #134 noch nicht
gemerged ist.

### Betroffene Spalten (Umfang)

Einzige admin-editierbare Spalten auf `produkte` sind die 4 Aktions-Spalten
(`aktion_setzen`/`aktion_entfernen` in `produkt_repo.py`). `aktiv` ist **nicht**
admin-editierbar. Der Umfang ist damit exakt auf die 4 Aktions-Spalten begrenzt.

## Entscheidung

Option C (von drei evaluierten Ansätzen): **Seed als gezieltes UPSERT, das nur
die Katalog-Spalten aktualisiert.**

| Option | Kern | Bewertung |
|---|---|---|
| A — separate Tabelle `produkt_aktionen` | Aktions-Spalten aus `produkte` auslagern | Strukturell am saubersten, aber Umbau an #134; 1:1-Split für 4 Spalten over-normalisiert |
| **C — UPSERT nur Katalog-Spalten** ⭐ | `ON CONFLICT(id) DO UPDATE` nur für Katalog | Kleinster Eingriff, kein #134-Umbau, Wurzel getroffen |
| B — `INSERT OR IGNORE` | Seed aktualisiert existierende Zeilen nie | Grob: Katalog-Korrekturen per Migration greifen nicht mehr |

Begründung C: KISS/YAGNI für ein kleines Projekt. Die Katalog-Spalten bleiben
Git-/Migrations-verwaltet (Korrekturen greifen weiter bei jedem Boot), die
Admin-Spalten bleiben unberührt. Kein Schema-Umbau, #134-Code unverändert.

## Umsetzung

### 1. `migrations/001_initial.sql`

`INSERT OR REPLACE` → `INSERT … ON CONFLICT(id) DO UPDATE SET` mit ausschliesslich
den Katalog-Spalten:

```sql
INSERT INTO produkte (id, name, menge_ml, preis_chf, beschreibung, bild_pfad) VALUES
    (1, ...), (2, ...), (3, ...)
ON CONFLICT(id) DO UPDATE SET
    name         = excluded.name,
    menge_ml     = excluded.menge_ml,
    preis_chf    = excluded.preis_chf,
    beschreibung = excluded.beschreibung,
    bild_pfad    = excluded.bild_pfad;
```

Ein Kommentar warnt davor, künftige admin-editierbare Spalten hier aufzunehmen.

### 2. Regressionstest (`tests/test_seed_aktion_persistenz.py`)

`init_db()` → Aktion via `aktion_setzen` setzen → `init_db()` erneut (simuliert
Neustart) → Aktion ist **weiterhin** gesetzt. Schützt die Wurzel dauerhaft.

### 3. Dokumentation

- `docs/arc42.md`: Seed-/Persistenz-Verhalten ergänzen, falls dort beschrieben.
- `docs/user-stories-testplan.md`: Testfall „Aktion überlebt Neustart" ergänzen.
- #134-Design-Spec: Querverweis auf diesen Fix.

## Risiken / Trade-offs

- **Disziplin-Footgun:** Jede künftige admin-editierbare Spalte muss bewusst aus
  der UPSERT-Liste herausgehalten werden. Mitigation: Kommentar im Seed.
- Verhalten für die Katalog-Spalten bleibt identisch (Korrekturen greifen bei
  jedem Boot) — keine Verhaltensänderung für bestehende Produkte 1–3 ausser dem
  Schutz der Aktions-Spalten.
