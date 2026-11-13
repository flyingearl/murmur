"""Saving and reading chat messages"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from murmur_api.models import Message


class MessageOut(BaseModel):
    """A message as the API returns it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    author: str
    body: str
    created_at: datetime


async def save_message(session: AsyncSession, author: str, body: str) -> Message:
    message = Message(author=author, body=body)
    session.add(message)
    await session.commit()
    return message


async def recent_messages(session: AsyncSession, limit: int) -> list[Message]:
    """The newest `limit` messages, oldest first (the order a chat shows them in)."""
    query = select(Message).order_by(Message.id.desc()).limit(limit)
    newest_first = await session.scalars(query)
    return list(reversed(newest_first.all()))
