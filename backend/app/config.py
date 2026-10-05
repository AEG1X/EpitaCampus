from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SQLite par défaut pour développer sans Docker ; PostgreSQL en production.
    database_url: str = "sqlite:///./dev.db"
    secret_key: str = "dev-secret-a-changer"
    data_dir: Path = Path("./data")
    # Inscription libre : utile plus tard pour le multi-utilisateur.
    # Le tout premier compte peut toujours être créé.
    allow_signup: bool = False
    token_days: int = 30
    cookie_secure: bool = False
    calendar_sync_minutes: int = 30


settings = Settings()
