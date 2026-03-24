CREATE TABLE IF NOT EXISTS produkte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    menge_ml INTEGER NOT NULL,
    preis_chf REAL NOT NULL,
    beschreibung TEXT NOT NULL DEFAULT '',
    bild_pfad TEXT NOT NULL DEFAULT '',
    aktiv INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS kunden (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vorname TEXT NOT NULL,
    nachname TEXT NOT NULL,
    email TEXT NOT NULL,
    telefon TEXT NOT NULL DEFAULT '',
    strasse TEXT NOT NULL,
    plz TEXT NOT NULL,
    ort TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bestellungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kunde_id INTEGER NOT NULL REFERENCES kunden(id),
    status TEXT NOT NULL DEFAULT 'neu',
    zahlungsart TEXT NOT NULL,
    versandart TEXT NOT NULL,
    versandkosten_chf REAL NOT NULL DEFAULT 0,
    total_chf REAL NOT NULL,
    stripe_session_id TEXT,
    kommentar TEXT NOT NULL DEFAULT '',
    erstellt_am TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bestellpositionen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bestellung_id INTEGER NOT NULL REFERENCES bestellungen(id),
    produkt_id INTEGER NOT NULL REFERENCES produkte(id),
    menge INTEGER NOT NULL,
    einzelpreis_chf REAL NOT NULL
);

-- Seed: Olivalle-Produkte
INSERT OR IGNORE INTO produkte (id, name, menge_ml, preis_chf, beschreibung, bild_pfad) VALUES
    (1, 'Olivenöl 250ml', 250, 8.00, 'Biologisches Olivenöl aus Andalusien — kleine Flasche', 'olivenoel-250ml.jpg'),
    (2, 'Olivenöl 750ml', 750, 18.00, 'Biologisches Olivenöl aus Andalusien — grosse Flasche', 'olivenoel-750ml.jpg'),
    (3, 'Olivenöl 3l Kanister', 3000, 50.00, 'Biologisches Olivenöl aus Andalusien — Kanister', 'olivenoel-3l.jpg');
