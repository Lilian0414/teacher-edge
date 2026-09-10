from fastapi.testclient import TestClient

from bridge.app import create_app
from bridge.config import Settings


PAYLOAD = {
    "requestId": "request-123",
    "deviceEui": "watcher-abc",
    "events": {
        "timestamp": 1788983266392,
        "text": "human detected",
        "data": {
            "inference": {
                "boxes": [[145, 262, 240, 308, 83, 0]],
                "classes_name": ["person"],
            }
        },
    },
}


def make_client(handler=lambda event: None) -> TestClient:
    settings = Settings(
        shared_token="test-token", allowed_device_euis=frozenset({"watcher-abc"})
    )
    return TestClient(create_app(settings, handler))


def test_health() -> None:
    response = make_client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_human_detection_is_normalized() -> None:
    received = []
    response = make_client(received.append).post(
        "/v1/notification/event",
        json=PAYLOAD,
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert response.json() == {"code": 200}
    event = received[0]
    assert event.source == "watcher"
    assert event.device_id == "watcher-abc"
    assert event.event_type == "human_detection"
    assert event.raw_request_id == "request-123"
    assert event.inference.classes_name == ["person"]


def test_invalid_or_missing_auth_is_rejected() -> None:
    client = make_client()
    for headers in ({}, {"Authorization": "wrong-token"}):
        response = client.post("/v1/notification/event", json=PAYLOAD, headers=headers)
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid device credentials"}


def test_device_allowlist_is_enforced() -> None:
    payload = {**PAYLOAD, "deviceEui": "unknown-device"}
    response = make_client().post(
        "/v1/notification/event",
        json=payload,
        headers={"Authorization": "test-token"},
    )
    assert response.status_code == 401


def test_invalid_json_and_payload_return_clear_4xx() -> None:
    client = make_client()
    headers = {"Authorization": "test-token", "Content-Type": "application/json"}
    malformed = client.post("/v1/notification/event", content="{", headers=headers)
    incomplete = client.post(
        "/v1/notification/event", json={"requestId": "only"}, headers=headers
    )
    assert malformed.status_code == 422
    assert incomplete.status_code == 422
    assert malformed.json()["detail"]
    assert incomplete.json()["detail"]
