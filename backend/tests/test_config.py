from app.core.config import Settings, get_settings


def test_settings_reads_documented_env_aliases(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://localhost:3000,http://localhost:3001")
    monkeypatch.setenv("MAP_PROVIDER", "mapmyindia")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://demo:demo@localhost:5432/demo")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.environment == "test"
    assert settings.map_provider == "mapmyindia"
    assert settings.database_url.endswith("/demo")
    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]

    get_settings.cache_clear()


def test_settings_defaults_stay_phase_one_safe():
    settings = Settings(_env_file=None)

    assert settings.google_translate_enabled is False
    assert settings.map_primary_provider == "mapmyindia"
    assert settings.database_url.startswith("postgresql+psycopg://")
