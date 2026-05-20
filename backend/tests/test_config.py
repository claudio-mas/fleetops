from app.core.config import Settings


def test_settings_loads_from_env() -> None:
    s = Settings()
    assert s.environment == "test"
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.redis_url.startswith("redis://")
    assert len(s.secret_key) >= 16


def test_settings_defaults_log_level_to_info() -> None:
    s = Settings()
    assert s.log_level == "INFO"
