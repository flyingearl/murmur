"""Murmur API: the application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import FastAPI, Path, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from murmur_api.config import SettingsDep, get_settings
from murmur_api.db import SessionDep, get_engine
from murmur_api.messages import MessageOut, recent_messages, save_message

HISTORY_ON_JOIN = 50


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await get_engine(get_settings().database_url).dispose()


app = FastAPI(title=get_settings().app_name, version="0.1.0", lifespan=lifespan)


class Health(BaseModel):
    status: str
    time: datetime


@app.get("/health")
async def health() -> Health:
    return Health(status="ok", time=datetime.now(UTC))


@app.get("/messages")
async def list_messages(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[MessageOut]:
    messages = await recent_messages(session, limit)
    return [MessageOut.model_validate(message) for message in messages]


class ConnectionManager:
    """Tracks open WebSocket connections in this process's memory.

    Nothing is saved, and it only works with one server process.
    """

    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)

    async def broadcast(self, text: str) -> None:
        for connection in list(self.active):
            try:
                await connection.send_text(text)
            except Exception:  # noqa: BLE001 - a dead socket must not break the room
                await self.disconnect(connection)


manager = ConnectionManager()


@app.websocket("/ws/{name}")
async def chat(
    websocket: WebSocket,
    name: Annotated[str, Path(min_length=1, max_length=50)],
    settings: SettingsDep,
    session: SessionDep,
) -> None:
    await manager.connect(websocket)
    for message in await recent_messages(session, HISTORY_ON_JOIN):
        await websocket.send_text(f"{message.author}: {message.body}")
    await manager.broadcast(f"{name} joined")
    try:
        while True:
            text = await websocket.receive_text()
            if len(text) > settings.max_message_length:
                await websocket.send_text(
                    f"Not sent . Messages can be up to {settings.max_message_length} characters"
                )
                continue
            await save_message(session, author=name, body=text)
            await manager.broadcast(f"{name}: {text}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        await manager.broadcast(f"{name} left")
