"""Murmur API: the application entry point."""

from datetime import UTC, datetime

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Murmur API", version="0.1.0")


class Health(BaseModel):
    status: str
    time: datetime


@app.get("/health")
async def health() -> Health:
    return Health(status="ok", time=datetime.now(UTC))