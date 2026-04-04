CREATE TABLE IF NOT EXISTS rabattcodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    rabattart TEXT NOT NULL CHECK (rabattart IN ('prozent', 'fixbetrag')),
    rabattwert REAL NOT NULL CHECK (rabattwert > 0),
    mindestbestellwert_chf REAL,
    max_einloesungen INTEGER,
    aktuelle_einloesungen INTEGER NOT NULL DEFAULT 0,
    gueltig_von TEXT NOT NULL,
    gueltig_bis TEXT NOT NULL,
    aktiv INTEGER NOT NULL DEFAULT 1,
    erstellt_am TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS code_einloesungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rabattcode_id INTEGER NOT NULL REFERENCES rabattcodes(id),
    email TEXT NOT NULL,
    bestellung_id INTEGER NOT NULL REFERENCES bestellungen(id),
    eingeloest_am TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(rabattcode_id, email)
);

-- ALTER TABLE Befehle fuer bestellungen werden in init_db() via Python
-- ausgefuehrt, da SQLite kein ADD COLUMN IF NOT EXISTS unterstuetzt.
-- Siehe app/database.py: _add_column_if_not_exists()
