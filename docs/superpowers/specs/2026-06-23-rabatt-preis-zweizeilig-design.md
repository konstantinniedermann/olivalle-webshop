# Design-Spec: Preis-Block zweizeilig (Rabatt-Eindeutigkeit)

**Datum:** 2026-06-23
**Issue:** Folge aus Produktkarten-Arbeit (#135 / offen #139, #140)
**Status:** Genehmigt, bereit für Plan-Phase

## Problem

Auf der Produktseite ist bei einem Aktions-Gebinde (z.B. Olivenöl 750ml) der
Rabatt nicht eindeutig gekennzeichnet. Aktuell stehen Alt-Preis, neuer Preis und
`−17%`-Chip in **einer** `flex`-Zeile mit `flex-wrap`:

```
[~~CHF 18.00~~] [CHF 15.00] [−17%]
```

Bei schmaler Spalte (Mobile, 4-Spalten-Grid) bricht diese Zeile **unkontrolliert**
um — der durchgestrichene Alt-Preis landet oben, darunter `CHF 15.00 −17%`. Das
`−17%`-Chip klebt dann am **neuen** Preis und liest sich als „nochmal 17% Rabatt
auf 15 CHF". Der Kunde könnte einen weiteren Abzug erwarten.

## Ziel

Das `−17%` eindeutig dem **Abzug vom Alt-Preis** zuordnen, sodass der neue Preis
sichtbar das **Resultat** der Rechnung ist — ohne die Zeile zu überladen.

## Lösung

Den Preis-Block bewusst zweizeilig strukturieren (gewählte Variante „Schlicht"):

```
Zeile 1:  ~~CHF 18.00~~  [−17%]      ← klein/grau + roter Chip, eine baseline
Zeile 2:  CHF 15.00                  ← text-xl, fett — das Resultat
```

Das `−17%` steht neben dem Alt-Preis („CHF 18.00, davon 17% Rabatt"), der neue
Preis darunter ist das Ergebnis. Der Umbruch ist jetzt **bewusst gesetzt** statt
dem Zufall der Spaltenbreite überlassen.

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `templates/produkte.html` (Z. 38–47) | Preis-Block des Aktions-Falls umstrukturieren |

**Kein Backend-Touch:** Die Daten `original_preis`, `preis`, `prozent` werden
bereits von `app/services/aktions_service.py` geliefert und im Template genutzt.

## Konkrete Template-Änderung

**Vorher (Z. 38–47):**
```html
<div class="mt-4">
    <div class="flex items-baseline flex-wrap gap-2 mb-3">
        {% if produkt.ist_aktion %}
        <span class="text-stone-400 line-through text-sm">CHF {{ "%.2f"|format(produkt.original_preis) }}</span>
        <span class="text-xl font-bold">CHF {{ "%.2f"|format(produkt.preis) }}</span>
        {% if produkt.prozent > 0 %}<span class="bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded">−{{ produkt.prozent }}%</span>{% endif %}
        {% else %}
        <span class="text-xl font-bold">CHF {{ "%.2f"|format(produkt.preis) }}</span>
        {% endif %}
    </div>
```

**Nachher (Konzept — finale Klassen in Plan/Implementierung):**
```html
<div class="mt-4">
    {% if produkt.ist_aktion %}
    <div class="flex items-baseline gap-2">
        <span class="text-stone-400 line-through text-sm">CHF {{ "%.2f"|format(produkt.original_preis) }}</span>
        {% if produkt.prozent > 0 %}<span class="bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded">−{{ produkt.prozent }}%</span>{% endif %}
    </div>
    <div class="text-xl font-bold mb-3">CHF {{ "%.2f"|format(produkt.preis) }}</div>
    {% else %}
    <div class="text-xl font-bold mb-3">CHF {{ "%.2f"|format(produkt.preis) }}</div>
    {% endif %}
```

- Obere Zeile: nur Alt-Preis + `−17%`-Chip, `flex items-baseline gap-2` (kein
  `flex-wrap` mehr nötig — die Zeile ist jetzt kurz genug).
- Untere Zeile: neuer Preis `text-xl font-bold`, eigener Block.
- Nicht-Aktions-Fall: unverändert nur der eine fette Preis.
- `RABATT`-Badge (Z. 26–28) und `aktionstext`-Badge (Z. 35–37) bleiben unangetastet.

## Unberührt

- Backend / Aktions-Service / DB-Schema
- `RABATT`-Badge oben rechts
- optionaler `aktionstext`-Badge
- „In den Warenkorb"-Button und dessen `data-*`-Attribute

## Mitzupflegen

- `tests/` — falls ein Test die Reihenfolge/Struktur des Preis-Blocks prüft,
  anpassen (Aktions-Fall: Alt-Preis + Chip zusammen, neuer Preis separat).
- `docs/user-stories-testplan.md` — gegenchecken (Issue #140 Testplan-Drift),
  ggf. den manuellen Prüfschritt zur Rabatt-Anzeige aktualisieren.

## Verifikation

1. App lokal rendern, Produktseite öffnen.
2. Am Aktions-Gebinde (750ml) prüfen: Alt-Preis + `−17%` oben zusammen, neuer
   Preis darunter als Resultat.
3. Schmale Spalte (Mobile / 4-Spalten-Grid) prüfen: kein unkontrollierter
   Umbruch mehr.
4. Nicht-Aktions-Gebinde prüfen: unverändert nur ein fetter Preis.
5. Tests grün, Lint sauber.
