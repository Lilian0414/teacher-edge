import httpx
from fastapi.testclient import TestClient

from bridge.app import create_app
from bridge.config import Settings
from bridge.teacher_client import TeacherClient


def test_text_request_creates_then_reuses_conversation() -> None:
    paths: list[str] = []

    def teacher_handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/v1/conversations":
            return httpx.Response(201, json={"id": "teacher-conversation"})
        return httpx.Response(
            200,
            json={
                "ok": True,
                "assistant_message": {"content": f"reply-{len(paths)}"},
                "retryable": False,
            },
        )

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(teacher_handler),
        base_url="http://127.0.0.1:8000",
    )
    settings = Settings("secret", frozenset({"watcher-1"}))
    with TestClient(create_app(settings, teacher_client=TeacherClient(http_client=http))) as client:
        payload = {
            "request_id": "request-1",
            "device_eui": "watcher-1",
            "session_id": "interaction-1",
            "text": "Hello Teacher",
        }
        first = client.post("/v1/text", json=payload, headers={"Authorization": "secret"})
        second = client.post(
            "/v1/text",
            json={**payload, "request_id": "request-2", "text": "Again"},
            headers={"Authorization": "secret"},
        )

    assert first.status_code == 200
    assert first.json() == {
        "conversation_id": "teacher-conversation",
        "assistant_text": "reply-2",
    }
    assert second.status_code == 200
    assert paths == [
        "/v1/conversations",
        "/v1/conversations/teacher-conversation/messages",
        "/v1/conversations/teacher-conversation/messages",
    ]


def test_same_session_id_is_isolated_between_devices() -> None:
    created = 0

    def teacher_handler(request: httpx.Request) -> httpx.Response:
        nonlocal created
        if request.url.path == "/v1/conversations":
            created += 1
            return httpx.Response(201, json={"id": f"conversation-{created}"})
        return httpx.Response(
            200,
            json={
                "ok": True,
                "assistant_message": {"content": "reply"},
                "retryable": False,
            },
        )

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(teacher_handler),
        base_url="http://127.0.0.1:8000",
    )
    settings = Settings("secret", frozenset({"watcher-1", "watcher-2"}))
    with TestClient(
        create_app(settings, teacher_client=TeacherClient(http_client=http))
    ) as client:
        responses = [
            client.post(
                "/v1/text",
                json={
                    "request_id": f"request-{device}",
                    "device_eui": device,
                    "session_id": "shared-name",
                    "text": "hello",
                },
                headers={"Authorization": "secret"},
            )
            for device in ("watcher-1", "watcher-2")
        ]

    assert [response.status_code for response in responses] == [200, 200]
    assert [response.json()["conversation_id"] for response in responses] == [
        "conversation-1",
        "conversation-2",
    ]


def test_teacher_unavailable_is_sanitized() -> None:
    def unavailable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("provider-secret-was-here", request=request)

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(unavailable),
        base_url="http://127.0.0.1:8000",
    )
    settings = Settings("secret", frozenset({"watcher-1"}))
    with TestClient(create_app(settings, teacher_client=TeacherClient(http_client=http))) as client:
        response = client.post(
            "/v1/text",
            json={"request_id": "one", "device_eui": "watcher-1", "text": "hello"},
            headers={"Authorization": "secret"},
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": {"error": "teacher_core_unavailable", "retryable": True}
    }
    assert "provider-secret" not in response.text
