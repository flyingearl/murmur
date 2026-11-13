"""The database connection, sessions, and the base class every model inherits from."""

from collections.abc import AsyncIterable
from datetime import datetime
from functools import lru_cache
from typing import Annotated, Any, ClassVar

from fastapi import Depends
from sqlalchemy import DateTime, MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from murmur_api.config import SettingsDep

# Predictable names for indexes and constraints, so later migrations can refer to them.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map: ClassVar[dict[Any, Any]] = {datetime: DateTime(timezone=True)}


@lru_cache
def get_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url)


async def get_session(settings: SettingsDep) -> AsyncIterable[AsyncSession]:
    engine = get_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
