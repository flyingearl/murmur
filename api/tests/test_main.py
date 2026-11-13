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
