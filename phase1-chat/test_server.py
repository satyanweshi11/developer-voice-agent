import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from server import app

client = TestClient(app)
LOCAL_ORIGIN = {"origin": "http://localhost"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_connect_sends_system_message():
    with client.websocket_connect("/ws", headers=LOCAL_ORIGIN) as ws:
        message = ws.receive_json()
        assert message["type"] == "system"
        assert message["client_id"]


def test_chat_message_is_broadcast():
    with client.websocket_connect("/ws", headers=LOCAL_ORIGIN) as ws:
        ws.receive_json()
        ws.send_json({"type": "chat", "content": "hello"})
        message = ws.receive_json()
        assert message["type"] == "chat"
        assert message["content"] == "hello"
        assert message["sender_id"]


def test_content_is_trimmed():
    with client.websocket_connect("/ws", headers=LOCAL_ORIGIN) as ws:
        ws.receive_json()
        ws.send_json({"type": "chat", "content": "  spaced  "})
        message = ws.receive_json()
        assert message["content"] == "spaced"


def test_rejects_unsupported_type():
    with client.websocket_connect("/ws", headers=LOCAL_ORIGIN) as ws:
        ws.receive_json()
        ws.send_json({"type": "ping"})
        message = ws.receive_json()
        assert message["type"] == "error"
        assert message["message"] == "Unsupported message type"


def test_rejects_invalid_json():
    with client.websocket_connect("/ws", headers=LOCAL_ORIGIN) as ws:
        ws.receive_json()
        ws.send_text("not json")
        message = ws.receive_json()
        assert message["type"] == "error"
        assert message["message"] == "Invalid message format"


def test_rejects_message_too_long():
    with client.websocket_connect("/ws", headers=LOCAL_ORIGIN) as ws:
        ws.receive_json()
        ws.send_json({"type": "chat", "content": "x" * 2001})
        message = ws.receive_json()
        assert message["type"] == "error"
        assert message["message"] == "Message too long"


def test_rate_limit_enforced():
    with client.websocket_connect("/ws", headers=LOCAL_ORIGIN) as ws:
        ws.receive_json()
        for _ in range(10):
            ws.send_json({"type": "chat", "content": "spam"})
            assert ws.receive_json()["type"] == "chat"

        ws.send_json({"type": "chat", "content": "spam"})
        message = ws.receive_json()
        assert message["type"] == "error"
        assert message["message"] == "Rate limit exceeded"


def test_rejects_disallowed_origin():
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws", headers={"origin": "http://evil.site"}):
            pass
    assert excinfo.value.code == 1008
