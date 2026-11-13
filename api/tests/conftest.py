"""Shared pytest fixtures. pytest loads this file automatically."""

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from murmur_api.config import Settings, get_settings
from murmur_api.db import Base, get_session
from murmur_api.main import app

API_DIR = Path(__file__).parent.parent

TEST_DATABASE_URL = os.environ.get(
    "MURMUR_TEST_DATABASE_URL",
    "postgresql+psycopg://murmur:murmur@localhost:5433/murmur_test",
)

# NullPool: open a fresh connection every time instead of keeping a pool. Each TestClient
# runs the app in its own event loop, and a pooled connection can't move between loops.
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Bring the test database up to the latest migration, once per test run."""
    config = Config(toml_file=API_DIR / "pyproject.toml")
    config.attributes["database_url"] = TEST_DATABASE_URL
    command.upgrade(config, "head")


@pytest.fixture
def clean_database() -> None:
    """Empty every table before the test, so no test sees another test's rows."""
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    engine = create_engine(TEST_DATABASE_URL, poolclass=NullPool)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    engine.dispose()


async def override_get_session() -> AsyncIterator[AsyncSession]:
    """Stands in for murmur_api.db.get_session, using the test database."""
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def session(clean_database: None) -> AsyncIterator[AsyncSession]:
    """A session for tests that call database code directly, without the API."""
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, max_message_length=20, database_url=TEST_DATABASE_URL)


@pytest.fixture
def client(settings: Settings, clean_database: None) -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
