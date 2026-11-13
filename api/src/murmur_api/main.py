"""Murmur API: the application entry point."""

from datetime import UTC, datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

app = FastAPI(title="Murmur API", version="0.1.0")


class Health(BaseModel):
    status: str
    time: datetime


@app.get("/health")
async def health() -> Health:
    return Health(status="ok", time=datetime.now(UTC))


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
            except Exception:   # noqa: BLE001 - a dead socket must not break the room
                await self.disconnect(connection)


manager = ConnectionManager()


@app.websocket("/ws/{name}")
async def chat(websocket: WebSocket, name: str) -> None:
    await manager.connect(websocket)
    await manager.broadcast(f"{name} joined")
    try:
        while True:
            text = await websocket.receive_text()
            await manager.broadcast(f"{name}: {text}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        await manager.broadcast(f"{name} left")
