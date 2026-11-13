from datetime import datetime

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient


def test_health_return_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_messages_are_broadcast_to_everyone(client: TestClient) -> None:
    with client.websocket_connect("/ws/ada") as ada:
        assert ada.receive_text() == "ada joined"

        with client.websocket_connect("/ws/bob") as bob:
            assert ada.receive_text() == "bob joined"
            assert bob.receive_text() == "bob joined"

            bob.send_text("hello")

            assert ada.receive_text() == "bob: hello"
            assert bob.receive_text() == "bob: hello"

        assert ada.receive_text() == "bob left"


def test_long_messages_are_rejected_and_not_broadcast(client: TestClient) -> None:
    with client.websocket_connect("/ws/ada") as ada:
        assert ada.receive_text() == "ada joined"

        ada.send_text("x" * 21)
        assert ada.receive_text() == "Not sent . Messages can be up to 20 characters"

        ada.send_text("x" * 20)
        assert ada.receive_text() == "ada: " + "x" * 20


def test_long_messages_are_not_stored(client: TestClient) -> None:
    with client.websocket_connect("/ws/ada") as ada:
        ada.receive_text()
        ada.send_text("x" * 21)
        ada.receive_text()

    assert client.get("/messages").json() == []


def test_sent_messages_are_listed(client: TestClient) -> None:
    assert client.get("/messages").json() == []

    with client.websocket_connect("/ws/ada") as ada:
        ada.receive_text()
        ada.send_text("hello")
        ada.receive_text()

    [message] = client.get("/messages").json()
    assert message["author"] == "ada"
    assert message["body"] == "hello"
    assert datetime.fromisoformat(message["created_at"]).tzinfo is not None


@pytest.mark.parametrize("limit", [0, 201])
def test_message_limit_is_validated(client: TestClient, limit: int) -> None:
    assert client.get("/messages", params={"limit": limit}).status_code == 422


def test_people_who_join_see_recent_history(client: TestClient) -> None:
    with client.websocket_connect("/ws/ada") as ada:
        ada.receive_text()
        ada.send_text("anyone here?")
        ada.receive_text()

    with client.websocket_connect("/ws/bob") as bob:
        assert bob.receive_text() == "ada: anyone here?"
        assert bob.receive_text() == "bob joined"


def test_names_longer_than_50_characters_are_refused(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws/" + "x" * 51):
        pass
