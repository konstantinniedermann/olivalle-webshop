# Design-Entscheidungen & Specs

Dieses Projekt entstand im Rahmen des CAS AI-Supported Software Engineering (FFHS) und folgt durchgängig einem **agentischen Workflow** (umgesetzt mit dem [superpowers](https://github.com/obra/superpowers)-Plugin für Claude Code). Jede Funktion und jeder grössere Fix durchläuft dieselben Phasen:

1. **Brainstorming** — Intent, Anforderungen und Lösungsvarianten klären.
2. **Spec** — die validierte Lösung als Design-Dokument festhalten.
3. **Plan** — den Spec in konkrete, abhakbare Implementierungsschritte zerlegen.
4. **Test-Driven Development** — Tests zuerst, dann Implementierung.
5. **Code-Review** — vor dem Merge gegen die Architektur-Checkliste prüfen.

Die dabei entstehenden **Specs (Design-Dokumente)** und **Plans (Implementierungspläne)** werden als rohe Arbeitsartefakte mit ins Repository eingecheckt. Sie dokumentieren den *Verlauf* einer Entscheidung — das „Warum" hinter jedem Feature — und ergänzen damit die kuratierte Doku.

!!! note "Abgrenzung zur kuratierten Doku"
    Die **finalen, kuratierten** Architektur-Entscheidungen stehen im [ADR-Index](adr-index.md) und in [arc42](arc42.md). Die Specs und Plans unten sind das **rohe Prozess-Material** dahinter — nützlich, um den Entstehungsweg nachzuvollziehen, aber nicht als Hochglanz-Doku gedacht.

## Wo die Artefakte liegen

Die Dateien liegen im Repository unter `docs/superpowers/` und sind bewusst **nicht** als einzelne Seiten in diese Doku-Site aufgenommen (sie würden die Navigation mit Rohartefakten überladen). Stattdessen wird hier direkt auf die jeweiligen GitHub-Verzeichnisse verlinkt:

- **[Specs / Design-Dokumente →](https://github.com/konstantinniedermann/olivalle-webshop/tree/main/docs/superpowers/specs)** — je ein Design-Dokument pro Feature/Fix.
- **[Plans / Implementierungspläne →](https://github.com/konstantinniedermann/olivalle-webshop/tree/main/docs/superpowers/plans)** — die zugehörigen Schritt-für-Schritt-Pläne.

## Namenskonvention

Die Dateien sind nach Datum und Thema benannt, sodass Spec und Plan eines Vorhabens zusammengehören:

- Spec: `YYYY-MM-DD-<thema>-design.md`
- Plan: `YYYY-MM-DD-<thema>.md`

Beispiel: Der Spec `2026-06-24-doku-luecken-144-design.md` und der Plan `2026-06-24-doku-luecken-144.md` gehören zum selben Vorhaben (Schliessen der Doku-Lücken aus dem Vollständigkeits-Audit).
