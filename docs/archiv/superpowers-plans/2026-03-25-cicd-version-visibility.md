# CI/CD Version-Sichtbarkeit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deployete Version in GitHub Actions sofort sichtbar machen — im Step-Namen und als Job Summary.

**Architecture:** Zwei Änderungen am Deploy-Job in `deploy.yml`: (1) Step-Name wird dynamisch mit der Version befüllt via `needs.build.outputs.app_version` (der Build-Job setzt `APP_VERSION` via `$GITHUB_ENV` und exponiert sie als Job-Output), (2) nach dem Deploy wird ein Summary-Block in `$GITHUB_STEP_SUMMARY` geschrieben.

**Tech Stack:** GitHub Actions YAML, `$GITHUB_STEP_SUMMARY` (Markdown)

---

### Task 1: Deploy-Step umbenennen und Summary hinzufügen

**Files:**
- Modify: `.github/workflows/deploy.yml` (Deploy-Job, Step "Deploy" und neuer Step danach)

- [ ] **Step 1: Deploy-Step-Name dynamisch machen**

Den Step mit `name: Deploy` im Deploy-Job ersetzen durch:

```yaml
      - name: Deploy ${{ needs.build.outputs.app_version }} to fly.io
        run: flyctl deploy --app olivalle --image ${{ needs.build.outputs.image_sha }}
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

- [ ] **Step 2: Summary-Step einfügen**

Direkt nach dem Deploy-Step (nach dem `FLY_API_TOKEN` env-Block), vor dem "Git-Tag setzen"-Step, folgenden Step einfügen:

```yaml
      - name: Summary schreiben
        # Kein `if: success()` nötig — GitHub Actions überspringt diesen Step
        # automatisch wenn der Deploy-Step fehlschlägt.
        run: |
          echo "## Deployment erfolgreich" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| | |" >> $GITHUB_STEP_SUMMARY
          echo "|---|---|" >> $GITHUB_STEP_SUMMARY
          echo "| **Version** | ${{ needs.build.outputs.app_version }} |" >> $GITHUB_STEP_SUMMARY
          echo "| **Commit** | \`${{ github.sha }}\` |" >> $GITHUB_STEP_SUMMARY
          echo "| **Branch** | \`${{ github.ref_name }}\` |" >> $GITHUB_STEP_SUMMARY
```

Der Deploy-Job hat danach folgende Step-Reihenfolge:
1. `actions/checkout@v4`
2. `superfly/flyctl-actions/setup-flyctl@v1`
3. `Deploy ${{ needs.build.outputs.app_version }} to fly.io`
4. `Summary schreiben`
5. `Git-Tag setzen`

- [ ] **Step 3: Committen und pushen**

```bash
git add .github/workflows/deploy.yml
git commit -m "feat: Version im CI/CD Step-Namen und Job Summary anzeigen"
git push
```

- [ ] **Step 4: Verifizieren**

Nach dem Push den GitHub Actions Run öffnen:
- Im Deploy-Job trägt der Deploy-Step den Namen "Deploy v0.1.X to fly.io"
- Im Tab "Summary" des Runs erscheint die Tabelle mit Version, Commit und Branch
