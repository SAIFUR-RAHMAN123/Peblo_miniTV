from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://peblo:peblo@localhost:5432/peblo_tv"

    storage_backend: str = "local"
    storage_local_root: str = "./storage_data"
    storage_public_base_url: str = "http://localhost:8000/media"

    r2_bucket: str = ""
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_public_base_url: str = ""

    editor_api_key: str = "editor-dev-key"
    admin_api_key: str = "admin-dev-key"

    artwork_max_kb: int = 200
    artwork_dimension_tolerance_pct: float = 10.0
    artwork_aspect_tolerance_pct: float = 2.0

    catalog_publish_dir: str = "catalog"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]


@lru_cache
def get_settings() -> Settings:
    return Settings()