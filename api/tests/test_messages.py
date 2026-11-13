import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from murmur_api.messages import recent_messages, save_message

pytestmark = pytest.mark.anyio


async def test_save_message_fills_in_id_and_time(session: AsyncSession) -> None:
    message = await save_message(session, author="ada", body="hello")

    assert message.id == 1
    assert message.created_at is not None


async def test_recent_messages_are_the_newest_in_chat_order(session: AsyncSession) -> None:
    for body in ["one", "two", "three"]:
        await save_message(session, author="ada", body=body)

    message = await recent_messages(session, limit=2)

    assert [message.body for message in message] == ["two", "three"]
