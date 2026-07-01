"""
Tests for application configuration validation.
"""
import pytest
from unittest.mock import patch

from app.config import Config


def _make_config(**overrides) -> Config:
    """Return a Config instance with env vars set via overrides."""
    env = {
        "APP_ENV": "development",
        "DATABASE_URL": "sqlite:///test.db",
        "TELEGRAM_BOT_TOKEN": "",
        "ALPHA_VANTAGE_API_KEY": "",
        "SESSION_SECRET": "",
        **overrides,
    }
    with patch.dict("os.environ", env, clear=False):
        return Config()


class TestConfigValidation:
    def test_missing_session_secret_raises(self):
        cfg = _make_config(SESSION_SECRET="")
        with pytest.raises(ValueError, match="SESSION_SECRET"):
            cfg.validate()

    @pytest.mark.parametrize(
        "bad_secret",
        ["change-me", "changeme", "secret", "password"],
    )
    def test_insecure_session_secret_raises(self, bad_secret):
        cfg = _make_config(SESSION_SECRET=bad_secret)
        with pytest.raises(ValueError, match="insecure default"):
            cfg.validate()

    def test_valid_session_secret_passes_in_development(self):
        cfg = _make_config(SESSION_SECRET="a-strong-random-secret-123!")
        cfg.validate()  # should not raise

    def test_production_requires_bot_token(self):
        cfg = _make_config(
            APP_ENV="production",
            SESSION_SECRET="a-strong-random-secret-123!",
            TELEGRAM_BOT_TOKEN="",
            ALPHA_VANTAGE_API_KEY="valid-key",
        )
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            cfg.validate()

    def test_production_requires_api_key(self):
        cfg = _make_config(
            APP_ENV="production",
            SESSION_SECRET="a-strong-random-secret-123!",
            TELEGRAM_BOT_TOKEN="valid-token",
            ALPHA_VANTAGE_API_KEY="",
        )
        with pytest.raises(ValueError, match="ALPHA_VANTAGE_API_KEY"):
            cfg.validate()

    def test_production_valid_config_passes(self):
        cfg = _make_config(
            APP_ENV="production",
            SESSION_SECRET="a-strong-random-secret-123!",
            TELEGRAM_BOT_TOKEN="valid-token",
            ALPHA_VANTAGE_API_KEY="valid-key",
        )
        cfg.validate()  # should not raise

    def test_multiple_errors_reported_together(self):
        cfg = _make_config(SESSION_SECRET="")
        with pytest.raises(ValueError, match=r"1 error"):
            cfg.validate()
