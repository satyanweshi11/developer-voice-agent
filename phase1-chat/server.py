import asyncio
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

MAX_MESSAGE_LENGTH = 2000
RATE_LIMIT_MESSAGES = 10
RATE_LIMIT_WINDOW_SECONDS = 5.0

_configured_origins = {
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
}
ALLOWED_DEV_HOSTS = {"localhost", "127.0.0.1"}


def is_origin_allowed(origin: str | None) -> bool:
    if not origin:
        return False
    if _configured_origins:
        return origin in _configured_origins
    return urlparse(origin).hostname in ALLOWED_DEV_HOSTS


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        client_id = str(uuid4())

        async with self.lock:
            self.connections[client_id] = websocket

        print(f"Client connected: {client_id}")
        return client_id

    async def disconnect(self, client_id: str) -> None:
        async with self.lock:
            self.connections.pop(client_id, None)

        print(f"Client disconnected: {client_id}")

    async def broadcast(self, message: dict) -> None:
        async with self.lock:
            clients = list(self.connections.items())

        results = await asyncio.gather(
            *[websocket.send_json(message) for _, websocket in clients],
            return_exceptions=True,
        )

        for (client_id, _), result in zip(clients, results):
            if isinstance(result, Exception):
                await self.disconnect(client_id)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Developer Voice Agent server starting...")
    yield
    print("Developer Voice Agent server stopping...")


app = FastAPI(
    title="Developer Voice Agent",
    lifespan=lifespan,
)


@app.get("/")
async def home():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if not is_origin_allowed(websocket.headers.get("origin")):
        await websocket.close(code=1008)
        return

    client_id = await manager.connect(websocket)
    recent_timestamps: deque[float] = deque()

    try:
        await websocket.send_json({
            "type": "system",
            "event": "connected",
            "client_id": client_id,
        })

        while True:
            try:
                message = await websocket.receive_json()
            except WebSocketDisconnect:
                raise
            except Exception:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format",
                })
                continue

            if not isinstance(message, dict) or message.get("type") != "chat":
                await websocket.send_json({
                    "type": "error",
                    "message": "Unsupported message type",
                })
                continue

            content = message.get("content")

            if not isinstance(content, str):
                continue

            content = content.strip()

            if not content:
                continue

            if len(content) > MAX_MESSAGE_LENGTH:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message too long",
                })
                continue

            now = time.monotonic()

            while recent_timestamps and now - recent_timestamps[0] > RATE_LIMIT_WINDOW_SECONDS:
                recent_timestamps.popleft()

            if len(recent_timestamps) >= RATE_LIMIT_MESSAGES:
                await websocket.send_json({
                    "type": "error",
                    "message": "Rate limit exceeded",
                })
                continue

            recent_timestamps.append(now)

            await manager.broadcast({
                "type": "chat",
                "message_id": str(uuid4()),
                "sender_id": client_id,
                "content": content,
            })

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(client_id)
