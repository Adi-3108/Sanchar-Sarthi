from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RAW_DATASET_NAME = "Astram event data_anonymized - Astram event data_anonymizedb40ac87 (1).csv"
LOCAL_SQLITE_DB_NAME = "eventflow_local.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="Sanchar Sarthi")
    environment: str = Field(
        default="local",
        pattern="^(local|test|production)$",
        validation_alias="APP_ENV",
    )
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/eventflow",
        validation_alias="DATABASE_URL",
    )
    raw_data_path: str = Field(
        default=DEFAULT_RAW_DATASET_NAME,
        validation_alias="RAW_DATA_PATH",
    )
    frontend_origin: str = Field(
        default="http://localhost:3000",
        validation_alias="FRONTEND_ORIGIN",
    )
    map_provider: str = Field(
        default="mapmyindia",
        pattern="^(osm|mapmyindia)$",
        validation_alias="MAP_PROVIDER",
    )
    map_primary_provider: str = Field(
        default="mapmyindia",
        validation_alias="MAP_PRIMARY_PROVIDER",
    )
    map_fallback_provider: str = Field(
        default="osm",
        validation_alias="MAP_FALLBACK_PROVIDER",
    )
    mapmyindia_api_key: str | None = Field(default=None, validation_alias="MAPMYINDIA_API_KEY")
    mapmyindia_rest_key: str | None = Field(default=None, validation_alias="MAPMYINDIA_REST_KEY")
    mapmyindia_credit_budget_inr: int = Field(
        default=1000,
        validation_alias="MAPMYINDIA_CREDIT_BUDGET_INR",
    )
    mapmyindia_daily_soft_limit_inr: int = Field(
        default=150,
        validation_alias="MAPMYINDIA_DAILY_SOFT_LIMIT_INR",
    )
    mapmyindia_enable_routing: bool = Field(
        default=True,
        validation_alias="MAPMYINDIA_ENABLE_ROUTING",
    )
    mapmyindia_enable_geocoding: bool = Field(
        default=True,
        validation_alias="MAPMYINDIA_ENABLE_GEOCODING",
    )
    mapmyindia_enable_distance_matrix: bool = Field(
        default=False,
        validation_alias="MAPMYINDIA_ENABLE_DISTANCE_MATRIX",
    )
    map_fallback_on_error: bool = Field(
        default=True,
        validation_alias="MAP_FALLBACK_ON_ERROR",
    )
    open_meteo_enabled: bool = Field(default=True, validation_alias="OPEN_METEO_ENABLED")
    google_translate_enabled: bool = Field(
        default=False,
        validation_alias="GOOGLE_TRANSLATE_ENABLED",
    )
    google_translate_provider: str = Field(
        default="google",
        validation_alias="GOOGLE_TRANSLATE_PROVIDER",
    )
    google_translate_target_language: str = Field(
        default="en",
        validation_alias="GOOGLE_TRANSLATE_TARGET_LANGUAGE",
    )
    google_translate_daily_char_limit: int = Field(
        default=50000,
        validation_alias="GOOGLE_TRANSLATE_DAILY_CHAR_LIMIT",
    )
    google_translate_monthly_char_limit: int = Field(
        default=500000,
        validation_alias="GOOGLE_TRANSLATE_MONTHLY_CHAR_LIMIT",
    )
    google_translate_fail_open: bool = Field(
        default=True,
        validation_alias="GOOGLE_TRANSLATE_FAIL_OPEN",
    )
    google_cloud_project_id: str | None = Field(
        default=None,
        validation_alias="GOOGLE_CLOUD_PROJECT_ID",
    )
    google_application_credentials_json: str | None = Field(
        default=None,
        validation_alias="GOOGLE_APPLICATION_CREDENTIALS_JSON",
    )
    firebase_project_id: str | None = Field(default=None, validation_alias="FIREBASE_PROJECT_ID")
    firebase_client_email: str | None = Field(default=None, validation_alias="FIREBASE_CLIENT_EMAIL")
    firebase_private_key: str | None = Field(default=None, validation_alias="FIREBASE_PRIVATE_KEY")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]

    @property
    def resolved_raw_data_path(self) -> Path:
        configured_path = Path(self.raw_data_path)
        if configured_path.is_absolute():
            return configured_path

        candidates = (
            Path.cwd() / configured_path,
            PROJECT_ROOT / configured_path,
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

        return (PROJECT_ROOT / configured_path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()


def resolve_database_url(database_url: str | None = None) -> str:
    if database_url:
        return database_url

    settings = get_settings()
    if "database_url" in settings.model_fields_set:
        return settings.database_url

    return f"sqlite:///{(PROJECT_ROOT / LOCAL_SQLITE_DB_NAME).as_posix()}"
