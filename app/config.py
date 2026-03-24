from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env"}

    secret_key: str = "change-me"
    base_url: str = "http://localhost:8000"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    resend_api_key: str = ""

    qr_iban: str = ""
    qr_name: str = ""
    qr_address: str = ""
    qr_zip: str = ""
    qr_city: str = ""

    database_path: str = "olivalle.db"


settings = Settings()
