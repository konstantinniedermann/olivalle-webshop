# Design: OSV-Malware-Gate in CI + PR-Vorlage (Issue #179)

**Datum:** 2026-07-10
**Issue:** [#179 — [Security] dep-guard Hook + osv-scanner in CI](https://github.com/konstantinniedermann/olivalle-webshop/issues/179)
**Referenz:** Munica-Umsetzung munica#192 (Spec `docs/superpowers/specs/2026-07-10-issue192-supply-chain-guard-design.md` dort)

## Kontext & Scope

Issue #179 hat drei Schichten gegen Supply-Chain-Angriffe definiert. Zwei davon
sind bereits **global** erledigt und hier nur verifiziert, nicht neu gebaut:

- **dep-guard-Hook** (user-scope, `~/.claude/hooks/dep_guard.py`): verifiziert
  am 2026-07-10 — Block-Test aus `~/.claude/hooks/README.md` liefert exit=2,
  Hook ist in `~/.claude/settings.json` registriert.
- **CLAUDE.md-Dependencies-Regel:** steht in der gemeinsamen `../CLAUDE.md`.

Verbleibender Scope für olivalle:

1. **OSV-Malware-Gate in der CI** — fängt legitime Pakete, die *nachträglich*
   kompromittiert wurden (inkl. transitiver Dependencies via Lockfile).
2. **PR-Vorlage mit Lockfile-Diff-Review-Punkt** — fängt Typosquatting auf
   echte alte Pakete (`python-dateutils`), das weder Hook noch OSV sehen.

## Vorbedingungen (verifiziert 2026-07-10)

- `git ls-files uv.lock package-lock.json` → beide getrackt ✅
  (das war in Munica die Stolperfalle: gitignored → Gate schlug fail-closed an)
- `uv lock --check` → sauber ✅

## Entscheid: Platzierung des Gates

**Gewählt: eigener Job `osv-gate` in `deploy.yml`, `build` erhält
`needs: [test, osv-gate]`.**

Alternativen:

| Option | Bewertung |
|---|---|
| Job in `lint.yml` | Läuft auf PRs, gate't aber das Deployment **nicht** — `deploy.yml` wartet nicht auf andere Workflows. Malware auf `main` würde trotzdem deployt. |
| Eigener Workflow `osv.yml` | Gleiches Problem; zusätzlich eine Datei mehr ohne Gate-Wirkung. |
| **Job in `deploy.yml`** ✅ | Blockiert Build + Deploy hart. Entspricht der Munica-Referenz. PR-zeitige Erkennung deckt der Lockfile-Diff-Punkt der PR-Vorlage (menschlicher Review) ab. |

Duplikation des Scan-Steps in `lint.yml` (für PR-Feedback) wird bewusst
weggelassen (DRY/KISS) — der Angriffsfall „Malware im Lockfile" wird spätestens
vor dem Deploy hart gestoppt.

## Komponenten

### 1. `scripts/ci/osv_malware_gate.py`

Logik 1:1 aus `../Munica/scripts/ci/osv_malware_gate.py` übernommen.
Nur der Docstring-Kopf wird angepasst (Issue #179, Hinweis: kanonische Quelle
und Weiterentwicklung in Munica). Eigenschaften:

- Bricht **nur** bei OSV-Einträgen mit Prefix `MAL-` (OpenSSF Malicious
  Packages) — geprüft in `id` **und** `aliases` (Malware kann als GHSA-ID mit
  MAL-Alias gemeldet werden). Normale Vulnerabilities brechen den Build nicht
  (sonst wäre die CI ab Tag 1 dauerrot — Erkenntnis 1 aus Munica).
- Fail closed: fehlende Datei, korruptes JSON und fehlender `results`-Key
  (Format-Drift bei künftigem Versions-Bump) → Exit ≠ 0.
- stdlib-only, ökosystem-agnostisch (PyPI + npm im selben Report).

### 2. `tests/test_osv_malware_gate.py`

Die 11 pytest-Tests aus Munica mitkopiert (Header-Hinweis auf kanonische
Quelle). Sie laufen in der bestehenden Test-Suite mit und schützen gegen
lokale Abweichungen vom Munica-Original.

### 3. `deploy.yml` — Job `osv-gate`

```yaml
osv-gate:
  name: OSV Malware Gate
  runs-on: ubuntu-latest
  permissions:
    contents: read        # Least Privilege: Job führt ein fremdes Binary aus
  steps:
    - uses: actions/checkout@<sha>  # v7.0.0 (gleicher Pin wie bestehende Jobs)
    - name: OSV malware scan (uv.lock + package-lock.json)
      run: |
        curl -sSfL -o /tmp/osv-scanner \
          https://github.com/google/osv-scanner/releases/download/v2.4.0/osv-scanner_linux_amd64
        chmod +x /tmp/osv-scanner
        echo "15314940c10d26af9c6649f150b8a47c1262e8fc7e17b1d1029b0e479e8ed8a0  /tmp/osv-scanner" | sha256sum -c -
        ec=0
        /tmp/osv-scanner scan --lockfile=uv.lock --lockfile=package-lock.json \
          --format json > /tmp/osv.json || ec=$?
        if [ "$ec" -gt 1 ]; then
          echo "osv-scanner fehlgeschlagen (exit $ec)"; exit "$ec"
        fi
        python3 scripts/ci/osv_malware_gate.py /tmp/osv.json
```

- **Version gepinnt (v2.4.0) UND sha256-verifiziert** — ein Tag-Pin allein
  reicht nicht, Release-Assets sind für einen bestehenden Tag austauschbar.
  Hash statisch eingebettet (aus offizieller `osv-scanner_SHA256SUMS` v2.4.0,
  kreuzverifiziert in munica#192).
- **Exit-Code-Muster:** exit 1 = „Findings vorhanden" (normal, wird vom Gate
  gefiltert); > 1 = echter Scanner-Fehler → fail closed.
- **Beide Lockfiles in einem Aufruf** → ein Report → ein Gate-Aufruf.
- `build` bekommt `needs: [test, osv-gate]` — ohne grünes Gate kein Image,
  kein Deploy.

### 4. `.github/PULL_REQUEST_TEMPLATE.md`

Vorlage aus Munica, an olivalle angepasst:

- Tests/Lint: `make test` bzw. `make lint-all` (kanonische Einstiegspunkte)
- Doku-Punkt: README, arc42, `docs/` (MkDocs-Site)
- **Lockfile-Diff-Punkt nennt beide Lockfiles:** `uv.lock`/`pyproject.toml`
  **und** `package-lock.json`/`package.json`
- Keine Secrets im Diff

### 5. Doku-Abgleich

- `docs/security.md`: Abschnitt Supply-Chain-Schutz (drei Schichten: Hook,
  OSV-Gate, Lockfile-Diff-Review — mit den jeweiligen Grenzen)
- `docs/ci-cd-und-versionierung.md`: neuer Job in der Deploy-Pipeline

## Verifikation vor dem Merge

Gate lokal gegen beide **echten** Lockfiles laufen lassen:
`osv-scanner_darwin_arm64` v2.4.0 herunterladen, Hash gegen offizielle
`osv-scanner_SHA256SUMS` v2.4.0 verifizieren, Scan + Gate ausführen —
erwartet: Exit 0, „keine MAL-Eintraege". Damit wird die CI nicht blind rot.

## Testing

- 11 mitkopierte pytest-Tests (Unit + CLI-E2E, inkl. fail-closed-Fälle)
- Lokaler End-to-End-Lauf gegen echte Lockfiles (siehe oben)
- `actionlint`/Review des Workflow-Diffs; CI-Lauf auf dem PR-Branch zeigt
  Lint grün, der Gate-Job selbst läuft erst nach Merge (deploy.yml = push main)

## Nicht abgedeckt (unverändert aus dem Issue)

- Typosquatting auf echte alte Pakete → nur Lockfile-Diff im Review (Punkt 4)
- Der Hook fängt halluzinierte/frische Pakete, das Gate nachträglich
  kompromittierte — alle drei Schichten nötig.
