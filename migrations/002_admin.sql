CREATE TABLE IF NOT EXISTS admin_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zeitpunkt TEXT NOT NULL DEFAULT (datetime('now')),
    admin_label TEXT NOT NULL,
    aktion TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    bestellung_id INTEGER REFERENCES bestellungen(id)
);

CREATE INDEX IF NOT EXISTS idx_admin_log_bestellung
    ON admin_log(bestellung_id);

CREATE INDEX IF NOT EXISTS idx_admin_log_zeitpunkt
    ON admin_log(zeitpunkt);
