from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env"}

    secret_key: str = "change-me"
    base_url: str = "http://localhost:8000"

    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    brevo_api_key: str = ""

    qr_iban: str = ""
    qr_name: str = ""
    qr_address: str = ""
    qr_zip: str = ""
    qr_city: str = ""

    database_path: str = "olivalle.db"

    admin_credentials: str = ""  # "label:bcrypt_hash,label:bcrypt_hash"
    admin_session_max_age: int = 86400  # 24h
    cookie_secure: bool = True  # in dev via .env auf False setzen

    app_version: str = "dev"

    # Hinter fly.io-Proxy: Fly-Client-IP / X-Forwarded-For vertrauen.
    # In Tests/lokal abschalten, damit Header nicht gespooft werden können.
    trust_proxy_headers: bool = True


settings = Settings()


# Secrets/Konfig-Felder, die in Produktion gesetzt sein MUESSEN. Fehlen sie,
# laeuft die App sonst mit unsicheren Defaults (secret_key) oder scheitert erst
# spaet zur Laufzeit (leere Stripe-/Brevo-Keys) — beides schwer zu diagnostizieren.
_PFLICHT_SECRETS = (
    "stripe_secret_key",
    "stripe_webhook_secret",
    "brevo_api_key",
    "admin_credentials",
    "qr_iban",
)


def pruefe_produktionskonfig(s: Settings | None = None) -> list[str]:
    """Prueft die Produktionskonfiguration und gibt eine Liste von Problemen zurueck.

    Leere Liste bedeutet: alles gesetzt. Wird beim Container-Start aufgerufen
    (siehe entrypoint.sh); lokal/in Tests wird sie nicht ausgefuehrt.
    """
    s = s or settings
    probleme: list[str] = []
    if not s.secret_key or s.secret_key == "change-me":
        probleme.append("SECRET_KEY ist nicht gesetzt (Default 'change-me' aktiv)")
    if s.base_url.startswith("http://localhost"):
        probleme.append("BASE_URL zeigt auf localhost (Stripe-Redirects brechen)")
    for feld in _PFLICHT_SECRETS:
        if not getattr(s, feld):
            probleme.append(f"{feld.upper()} ist leer")
    return probleme


def _cli_fail_fast() -> None:
    """Entrypoint-Hook: bricht den Start ab, wenn Pflicht-Konfig fehlt."""
    import sys

    probleme = pruefe_produktionskonfig()
    if probleme:
        print("[config] Produktionskonfiguration unvollstaendig:", file=sys.stderr)
        for p in probleme:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)
    print("[config] Produktionskonfiguration ok.")


if __name__ == "__main__":
    _cli_fail_fast()
