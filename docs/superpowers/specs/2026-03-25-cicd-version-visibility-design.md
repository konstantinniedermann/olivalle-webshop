# Design: Version-Sichtbarkeit in GitHub Actions

**Datum:** 2026-03-25
**Status:** Approved

## Problem

Die deployete Version ist im GitHub Actions Run nicht sofort sichtbar. Man muss den Deploy-Step aufklappen und durch das Log scrollen um `APP_VERSION` zu finden.

## Ziel

Version auf zwei Ebenen sichtbar machen:
1. Im **Step-Namen** — direkt in der Job-Übersicht
2. Als **Job Summary** — Markdown-Tabelle unter dem Run, ohne Log-Scrollen

## Änderungen

### deploy.yml — Deploy-Job

**Step-Name** (dynamisch via Job-Output):
```yaml
- name: Deploy ${{ needs.build.outputs.app_version }} to fly.io
  run: flyctl deploy --app olivalle --image ${{ needs.build.outputs.image_sha }}
  env:
    FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**Neuer Summary-Step** (nach Deploy, vor Git-Tag):
```yaml
- name: Summary schreiben
  run: |
    echo "## Deployment erfolgreich" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "| | |" >> $GITHUB_STEP_SUMMARY
    echo "|---|---|" >> $GITHUB_STEP_SUMMARY
    echo "| **Version** | ${{ needs.build.outputs.app_version }} |" >> $GITHUB_STEP_SUMMARY
    echo "| **Commit** | \`${{ github.sha }}\` |" >> $GITHUB_STEP_SUMMARY
    echo "| **Branch** | \`${{ github.ref_name }}\` |" >> $GITHUB_STEP_SUMMARY
```

## Nicht im Scope

- GitHub Releases (zu viel Overhead für dieses Projekt)
- Slack/E-Mail-Notifications
- Änderungen am Build- oder Test-Job
