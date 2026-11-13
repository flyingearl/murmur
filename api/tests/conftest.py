"""Shared pytest fixtures. pytest loads this file automatically."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from murmur_api.config import Settings, get_settings
from murmur_api.main import app


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, max_message_length=20)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
