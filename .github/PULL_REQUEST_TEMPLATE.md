## Beschreibung

<!-- Was ändert dieser PR? Issue-Referenz: Closes #XX -->

## Checkliste

- [ ] Tests grün (`make test`) und Lint sauber (`make lint-all`)
- [ ] Doku konsistent mit der Änderung (README, `docs/` inkl. arc42, `.env.example`)
- [ ] **Lockfile-Diff geprüft:** Änderungen an `uv.lock`/`pyproject.toml` bzw. `package-lock.json`/`package.json` bewusst gewählt — Paketname exakt richtig (kein Typosquat auf ein echtes altes Paket), Quelle plausibel
- [ ] Keine Secrets im Diff
