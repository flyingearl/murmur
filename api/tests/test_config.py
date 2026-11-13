import pytest
from pydantic import ValidationError

from murmur_api.config import Settings


def test_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "Murmur API"
    assert settings.max_message_length == 4000


def test_reads_prefixed_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MURMUR_MAX_MESSAGE_LENGTH", "500")

    assert Settings(_env_file=None).max_message_length == 500


@pytest.mark.parametrize("value", ["0", "-1", "lots"])
def test_rejects_invalid_max_message_length(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("MURMUR_MAX_MESSAGE_LENGTH", value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
