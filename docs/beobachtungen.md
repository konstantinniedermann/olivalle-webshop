# Beobachtungen

Posteingang für Befunde, die **kein eigener Vorgang** sind: Dinge, die beim
Arbeiten an etwas anderem auffallen, aber weder in den laufenden Scope gehören
noch für sich genommen ein GitHub-Issue rechtfertigen.

**Warum die Datei existiert:** Sonst gibt es nur zwei Ablagen — „jetzt erledigen"
oder „Issue anlegen". Alles dazwischen wird zwangsläufig zum Issue, und die
Issue-Liste wächst schneller, als sie abgearbeitet wird. Diese Datei ist die
dritte Ablage. Für Olivalle im Maintenance-Modus ist sie der Normalfall: Ein
Befund, der den Produktivbetrieb nicht stört, wird hier notiert und nicht zum
Vorgang gemacht.

## Wie sie benutzt wird

**Eintragen** (Claude, ohne Rückfrage): Ein Befund, der Regel 3 der
übergeordneten `../CLAUDE.md` nicht erfüllt, kommt hier als kurzer Eintrag rein.
Keine Definition of Done, kein Milestone, keine Labels.

Form eines Eintrags:

```markdown
### JJJJ-MM-TT — Titel, der den Befund in einem Satz sagt

**Thema:** Kurzes Stichwort

**Fundort:** Datei, Symbol, Seite — worauf sich der Befund bezieht.

**Beobachtung:** Was auffiel.

**Ursprung:** Woraus der Befund fiel (Issue, Release, Session).

**Einschätzung:** Erste Bewertung — ausdrücklich vorläufig.
```

**Das Thema wird wiederverwendet, nicht erfunden.** Vor dem Schreiben:

```bash
sed -n '/^## Offen/,$p' docs/beobachtungen.md \
  | grep '^\*\*Thema:\*\*' | sort | uniq -c | sort -rn
```

Gibt es das Stichwort schon, wird genau dieses genommen. Beschreibt ein
bestehender Eintrag denselben Befund aus derselben Ursache, wird **dort
ergänzt** statt neu angelegt. Der Zweck ist nicht Ordnung, sondern Sichtbarkeit:
Häufungen sollen beim Eintragen auffallen und nicht erst bei der Auswertung.

**Auswerten** (gemeinsam, in Ruhe): über den Skill `beobachtungen-auswerten`.
Er verifiziert jeden offenen Eintrag am aktuellen Stand des Repos, bevor
entschieden wird — ein Eintrag ist eine Behauptung, kein Befund. Danach bekommt
jeder Eintrag genau einen von fünf Ausgängen:

| Ausgang | Bedeutung |
|---------|-----------|
| **Verworfen** | Die Behauptung trifft nicht zu. Eintrag wandert mit **Gegenbeleg** ins Archiv — der Beleg verhindert, dass derselbe Fund wiederkommt |
| **Abhaken** | Trifft zu, wir tun bewusst nichts. Mit Begründung, und wo sinnvoll mit **Reevaluations-Trigger** („kommt zurück, wenn …") |
| **Mitmachen** | Trivial-Fix, sofort erledigt, eigener Commit |
| **Doku / Regel / Memory** | Erkenntnis ohne Vorgang — ADR, arc42, `CLAUDE.md` oder Memory |
| **Issue** | Erfüllt Regel 3 der `../CLAUDE.md`. Neu, an ein bestehendes angehängt, oder mehrere gebündelt — nur auf ausdrückliche Zustimmung |

**„Abhaken" ist ein vollwertiges Ergebnis und ausdrücklich der Normalfall.** Ein
Eintrag, der monatelang unangetastet bleibt, hat sich damit selbst beantwortet.

**Es gibt keinen automatischen Auslöser.** Wann ausgewertet wird, entscheidet
der Nutzer.

### Bleibt ein Eintrag nach einer Auswertung offen

Dann trägt er, was die Verifikation ergeben hat:

```markdown
**Verifiziert:** TT.MM.JJJJ gegen v1.4.10 — belegt
(`app/services/email_service.py` → `_fehlergrund`).
Offen ist nur die Entscheidung, ob …
```

Die nächste Auswertung verifiziert einen solchen Eintrag **nicht neu**. Sie
prüft nur, ob sich an den im Beleg genannten Pfaden seither etwas bewegt hat
(`git log <ref>..HEAD -- <pfade>`); ist dort nichts passiert, gilt der Beleg
weiter. Ein frischer Eintrag hat kein `Verifiziert`-Feld — er ist unverifiziert,
und genau das soll man sehen.

**„Notieren" ist kein Ausgang.** Es klingt nach Entscheidung, ist aber
Vertagung, und genau daran wächst die Datei. Wo etwas später wieder relevant
wird, ist der richtige Ausgang „Abhaken **mit Trigger**".

---

## Offen

### 2026-09-09 — Kein „E-Mail erneut senden" im Admin; Nachsenden geht nur über Statuswechsel

**Thema:** E-Mail-Versand

**Fundort:** `app/routers/admin.py:294` (`sende_status_email` nur im
Statuswechsel-Pfad), `app/routers/bestellungen.py:56` und
`app/routers/webhooks.py:75` (Bestellbestätigung nur im Bestell-/Webhook-Pfad).

**Beobachtung:** Schlägt ein Versand fehl, gibt es keinen Weg, dieselbe Mail
noch einmal auszulösen. Der Stakeholder hat am 09.09. den Status von
Bestellung #37 auf `neu` → `in_bearbeitung` → `abholbereit` zurückgeschaltet,
um die Abholbereit-Mail erneut zu triggern — das ist die einzige verfügbare
Methode und erzeugt zwei irreführende Einträge im Verlauf. Die
Bestellbestätigung lässt sich überhaupt nicht nachsenden.

**Ursprung:** Störungsanalyse Brevo-Ausfall vom 31.08.2026 (Bestellung #37),
Session vom 09.09.2026.

**Einschätzung:** Vorläufig. Ein Knopf „erneut senden" pro Verlaufseintrag wäre
naheliegend, ist aber ein neues Feature — im Maintenance-Modus nicht
selbstverständlich gerechtfertigt. Gegenargument: Bei ~1 Bestellung/Monat ist
der Statuswechsel-Umweg zumutbar, solange die Ursache eines Fehlers jetzt im
Verlauf steht. Frage für die Auswertung: Wie oft kommt das realistisch vor?

### 2026-09-09 — Ein fehlgeschlagener Mailversand löst keine Benachrichtigung aus

**Thema:** E-Mail-Versand

**Fundort:** `app/services/email_service.py` → `_log_email` (Ausgang
`email_fehler`); `docs/runbook-incident.md`; HTTP/TLS-Monitoring aus #111.

**Beobachtung:** Der Versand für Bestellung #37 scheiterte am 31.08.2026. Bemerkt
wurde es am 09.09.2026 — neun Tage später, und nur weil der Stakeholder ohnehin
ins Dashboard schaute. Das bestehende Monitoring prüft Erreichbarkeit und TLS,
nicht den Erfolg der Fachlogik. Ein `email_fehler` bleibt still im admin_log
stehen. Der Kunde von #37 hat weder Bestellbestätigung noch Abholbereit-Mail
erhalten und wartete neun Tage ohne Rückmeldung.

**Ursprung:** Störungsanalyse Brevo-Ausfall vom 31.08.2026, Session vom
09.09.2026.

**Einschätzung:** Vorläufig, aber von den Befunden dieser Session der mit dem
grössten Kundeneffekt — ein Ausfall bleibt beliebig lange unbemerkt. Denkbar
schlank: der bestehende Healthcheck meldet die Zahl der `email_fehler` der
letzten 24 h, oder der Admin zeigt einen Zähler ungelesener Fehler. Ein
zusätzlicher Kanal für die Fehlermeldung selbst (SMS, Push) wäre naheliegend,
scheitert aber daran, dass die Störung genau den Kanal betraf, über den
benachrichtigt würde.

### 2026-09-09 — Fly.io hat keine feste ausgehende IP; IP-Allowlists bei Drittdiensten sind darum untauglich

**Thema:** Betrieb / externe Dienste

**Fundort:** `fly.toml`; `fly ips list` zeigt nur eingehende IPs, keine
Egress-IP allokiert.

**Beobachtung:** Die ausgehende IP der Maschine wechselt: am 31.08.2026 meldete
Brevo `2605:4c40:159:f110::2574` (IPv6), am 09.09.2026 antwortete dieselbe
Maschine mit `167.88.159.93` (IPv4). fly.io routet ausgehenden Verkehr über
einen gemeinsamen NAT-Pool. Eine einzelne IP bei einem Drittdienst
freizuschalten hält deshalb nicht; eine feste Egress-IP ist bei fly.io ein
kostenpflichtiges Extra (`fly ip allocate-egress`).

**Ursprung:** Störungsanalyse Brevo-Ausfall vom 31.08.2026, Session vom
09.09.2026.

**Einschätzung:** Vorläufig. Betrifft aktuell nur Brevo, gilt aber für jeden
Dienst mit IP-Allowlist — auch Stripe, falls dort je eine aktiviert wird.
Kandidat für einen Absatz in `docs/arc42.md` (Randbedingungen) statt für einen
Vorgang. Für Brevo selbst ist die Konsequenz bereits gezogen: IP-Prüfung im
Brevo-Konto deaktiviert, nicht eine IP freigegeben.

## Erledigt

Noch nichts ausgewertet. Abgeschlossene Einträge kommen hier eingedampft hin —
eine Zeile mit Ausgang und Verweis; die Begründung lebt dort, wo sie hingehört
(Issue-Body, Commit, Memory). Ausnahme sind verworfene Einträge: die behalten
ihren Gegenbeleg. Wächst der Abschnitt, zieht er in eine eigene
`beobachtungen-archiv.md` um.
