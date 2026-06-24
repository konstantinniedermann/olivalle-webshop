# CAS-Fazit Olivalle — Persönliche Reflexion (Arbeitsstand)

> **Status:** In Arbeit, Interview-basiert (Issue #113). Pro Thema: Rohnotizen (O-Ton) +
> Belege (Commit-/Issue-Anker) + erster Entwurf in Ich-Stimme.
> **Endform:** frei erzählend, Ich-Perspektive, *keine* Raster-Gliederung. Wird zum Schluss
> verdichtet in `../CAS-Abgabe.md §3 „Persönliches Fazit"`.
> **Zusammenstreichen/Kürzen** erfolgt erst, wenn alle Themen erfasst sind.

## Interview-Spielregeln (mit KN vereinbart)

- Claude führt als Interviewer, KN antwortet in eigenen Worten (Stichworte genügen).
- Max. **1–2 Themen pro Rückfrage-Runde** — sonst Überblicksverlust.
- Fragen immer **nummeriert taggen** (z. B. *Frage 1.5.3*), damit KN sauber referenzieren kann.
- **Kein thematisches Hin-und-Her-Springen.**
- Nach jedem Thema: **unterbrechen**, Notizen ins `.md` zusammenstellen, Fortschritt im Issue festhalten.
- Jede Aussage an einer **konkreten Olivalle-Situation** (Commit-/Issue-Bezug) verankern — Belege sind der Notenhebel (Kriterium 18: 3 belegte Veto-Entscheidungen + Übertrag = voller Score).

## Fortschritt

- [x] **Thema 1 — Lernkurve** (Rohnotizen + Entwurf erfasst)
- [x] **Thema 2 — Agentic Coding konkret** (Workflow half / bremste — erfasst)
- [x] **Thema 3 — Veto-Momente** (Belegbank + Recht-Vertrauensgrenze + Geschäftslogik — erfasst)
- [x] **Thema 4 — Fehler & Aha-Momente** (knapp/ehrlich erfasst)
- [x] **Thema 5 — Claude beim Designen** (Architektur stark, Visuelles unbeurteilbar, Mockup-Vorsatz — erfasst)
- [x] **Thema 6 — Tooling ehrlich** (gh-Issues Favorit, context7 unsichtbar-nützlich, grepai unsicher — erfasst)
- [x] **Thema 7 — Token-/Kosten-Bewusstsein** (Budgetierung nach Aufgabentyp; Spar-Tools-Nutzen nicht belegbar — erfasst)
- [x] **Thema 8 — Meta-Reflexion** (anderer statt weniger Aufwand; „anonyme Experten" & Vertrauen — erfasst, Herzstück)
- [x] **Thema 9 — Übertrag** (Behalten/Anpassen/Neu/Weglassen + Robustheit + Schlussthese — erfasst)
- [ ] Schluss A — Wo lief KI in die falsche Richtung + mein Fazit
- [ ] Schluss B — Deployment heikel → Human-in-the-Loop stärken

---

## Thema 1 — Lernkurve: erste eigene Webapp + CAS-Konzepte

### Rohnotizen (O-Ton KN)

- **Grundhaltung:** durchgehend zuversichtlich — „das werde ich schon schaffen". Stark **motiviert durch die Fortschritte/Beispiele aus der Vorlesung**.
- In die neuen Technologien (FastAPI, Jinja2, Stripe) habe ich mich **nicht gross eingelesen** — CC hat mir bei der **Recherche von Tools / Strategien / Vorgehen** geholfen.
- Die **Struktur, wie man ein Softwareprojekt professionell angeht**, war mir grösstenteils nicht geläufig. arc42 / ADRs / GitHub-Issues haben mir **Struktur und Übersicht** gegeben — vorausplanen, Abhängigkeiten und Blocker setzen. Das wäre sonst mit grosser Disziplin und Aufwand verbunden gewesen und hätte **ohne AI deutlich schlechter funktioniert**.
- **Kosten-Themen** (Domain, Hosting, E-Mail-Provider, QR-Rechnung) habe ich erst durch CC-Recherche kennengelernt und mit Alternativen verglichen — die Entscheidung am Ende aber **selbst übernommen** (meist CCs Empfehlung gefolgt, aber auch schon widersprochen).
- **Security war Neuland.** Abhängigkeiten hätte ich grösstenteils auch selbst erkannt, aber Sicherheitsthemen nicht. Wie es ganz ohne CC gelaufen wäre, kann ich nicht sagen — **an so ein Projekt hätte ich mich sonst gar nicht gewagt** (erste nachhaltig erstellte, deployte App).

> **Vorgriff Thema 8 (KN hat es hier schon gesagt — dort vertiefen):**
> Mehrfach habe ich **blind vertraut**. Das muss man beim Delegieren an Agenten auch können —
> wie bei Mitarbeitenden, denen man im Job vertraut. Wo mir die Expertise zur Beurteilung fehlte,
> habe ich **nachgehakt** („Bist du dir sicher?", „Hast du an X gedacht?"); teils war mir die Zeit
> nicht wert, alles zu überprüfen.

### Belege (Anker)

- **ADR E-Mail-Provider** — `docs/adr-email-provider.md`, Commit `496c750` (01.04.2026):
  Resend (USA) ursprünglich vorgesehen → **verworfen wegen DSG** (kein EU-Standort).
  **Brevo gewählt, obwohl Lettermint das technisch sauberere async-Python-SDK bot** (passt
  besser zu FastAPI) — technischer Vorteil bewusst zugunsten Geschäftswert (9'000 statt 300
  Mails/Mt, Newsletter, EU-Standort) überstimmt. → Mensch überstimmt den technisch „saubereren"
  AI-Default. *(Vorbehalt: EU-Anstoss kam laut ADR teils vom Stakeholder; KN klärt beim
  Verdichten, was sein Veto war und was SHs.)*
- **Weitere Kosten-/Strategie-ADRs als Beleg für „CC-Recherche → KN entscheidet":**
  `docs/adr-tech-stack.md` (Sprache/UI/DB/Payments/Hosting — fly.io),
  `docs/adr-domain-registrar.md` (Infomaniak für olivalle.ch),
  `docs/adr-backup-strategie.md` (Litestream + Tigris). Index: `docs/adr-index.md`.
- **Security als Neuland → strukturiertes Audit fing, was Intuition nicht sah:**
  Security-Audit-Serie #70–#79 vor Go-Live (z. B. #70 CSRF in Admin-POSTs, Fix `629f019`).

#### Weitere belegte „Mensch überstimmt den Default"-Momente (von KN bestätigt) → Veto-Kandidaten Thema 3

- **C1 — `/health`-`version`-Feld bewusst NICHT nachgerüstet** (Commit `a40bb0e`,
  „…bewusst nicht nachruesten — Entscheidung final"). Die Versioning-Spec sah ein
  `version`-Feld in `/health` vor; KN hat es bewusst weggelassen (YAGNI: Version steht schon
  im Footer + Git-Tags). → Sauberes menschliches YAGNI-Veto gegen das Spezifizierte.
- **C2 — Backup-Monitoring-Kehrtwende** (`docs/adr-backup-strategie.md` Nachtrag 2026-04-22b,
  Z.99: *„nicht Kosten treiben den Wechsel, sondern Korrektheit"*; Spec #118). In #116 hatte
  KN entschieden, die GitHub-Action-Lösung lohne sich nicht für ~CHF 1.40/Mt. Kurz darauf
  bewusst umgeschwenkt — **nicht wegen Kosten, sondern wegen Korrektheit** (Heartbeat-Pfad-Bug,
  falsche Mess-Semantik). → KN überstimmt seine *eigene* frühere, „wirtschaftlich klingende"
  Logik; widersteht dem „billiger = klüger"-Reflex.
- **C4 — QR-Rechnung als PDF statt SVG** (Commit `798177f`). KNs Begründung: **PDF-Rechnung
  ist Standard bei Schweizer Online-Shops** (UX-/Domänen-Urteil) — die Brevo-SVG-Inkompatibilität
  war sekundär. → Menschliches Domänenwissen schlägt das technisch „elegantere" SVG.

### Entwurf (Ich-Stimme) — *roh, wird gekürzt*

Olivalle war meine erste eigene Webapp — und obwohl FastAPI, Jinja2 und Stripe alle neu waren,
hatte ich nie das Gefühl, das nicht zu schaffen. Die Beispiele aus der Vorlesung haben mich
enorm motiviert: Wenn das dort funktioniert, kriege ich das auch hin. Ich habe mich bewusst
*nicht* tief in jede neue Technologie eingelesen — stattdessen war Claude Code mein
Recherche-Partner für Tools, Strategien und Vorgehen.

Was mir wirklich gefehlt hat, war nicht das Programmieren, sondern die **Struktur, wie man ein
Softwareprojekt professionell angeht**. arc42, ADRs und das Arbeiten mit GitHub-Issues waren mir
grösstenteils fremd. Genau hier lag der grösste Gewinn: Ich konnte vorausplanen, Abhängigkeiten
und Blocker sichtbar machen und den Überblick behalten. Diese Disziplin hätte ich allein kaum
durchgehalten — mit AI ging sie fast nebenbei.

Bei allem, was Geld kostet — Domain, Hosting, E-Mail-Versand, QR-Rechnung — habe ich die Optionen
überhaupt erst durch Claudes Recherche kennengelernt und vergleichen können. Die Entscheidung habe
ich am Ende aber immer selbst getroffen. Meist bin ich der Empfehlung gefolgt, aber nicht immer:
Beim E-Mail-Provider habe ich Brevo gewählt, obwohl die Alternative Lettermint das technisch
sauberere async-SDK hatte — der Geschäftswert (EU-Datenstandort fürs DSG, viel grösseres
Gratis-Kontingent, Newsletter-Option) war mir wichtiger.

Ehrlich bleibt: Sicherheit war für mich Neuland. Abhängigkeiten im Projekt hätte ich
grösstenteils auch selbst erkannt, die Sicherheitsthemen nicht. Wie das Projekt ganz ohne Claude
gelaufen wäre, kann ich nicht sagen — denn an eine erste, dauerhaft deployte App hätte ich mich
sonst gar nicht herangewagt.

---

## Thema 2 — Agentic Coding konkret: wo der Workflow trug, wo er bremste

### Rohnotizen (O-Ton KN)

- **Kein „Heureka-Rettungsmoment", aber Vertrauen ins Ergebnis:** Ich habe nie eine dramatische
  „Rettung" gespürt — eher das Gefühl, dass durch den superpowers-Workflow am Ende **etwas Gutes
  herauskommt, das nicht mehr oft nachjustiert werden muss**.
- **Der Seed-Bug #137 als belegtes Beispiel:** Den hätte ich auch bemerkt — aber erst, **wenn er
  live gewesen wäre**. Dass der Workflow ihn vorher fand, war der Mehrwert.
- **HARD-GATE bremste — und kostete Tokens:** Das erzwungene Brainstorming *vor jeder*
  Implementierung hat oft gebremst und mit dem kleinen Anthropic-Abo auch das **Token-Limit
  belastet** — auch Kleinkram kostete immer viel Zeit und Tokens.
- **Vorsatz (noch nicht umgesetzt):** Ich habe mir vorgenommen, **kleinere Sachen künftig selbst**
  anzugehen, also das HARD-GATE bewusst zu umgehen — in *diesem* Projekt habe ich es aber **noch
  nicht** gemacht. So war es lehrreich, wenn auch nicht effizient.
- **Overkill sieht man oft erst im Nachhinein:** Dass der volle Prozess für eine Sache übertrieben
  war, lässt sich manchmal erst hinterher feststellen.
- **Aber: Brainstorming als Schärf- und Inspirationsmotor.** Häufig hat der **Dialog mit CC** das
  Issue erst richtig geschärft — oder eine **nicht abgedeckte Lücke** sichtbar gemacht, die behoben
  werden muss (aber bewusst nicht in der aktuellen Session). Ohne dieses Brainstorming wäre man
  womöglich gar nicht darauf gekommen.
- **Selbsteinschätzung (zu #123/#122):** Dass der Restore-Test einen stillen Datenverlust-Bug
  aufdeckte, zeigte mir auch, dass ich **im SE noch nicht sehr erfahren** bin — und genau deshalb
  sind solche Guidelines und unterstützenden Agenten für mich sehr hilfreich.
- *(2.3a revDSG-TDD: keine konkrete Erinnerung — nicht verwerten.)*

### Belege (Anker)

- **Workflow fing Bug vor Produktion:** Seed-UPSERT-Bug **#137**, entdeckt im **Brainstorming zu
  #135** (vor Merge von #134), nie in Prod. Fix `162d923` + Regressionstest
  `tests/test_seed_aktion_persistenz.py`.
- **Prozess (Restore-Test) deckte latenten Daten-GAU auf:** **#123 → #122** — SQLite `mode=rwc`
  legt bei fehlender DB still eine leere an; Fix `bbf5304` (`mode=rw` → 500 statt leise leere DB).
- **HARD-GATE-Overhead bei Trivial-Fix:** Stripe-TWINT-Crash **#97** = Ein-Zeilen-Fix `de6794c`,
  durchlief trotzdem die Phasen.
- **Brainstorming gebar neue Issues (Schärfen/Inspiration):** Arbeit an **#101 (QR)** legte den
  Ruff-Backlog **#103** offen; Brainstorming zu **#134/#135** gebar **#137**.

### Entwurf (Ich-Stimme) — *roh, wird gekürzt*

Einen einzelnen dramatischen Moment, in dem mich der Workflow „gerettet" hat, gab es für mich
nicht. Was ich hatte, war ein anderes, ruhigeres Gefühl: Am Ende des superpowers-Zyklus kam meist
etwas heraus, an dem ich nicht mehr lange nachjustieren musste. Der Seed-Bug #137 ist das beste
Beispiel — ich hätte ihn auch gefunden, aber erst, wenn er bereits live Schaden angerichtet hätte.
Dass das Brainstorming ihn vorher aufgespürt hat, war genau dieser stille Mehrwert.

Ehrlich ist aber auch die andere Seite: Das HARD-GATE, das *vor jeder* Implementierung ein
Brainstorming erzwingt, hat mich oft gebremst — und mit meinem kleinen Anthropic-Abo spürbar
Tokens gekostet. Auch ein Ein-Zeilen-Fix wie der Stripe-TWINT-Crash #97 musste durch alle Phasen.
Ich habe mir vorgenommen, kleinere Dinge künftig selbst zu erledigen und das Gate bewusst zu
umgehen — in diesem Projekt habe ich es aber noch nicht getan. Es war lehrreich, aber nicht immer
effizient, und ob der volle Prozess Overkill war, sah ich oft erst im Nachhinein.

Gleichzeitig hat genau dieses Brainstorming oft mehr gebracht, als nur zu bremsen: Im Dialog mit
Claude wurde manches Issue erst richtig scharf, oder es tauchte eine Lücke auf, die ich vorher gar
nicht gesehen hatte — etwas, das behoben werden muss, aber bewusst in eine spätere Session
wandert. So entstand aus der Arbeit an der QR-Rechnung der Blick auf den Ruff-Backlog (#103), und
aus dem Brainstorming zu den Aktionspreisen der Seed-Bug (#137). Und als der Restore-Test einen
stillen Datenverlust-Bug aufdeckte, wurde mir klar, dass ich im Software Engineering noch nicht
erfahren bin — gerade deshalb sind solche Leitplanken und unterstützenden Agenten für mich
wertvoll.

---

## Thema 3 — Veto-Momente: wo ich Claude bewusst *nicht* entscheiden liess

### Rohnotizen (O-Ton KN)

**CC als Recht-/Compliance-Sparringspartner (über Software hinaus):**
- Im Austausch mit CC habe ich viele **rechtliche Themen** besprochen (AGB, MwSt, Nährwert-/
  Lebensmittel-Deklaration), die man sonst womöglich nicht abgedeckt hätte. CC war also nicht nur
  bei Software-Themen nützlich — und ich musste **keine Einschätzung einer Rechtsperson** einholen.

**3.1 — Vertrauensgrenze beim Recht (Vertrauen *kalibriert auf Tragweite*):**
- Ich habe es **mit dem SH besprochen — am Ende trägt er die Verantwortung**.
- Leitprinzip bei diesen Entscheidungen: *„Sollte es nichts nützen, so schadet es nicht."*
  Wahrscheinlich hätte es nie ein ernsthaftes Problem gegeben, wenn man z. B. die
  Nährwertdeklaration *nicht* macht — aber so sind wir auf der sicheren Seite.
- Ich habe die Texte mit denen **bekannter Webshops abgeglichen**, sie als Inspiration genutzt und
  darauf vertraut, dass die sich in dem Bereich keine Fehler leisten.
- **Keine** dieser Entscheidungen hatte grosse Tragweite, wo ein Fehler teuer geworden wäre →
  bewusst *niedrige* Prüf-Tiefe, weil das Risiko niedrig war.

**3.2 — Was mir zu wichtig zum Delegieren war (Geschäftslogik):**
- **Preise, Aktionspreise und Rabattcodes haben SH und ich manuell geprüft.** Funktionieren
  Aktionspreise & Rabattcodes? Wird korrekt abgerechnet? Lassen sich mehrere Codes
  aktivieren/kombinieren? Ein Fehler hätte **direkten finanziellen Schaden für den SH** bedeutet —
  deshalb war manuelles Prüfen und Sicher-Gehen hier Pflicht.

### Belege (Anker)

- **Recht/Compliance breit abgedeckt mit CC:** revDSG-Datenschutz **#69** (`fe74806`);
  **Lebensmittel-Deklaration nach LIV Art. 39** **#100** (mit failing-tests-first `1e54e28`,
  Doku-Nachweis `9a4b625`); AGB **#42/#43/#135**; Impressum/Datenschutz (`1469c53`).
  `docs/legal/{agb,datenschutz,impressum,lebensmittel-deklaration}.md`.
- **Geschäftslogik-Veto in Tests gegossen (kein Code-Stapeln):**
  `tests/test_aktionspreis_bestellung.py::test_rabattfaehiger_subtotal_nur_nicht_aktion` und
  `::test_rabattfaehiger_subtotal_reine_aktion_null` — Rabattcode greift **nur auf den
  Nicht-Aktions-Anteil**, kein Stapeln auf bereits reduzierte Ware. Plus `test_aktions_service.py`
  (Datumsgrenzen inklusive), `test_aktionspreis_bestellung.py` (korrekte Abrechnung).

### Veto-Belegbank — Spektrum (Kriterium 18: 3 belegte nötig, hier deutlich mehr)

| Veto | Art | Beleg |
|---|---|---|
| Brevo statt Resend/Lettermint | wirtschaftlich + DSG (vs. technisch sauberes async-SDK) | `496c750` / ADR |
| C1 `/health`-version weggelassen | YAGNI / technisch | `a40bb0e` |
| C2 Backup-Monitoring-Kehrtwende | Korrektheit > Kosten | ADR Nachtrag b / #118 |
| C4 QR PDF statt SVG | Domänen-Standard CH-Shops | `798177f` |
| **Recht: Tragweite-kalibriertes Vertrauen** | rechtlich (SH trägt Verantwortung, „schadet nicht") | #69 / #100 / AGB |
| **Preise/Rabattcodes manuell geprüft** | Geschäftslogik (direkter $-Schaden) | `test_rabattfaehiger_subtotal_*` |

→ Spektrum **technisch / wirtschaftlich / rechtlich / geschäftslogisch** abgedeckt.

### Entwurf (Ich-Stimme) — *roh, wird gekürzt*

Spannend war, dass Claude längst nicht nur beim Code half. Viele **rechtliche Themen** — AGB,
Mehrwertsteuer, die Nährwert- und Lebensmittel-Deklaration — habe ich mit ihm durchgesprochen, und
einiges davon hätte ich ohne diesen Austausch vermutlich gar nicht auf dem Schirm gehabt. Ich
musste dafür keine Rechtsperson beiziehen.

Trotzdem habe ich mein Vertrauen bewusst an der **Tragweite** ausgerichtet. Die rechtlichen
Entscheidungen habe ich mit dem SH besprochen — am Ende trägt er die Verantwortung. Und sie folgten
fast alle dem Prinzip „nützt es nichts, so schadet es nicht": Eine fehlende Nährwertdeklaration
hätte real wohl nie ein Problem gegeben, aber mit ihr sind wir auf der sicheren Seite. Ich habe die
Texte an denen bekannter Webshops gespiegelt und darauf vertraut, dass die sich dort keine Fehler
erlauben. Keine dieser Entscheidungen hatte eine Tragweite, bei der ein Fehler teuer geworden wäre
— deshalb war die geringe Prüf-Tiefe für mich vertretbar.

Ganz anders dort, wo ein Fehler **direkt Geld gekostet** hätte: Bei Preisen, Aktionspreisen und
Rabattcodes haben der SH und ich **manuell geprüft**. Rechnet der Shop korrekt ab? Lassen sich
Codes kombinieren oder mehrfach einlösen? Das wollte ich nicht der Automatik überlassen — ein
Fehler hier hätte den SH unmittelbar getroffen. Die wichtigste Regel haben wir zusätzlich in Tests
festgehalten: Ein Rabattcode greift nur auf den nicht reduzierten Anteil, niemals zusätzlich auf
bereits vergünstigte Aktionsware.

Das ist im Rückblick mein Muster bei den Veto-Momenten: Ich habe Claude entscheiden lassen, wo
Fehler billig und reversibel waren — und die Kontrolle behalten, wo sie es nicht waren (Geld,
Geschäftslogik, am Ende auch Recht über den SH).

---

## Thema 4 — Fehler & Aha-Momente: was fingen Tests, was fiel erst live auf?

### Rohnotizen (O-Ton KN)

- **#141 war der schlimmste Bug — hat mich am meisten gestresst.** An die anderen „erst-live"-Bugs
  (#96 Zeitzone, #101 QR-Hausnummer, #97 Stripe-TWINT) erinnere ich mich kaum, an #141 selbst nur
  knapp.
- **Was #141 so stressig machte:** Der Button **„tat nichts"** — kein sichtbarer Fehler, schwer
  zu fassen.
- **Test-Praxis (4.2):** Ja — nach einem Live-Bug kam jeweils ein Regressionstest hinterher
  (#141 → Cache-Busting-Test, #101 → E2E-Hausnummer-Test). Die *tiefer gehende* These über die
  Grenzen von Unit-Tests konnte ich **selbst nicht beurteilen** — passt zu meiner
  Selbsteinschätzung (im SE noch nicht erfahren). Ehrlich festgehalten statt schöngeredet.

### Belege (Anker)

- **#141** — Rabattcode-Button „tat nichts": alte `cart.js` aus Browser-Cache (`getRabattSubtotal
  is not a function`). Fix `1078eac` (Cache-Busting `?v={{ app_version }}` + sauberer Handler) +
  neuer Regressionstest `tests/test_static_cache_busting.py`.
- **#101** — QR-Hausnummer fiel erst beim echten Scan auf; danach E2E-Regressionstest `893875c`.
- *(#96 Zeitzone, #97 Stripe-TWINT: belegt im Dossier, aber von KN nicht erinnert → nicht in den
  Vordergrund stellen.)*

### Entwurf (Ich-Stimme) — *roh, wird gekürzt*

Der Bug, der wirklich hängengeblieben ist, war #141: das Einlösen eines Rabattcodes, bei dem der
Button schlicht „nichts tat". Kein roter Fehler, keine Meldung — einfach keine Reaktion. Genau das
war das Stressige: Wenn etwas *abstürzt*, hat man eine Spur; wenn etwas *nichts tut*, sucht man im
Nebel. Im Hintergrund zog der Browser eine alte, gecachte Version von `cart.js`, in der die neue
Funktion fehlte. An die anderen Produktionsbugs erinnere ich mich ehrlich gesagt kaum — dieser hat
sich eingebrannt.

Was ich aus der Serie mitgenommen habe, ist eine einfache Praxis: Wenn ein Fehler erst live
auftauchte, kam danach sofort ein Test dazu, damit er nicht zurückkommt — beim Cache-Problem ein
Test, der prüft, dass JS/CSS versioniert ausgeliefert werden, bei der QR-Hausnummer ein
End-to-End-Test. Die grössere Frage, *warum* meine grünen Tests diese Dinge nicht vorher gefangen
haben, kann ich fachlich noch nicht abschliessend beurteilen — und das ist Teil meines ehrlichen
Standes als SE-Anfänger.

---

## Thema 5 — Claude beim *Designen* (nicht nur Coden)

### Rohnotizen (O-Ton KN)

- **Vorbehalt:** Schwer zu beurteilen — mir fehlt der Vergleich, weil ich noch wenig SE-Erfahrung
  in Projekten *ohne* AI habe.
- **5.1 Architektur/Struktur:** sicher **sauber und gut strukturiert**. Das Projekt war aber auch
  **nicht sehr innovativ** — daher für AI wohl einfach zu unterstützen.
- **5.1 Visuelles:** kann ich nicht beurteilen. **„First-time-right" gab es quasi nie** — bzw. nie
  so, wie ich es mir vorgestellt hatte; das lag aber wohl auch an meiner **unpräzisen
  Formulierung**.
- **Arbeitsweise:** ohne Mockups gearbeitet, nur **beschrieben**. Teilweise mit CCs Design-
  Vorschlägen gearbeitet — aber da die Site visuell nicht anspruchsvoll ist, war das ein kleiner
  Teil.
- **5.2 / Übertrag:** Mockups hätten bestimmt geholfen — **wenn man schon ein klares Bild im Kopf
  hat**. Vorsatz: **nächstes Mal mit Design-Mockups arbeiten** (→ auch Thema 9).

### Belege (Anker)

- **Iteration statt First-time-right (visuell):** Card-UI-Guidelines #51, dazu mehrere
  Design-Runden — Specs `2026-03-28-card-ui-guidelines`, `2026-03-28-card-ui-responsive`,
  `2026-03-30-card-ui-cleanup`, `2026-03-30-frontend-redesign`,
  `2026-06-23-produktkarte-rabatt-stil-layout`, `2026-06-23-rabatt-preis-zweizeilig`; Kachel-
  Overhaul **#139 noch offen**. → belegt das „nie first-time-right".
- **Architektur sauber:** FastAPI + Jinja2 als bewusst einfache Wahl (kein zweites Framework),
  Card-UI als *System* in CLAUDE.md verankert.

### Entwurf (Ich-Stimme) — *roh, wird gekürzt*

Beim Design tue ich mich mit dem Urteil ehrlich schwer — mir fehlt schlicht der Vergleich, weil
ich kaum Projekte *ohne* AI gebaut habe. Was ich sagen kann: Die **Architektur und Struktur** waren
sauber. Aber Olivalle ist auch kein besonders innovatives Projekt — ein überschaubarer Webshop —,
und genau so etwas kann eine KI gut stützen. Beim **Visuellen** traue ich mir kein Urteil zu. Was
mir auffiel: „first time right" gab es praktisch nie, jedenfalls nie genau so, wie ich es mir
vorgestellt hatte. Ein gutes Stück davon lag aber an mir — ich habe nur **beschrieben** statt
gezeigt, und Beschreibungen sind nun mal unpräzise.

Ich habe komplett **ohne Mockups** gearbeitet. Claudes Design-Vorschläge habe ich teils genutzt,
aber weil die Seite optisch nicht anspruchsvoll ist, war das ein kleiner Teil. Mein klarster
Lernpunkt hier: Beim nächsten Mal will ich **mit Design-Mockups** starten — aber das setzt voraus,
dass ich selbst schon ein klares Bild im Kopf habe. Genau daran hat es oft gefehlt, und kein Agent
kann mir dieses Bild abnehmen.

---

## Thema 6 — Tooling ehrlich: Mehrwert oder Deko/Doppelpflege?

### Rohnotizen (O-Ton KN)

- **GitHub-Issues = Favorit.** Haben sich als mein bevorzugtes Werkzeug herausgestellt.
- **`.plans/` (talent-factory):** in einem *kleineren* Projekt (project-costs) verwendet — hat
  funktioniert, alles lokal und übersichtlich, aber **funktional irgendwann eingeschränkt**. In
  Olivalle nicht genutzt; gh-Issues gewonnen.
- **superpowers:** top — aber mit Nachteilen (HARD-GATE/Token, siehe Thema 2).
- **CLAUDE.md:** top. Wird **automatisch angepasst, damit CC nichts „vergisst"**. Erstes Projekt
  mit CC → konnte nicht von Beginn an perfekt sein, wurde **stetig verbessert**.
- **context7:** **selbst nicht bemerkt**, aber CC hat es wohl genutzt → top, weil ich an etwas
  **weniger denken musste**.
- **grepai:** in CLAUDE.md verankert, eingeführt **um Tokens zu sparen** — aber **unsicher, wie gut
  es tatsächlich genutzt wurde**.
- **6.2 — eine Tracking-Ebene statt zwei:** habe ich mir so nicht überlegt, aber **hat sich
  bewährt**. (Zu wenig SE-Erfahrung, um zu wissen, was es sonst gäbe.)

### Belege (Anker)

- **`.plans/` in Olivalle nie angelegt** (Verzeichnis existiert nicht), obwohl die übergeordnete
  `CLAUDE.md` das Hybrid-System (gh + `.plans/`) vorschreibt → faktisch durch Weglassen entschärfte
  Doppelpflege. De-facto-Detail-Ebene: **41 Specs + 16 Plans** unter `docs/superpowers/`.
- **grepai eingerichtet:** lokaler `.grepai`-Index vorhanden, Nutzung in `CLAUDE.md` verankert.
- **context7:** automatisch bei FastAPI/Stripe (MCP) — für KN unsichtbar im Hintergrund.
- **`make help`** als kanonischer Einstieg (echte Targets: dev, test, lint-all, css-build, …).

### Entwurf (Ich-Stimme) — *roh, wird gekürzt*

Bei den Werkzeugen hat sich für mich klar herauskristallisiert, was ich behalte. **GitHub-Issues**
sind mein Favorit geworden — die Übersicht, die Abhängigkeiten, das Vorausplanen. Das vorgesehene
zweite System, `.plans/`, habe ich in einem kleineren Projekt ausprobiert; es funktionierte und war
schön lokal, stiess aber funktional an Grenzen. In Olivalle habe ich es gar nicht erst angelegt —
ohne das bewusst als Entscheidung zu treffen. Im Rückblick war genau das richtig: eine Detail-Ebene
(die superpowers-Specs neben den Issues) hat gereicht, die zweite hätte nur Doppelpflege bedeutet.
Dass das eine kluge Reduktion war, weiss ich allerdings eher aus dem Ergebnis als aus Erfahrung —
mir fehlt der Überblick, was es sonst noch gäbe.

Am meisten überrascht hat mich, welche Tools im *Hintergrund* wirkten. **context7** habe ich selbst
nie bemerkt — aber Claude hat es offenbar genutzt, um aktuelle Doku nachzuschlagen, und genau das
ist der Punkt: Ein gutes Tool merkt man nicht, weil es einem das Mitdenken abnimmt. Bei **grepai**
bin ich ehrlich unsicher; ich hatte es eingeführt, um Tokens zu sparen, und in der CLAUDE.md
verankert — ob es wirklich viel gebracht hat, kann ich nicht belegen. Und die **CLAUDE.md** selbst
war fast das wichtigste „Tool": Sie ist mit dem Projekt gewachsen, wurde laufend nachgeschärft,
damit Claude über die Sessions hinweg nichts Wesentliches vergisst. Dass sie anfangs nicht perfekt
war, gehört dazu — es war mein erstes Projekt mit Claude Code.

---

## Thema 7 — Token-/Kosten-Bewusstsein

### Rohnotizen (O-Ton KN)

- **superpowers war teuer.**
- **Token-Budgetierung nach Aufgabentyp (selbst entwickelt):**
  - *wenig freie Tokens* → GitHub-Issue-Arbeit, Themen **schärfen und ausarbeiten**.
  - *viel freie Tokens* → grosse **Implementierungen, Code-Reviews, Refactoring**.
- **Vorausarbeiten + Parken:** Themen ausgearbeitet, beiseitegelegt und **später, wenn das Limit
  wieder da war, umsetzen lassen**.
- **Stress mit kleinem Abo:** oft gestresst, die Token-Zeitfenster optimal zu nutzen. Seit dem
  **grossen Abo weniger Stress** — meist genug, selbst ohne darauf zu achten.
- **7.2 — Spar-Mechanismen:** Zu **keinem** (Context-Scopes, `.claudeignore`, grepai) kann ich den
  Nutzen **belegen**.

### Belege (Anker)

- Spar-Mechanismen vorhanden, aber Effekt unbelegt: **Context-Scopes** (Tabelle „Aufgabe → Pfade"
  in `CLAUDE.md`), **`.claudeignore`** (PDFs/Archiv aus Auto-Context), **grepai** (`.grepai`-Index).
- Teuer-Treiber: superpowers-Zyklus (Brainstorm→Plan→TDD→Review) bei *jeder* Änderung — siehe
  Thema 2 (HARD-GATE-Overhead, Trivial-Fix #97).

### Entwurf (Ich-Stimme) — *roh, wird gekürzt*

Kosten waren bei mir vor allem ein **Token-Thema**, und teuer war eindeutig der superpowers-Zyklus
— jede Änderung durch alle Phasen summiert sich. Mit dem kleinen Abo hat mich das zu einer eigenen
Arbeitsweise gezwungen, auf die ich im Rückblick fast ein bisschen stolz bin: Ich habe die Arbeit
nach verfügbarem Token-Budget sortiert. War wenig frei, habe ich an den GitHub-Issues gearbeitet —
Themen geschärft, ausgearbeitet, Abhängigkeiten gesetzt. War viel frei, kamen die teuren Sachen
dran: grosse Implementierungen, Code-Reviews, Refactorings. Manches Thema habe ich fertig
ausgearbeitet, beiseitegelegt und erst umgesetzt, als das Limit sich erneuert hatte.

Ehrlich war das oft auch **Stress** — ich habe ständig geschaut, das Zeitfenster optimal zu nutzen.
Seit ich das grössere Abo habe, ist dieser Druck weg; meist habe ich genug, ohne darauf zu achten.
Was ich *nicht* behaupten kann: dass meine eingebauten Spar-Mechanismen — Context-Scopes,
`.claudeignore`, grepai — wirklich viel gebracht haben. Ich habe sie mit guter Absicht eingeführt,
aber den Effekt kann ich bei keinem belegen. Der wirksamste Hebel war am Ende nicht ein Tool,
sondern **wann** ich **welche Art Arbeit** gemacht habe — und schliesslich das grössere Abo.

---

## Thema 8 — Meta-Reflexion: Aufwand reduziert oder verschoben? Welche Skills sind wirklich meine?

### Rohnotizen (O-Ton KN)

- **8.1 — Aufwand:** Gefühlt **anderer Aufwand, nicht weniger** (Coden → Issues schärfen, Prompten,
  Reviews lesen, Token-Fenster jonglieren).
- **8.2 — Skills (Tabelle bestätigt):**
  - *Wirklich meins:* Projekt-Struktur (arc42, Issues, Abhängigkeiten), agentischen Workflow
    steuern / gut prompten, wissen *wann* prüfen / *wann* vertrauen, Token-/Arbeits-Budgetierung.
  - *„Claude hat's gemacht":* FastAPI-/JS-Code im Detail, Security-Tiefe (CSP/CSRF) selbst
    beurteilen, visuelles Design. (Liste nicht abschliessend.)
- **„Claude hat's gemacht" ist KEIN Problem** — *„delegieren und gezielt kontrollieren können"* ist
  selbst die eigentliche **neue Kompetenz**.
- **Bild:** Toll, ein Tool zu haben, das **Agenten in diversen Rollen spawnt** — man stellt sich
  sein **Team aus Experten** je nach Aufgabe zusammen.
- **ABER das Kernproblem — „anonyme Experten":** Es fühlt sich an wie jemand, der *behauptet*,
  Experte zu sein, und das gut formuliert — aber ohne eigene Kompetenz im Thema bleibt mir **keine
  andere Wahl als zu VERTRAUEN**. Genau das macht es schwierig.
- **Vertrauen braucht Zeit:** Bei einem **menschlichen** Team mit Qualifikationen/Erfahrung fällt
  Vertrauen leichter als bei einem **neuen Agenten**, dem man sofort eine schwierige, selbst nicht
  kontrollierbare Aufgabe gibt. Vertrauen baut man real nur über **Zeit und Erfahrung** auf.
- **Noch zu früh — und vielleicht nie ganz:** Es ist noch zu früh, CC immer mit gutem Gefühl machen
  zu lassen — ich kenne Tool & Agenten zu wenig. Und vielleicht wird das **nie** so sein: Neue
  Modelle/Tools kommen so schnell, dass man **selten lange mit demselben Modell** arbeitet und so
  dessen Stärken/Schwächen kennenlernt.
- **Deshalb auf Erfahrungen anderer angewiesen — und genau hier war das CAS wertvoll:** Austausch
  mit Kommilitonen und Profs über Erfahrungen → viel gelernt.

### Entwurf (Ich-Stimme) — *roh, wird gekürzt*

Wenn ich ehrlich bin, hat die agentische Arbeitsweise meinen Aufwand nicht *reduziert*, sondern
*verschoben*. Ich habe weniger selbst getippt, dafür mehr Zeit damit verbracht, Issues zu schärfen,
Prompts zu formulieren, Reviews zu lesen und Token-Fenster zu jonglieren. Es ist anderer Aufwand,
nicht weniger.

Und doch ist dabei etwas entstanden, das ich als echte Kompetenz verbuche: Projekt-Struktur,
das Steuern des Workflows, das Gespür dafür, *wann* ich prüfe und *wann* ich vertraue. Den
Detail-Code in FastAPI oder JavaScript, die Sicherheitstiefe, das visuelle Design — das hat
grösstenteils Claude gemacht. Für mich ist das **kein Problem**: „Delegieren und gezielt
kontrollieren können" ist selbst die neue Fähigkeit. Es ist beeindruckend, ein Werkzeug zu haben,
das mir je nach Aufgabe ein ganzes **Team aus Experten** zusammenstellt.

Aber genau hier liegt für mich der wunde Punkt, und er ist mir wichtig: Diese Experten sind
**anonym**. Es ist, als arbeite ich mit jemandem, der überzeugend *behauptet*, Experte zu sein —
und solange mir im Thema selbst die Kompetenz fehlt, bleibt mir keine andere Wahl, als zu
**vertrauen**. In einem menschlichen Team baut man Vertrauen über Zeit, Qualifikationen und
gemeinsame Erfahrung auf. Einem nagelneuen Agenten dagegen gebe ich sofort eine schwierige Aufgabe,
die ich selbst nicht kontrollieren kann — und das fällt schwer. Es ist schlicht noch zu früh, Claude
immer mit gutem Gefühl machen zu lassen; ich kenne das Werkzeug und seine Agenten dafür zu wenig.

Vielleicht wird dieses ruhige Vertrauen sogar nie ganz entstehen: Die Modelle und Tools wechseln so
schnell, dass man selten lange genug mit demselben arbeitet, um seine Stärken und Schwächen wirklich
kennenzulernen. Umso mehr ist man auf die Erfahrungen anderer angewiesen — und das ist rückblickend
einer der grössten Werte des CAS gewesen: der Austausch mit Kommilitonen und Dozenten darüber, was
in der Praxis funktioniert und was nicht.

---

## Thema 9 — Übertrag auf künftige Arbeitsweise

### Behalten / Anpassen / Neu / Weglassen (von KN bestätigt)

| Korb | Inhalt |
|---|---|
| **Behalten** | GitHub-Issues als Leitsystem · CLAUDE.md als mitwachsendes „Gedächtnis" · agentischer Workflow mit Augenmass · Token-/Arbeits-Budgetierung nach Aufgabentyp · Vertrauen an Tragweite kalibrieren (billig/reversibel → delegieren) · Geld/Geschäftslogik manuell prüfen |
| **Anpassen** | HARD-GATE nicht mehr stur bei Kleinkram — kleine Fixes selbst angehen (Vorsatz, noch nicht umgesetzt) · grösseres Abo nimmt Token-Stress |
| **Neu machen** | Mit **Design-Mockups** starten statt nur beschreiben — sobald ich ein klares Bild im Kopf habe |
| **Weglassen** | Doppelte Tracking-Ebene (`.plans/`) · Spar-Tools mit unbelegtem Nutzen |

### Rohnotizen — zukunftsgerichtete Ergänzungen (O-Ton KN)

- **Spar-Tools messbar machen:** Nutzen vieler Tools ist „noch nicht gut messbar, wie es für mich
  performt" → da will ich **zulegen und recherchieren** (statt sie nur gut gemeint einzubauen).
- **Entwicklungsumgebung evaluieren:** Alternativen zu VS Code ausprobieren/bewerten
  (genanntes Beispiel: **Ghostty / Herd**).
- **Produktiv-Robustheit (Vendor-Lock-in):** Meine Projekte laufen produktiv → **robuster machen**.
  Leitfrage: *Was, wenn z. B. fly.io ausfällt?* Ein Wechsel soll **schnell und ohne grossen
  Aufwand** möglich sein. → verbindet sich direkt mit **Schluss B** (Deployment/Resilienz).

### 9.2 — Schlussthese (Kandidat für den Schlusssatz des Fazits)

> Automatisierung, Auslagern, Vereinfachen und **Austauschbar-Machen** sind sehr wichtige Pfeiler
> eines Projekts — damit der Betrieb möglichst **wartungsarm** ist und man **schnell reagieren**
> kann. Und: Vor der Implementierung gehört eine **gute Struktur und ein Rahmen** geschaffen
> (Architektur, CI/CD, …).

### Entwurf (Ich-Stimme) — *roh, wird gekürzt*

Was nehme ich konkret mit? Behalten will ich das, was sich bewährt hat: die GitHub-Issues als
Leitsystem, die mitwachsende CLAUDE.md, den agentischen Workflow — aber mit mehr Augenmass. Vor
allem zwei Haltungen bleiben: mein Vertrauen an der Tragweite auszurichten und Dinge, bei denen es
um Geld oder Geschäftslogik geht, selbst zu prüfen. Anpassen will ich das HARD-GATE: Kleinkram gehe
ich künftig selbst an, statt jeden Ein-Zeilen-Fix durch den vollen Zyklus zu schicken. Neu dazu
kommt, dass ich beim nächsten visuellen Projekt mit Mockups starte. Und weglassen kann ich, was nur
doppelte Pflege war — die zweite Tracking-Ebene und Spar-Tools, deren Nutzen ich nie belegen konnte.

Darüber hinaus habe ich drei Dinge, die ich gezielt angehen will. Erstens den **Nutzen meiner
Tools wirklich messbar machen** — ich habe zu vieles eingebaut, ohne sagen zu können, was es bringt.
Zweitens meine **Entwicklungsumgebung evaluieren** und Alternativen zu VS Code ausprobieren.
Drittens, und das ist mir am wichtigsten, **Robustheit**: Meine Projekte laufen produktiv, und ich
will, dass ein Anbieterwechsel — etwa wenn fly.io ausfiele — schnell und ohne grossen Aufwand möglich
ist.

Der grösste Lernsatz steht für mich über allem: **Automatisieren, auslagern, vereinfachen und
austauschbar machen** sind die Pfeiler, damit ein Projekt wartungsarm bleibt und ich schnell
reagieren kann — und das beginnt nicht beim Code, sondern bei einer **guten Struktur und einem
sauberen Rahmen** (Architektur, CI/CD), die ich *vor* der Implementierung schaffe.
