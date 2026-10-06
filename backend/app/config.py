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
    moodle_sync_hours: int = 6
    # Autorise les liens ICS vers le réseau local (désactivé pour éviter qu'un utilisateur
    # se serve du serveur pour sonder le réseau de la maison).
    allow_private_ics: bool = False


settings = Settings()

if not settings.database_url.startswith("sqlite") and (
    settings.secret_key == "dev-secret-a-changer" or len(settings.secret_key) < 32
):
    raise RuntimeError("SECRET_KEY manquante ou trop courte : générer avec `openssl rand -hex 32`")
