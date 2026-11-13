"""Database tables, written as Python classes."""

from datetime import datetime

from sqlalchemy import BigInteger, Identity, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from murmur_api.db import Base


class Message(Base):
    """A chat message. Only messages sent after this table was created are stored."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    author: Mapped[str] = mapped_column(String(50))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
