# Stripe Account einrichten — Anleitung

Diese Anleitung beschreibt die Schritte, um den Stripe-Account für den Olivalle Webshop einzurichten. Der Account gehört dem Geschäftsinhaber, da Stripe Auszahlungen auf sein Bankkonto macht und seine Daten für die Verifizierung braucht.

---

## Schritt 1: Account erstellen

1. Geh auf **https://dashboard.stripe.com/register**
2. Gib deine E-Mail-Adresse ein und wähle ein sicheres Passwort
3. Bestätige deine E-Mail-Adresse (Link im Posteingang)

> **Was passiert hier?** Stripe ist unser Zahlungsanbieter. Über Stripe können Kunden im Webshop mit Kreditkarte und Twint bezahlen. Stripe überweist das Geld dann auf dein Bankkonto.

---

## Schritt 2: Geschäftsdaten hinterlegen

Nach dem Login fragt Stripe nach deinen Geschäftsdaten:

1. **Unternehmenstyp:** Einzelunternehmen
2. **Land:** Schweiz
3. **Persönliche Angaben:** Name, Adresse, Geburtsdatum
4. **Bankverbindung:** IBAN deines Geschäftskontos (für Auszahlungen)

> **Was passiert hier?** Stripe ist gesetzlich verpflichtet, die Identität der Geschäftsinhaber zu prüfen (Know Your Customer). Deine Daten werden sicher bei Stripe gespeichert und nicht im Webshop.

---

## Schritt 3: Twint aktivieren

1. Geh im Dashboard auf **Einstellungen → Zahlungsmethoden** (oder: Settings → Payment methods)
2. Suche nach **Twint** und aktiviere es
3. Kreditkarten (Visa, Mastercard) sind standardmässig aktiv

> **Was passiert hier?** Twint ist in der Schweiz die beliebteste Zahlungsmethode. Stripe unterstützt Twint nativ — wir müssen es nur einschalten.

---

## Schritt 4: Test-API-Keys kopieren

1. Geh im Dashboard auf **Entwickler → API-Schlüssel** (oder: Developers → API keys)
2. Stelle sicher, dass oben **"Testmodus"** aktiv ist (Schalter)
3. Kopiere diese zwei Werte und schick sie mir:

   - **Veröffentlichbarer Schlüssel** (beginnt mit `pk_test_...`)
   - **Geheimer Schlüssel** (beginnt mit `sk_test_...`)

> **Was passiert hier?** Im Testmodus können wir den Webshop entwickeln und testen, ohne echtes Geld zu bewegen. Kein Kunde wird belastet. Erst wenn alles funktioniert, schalten wir auf den Live-Modus um.

> **Sicherheitshinweis:** Den geheimen Schlüssel (`sk_test_...`) niemals per unverschlüsselter E-Mail schicken. Am besten persönlich, per Signal oder über einen Passwort-Manager teilen.

---

## Schritt 5: Mich als Team-Member einladen (optional)

1. Geh auf **Einstellungen → Team** (oder: Settings → Team)
2. Klicke auf **Mitglied einladen**
3. Gib meine E-Mail-Adresse ein und wähle die Rolle **Entwickler**

> **Was passiert hier?** Damit kann ich selbst ins Dashboard schauen, ohne deine Login-Daten zu brauchen. Du bleibst Owner, ich habe nur Entwickler-Zugriff.

---

## Zusammenfassung

| Was | Wer | Dauer |
|---|---|---|
| Account erstellen | Du (Geschäftsinhaber) | 5 Min |
| Geschäftsdaten eingeben | Du | 10 Min |
| Twint aktivieren | Du | 2 Min |
| Test-API-Keys an mich schicken | Du | 2 Min |
| Mich einladen (optional) | Du | 2 Min |

Bei Fragen melde dich einfach bei mir.
