from fastapi.testclient import TestClient

from murmur_api.main import app

client = TestClient(app)


def test_health_return_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_messages_are_broadcast_to_everyone() -> None:
    with client.websocket_connect("/ws/ada") as ada:
        assert ada.receive_text() == "ada joined"

        with client.websocket_connect("/ws/bob") as bob:
            assert ada.receive_text() == "bob joined"
            assert bob.receive_text() == "bob joined"

            bob.send_text("hello")

            assert ada.receive_text() == "bob: hello"
            assert bob.receive_text() == "bob: hello"

        assert ada.receive_text() == "bob left"
