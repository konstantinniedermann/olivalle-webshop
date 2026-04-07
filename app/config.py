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

    app_version: str = "dev"

    # Hinter fly.io-Proxy: Fly-Client-IP / X-Forwarded-For vertrauen.
    # In Tests/lokal abschalten, damit Header nicht gespooft werden können.
    trust_proxy_headers: bool = True


settings = Settings()
