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
-- UPSERT: init_db() laeuft bei jedem Container-Start. Beim Konflikt werden NUR
-- die Katalog-Spalten aktualisiert. Die admin-editierbaren Aktions-Spalten
-- (aktionspreis_chf, aktionstext, aktion_von, aktion_bis) sind bewusst NICHT
-- gelistet, damit im Admin gesetzte Aktionen einen Neustart ueberleben (Bug #137).
-- ACHTUNG: Kuenftige admin-editierbare Spalten hier ebenfalls NICHT auffuehren.
INSERT INTO produkte (id, name, menge_ml, preis_chf, beschreibung, bild_pfad) VALUES
    (1, 'Olivenöl 250ml', 250, 8.00, 'Die kleine Flasche ist ideal zum Kennenlernen, als Geschenk oder für Feinkostläden, die Olivalle ins Sortiment aufnehmen möchten.', 'products/olivalle-250ml.jpeg'),
    (2, 'Olivenöl 750ml', 750, 18.00, 'Der Klassiker für den täglichen Gebrauch in der Küche. Ob zum Verfeinern von Salaten, zum Braten oder einfach mit frischem Brot — diese Flasche gehört auf jeden Tisch. Auch beliebt bei Restaurants und Betrieben.', 'products/olivalle-750ml.jpeg'),
    (3, 'Olivenöl 3l Kanister', 3000, 50.00, 'Für Liebhaber, die nicht genug bekommen, und für Gastronomiebetriebe, die auf Qualität setzen: Der Kanister bietet das beste Preis-Leistungs-Verhältnis und reicht für den täglichen Einsatz.', 'products/olivalle-3l.jpeg'),
    (4, 'Olivenöl 500ml', 500, 25.00, 'Olivar de los 3 Ríos – die perfekte Geschenkflasche. Die exklusive Design Kollektion ist inspiriert von den Flusslandschaften des Guadalbarbo, Cuzna und Gato – wo Natur und Olivenkultur seit Generationen im Einklang leben.', 'products/olivalle-500ml.jpeg')
ON CONFLICT(id) DO UPDATE SET
    name         = excluded.name,
    menge_ml     = excluded.menge_ml,
    preis_chf    = excluded.preis_chf,
    beschreibung = excluded.beschreibung,
    bild_pfad    = excluded.bild_pfad;
