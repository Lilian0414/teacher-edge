import json

import httpx
import pytest

from bridge.teacher_client import TeacherClient, TeacherClientError


@pytest.mark.anyio
async def test_conversation_and_message_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/v1/conversations":
            return httpx.Response(201, json={"id": "conversation-1", "extra": True})
        return httpx.Response(
            200,
            json={
                "ok": True,
                "assistant_message": {"content": "Teacher reply", "role": "assistant"},
                "retryable": False,
            },
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://127.0.0.1:8000"
    ) as http:
        client = TeacherClient(http_client=http)
        conversation_id = await client.create_conversation()
        reply = await client.send_message(conversation_id, "hello")

    assert conversation_id == "conversation-1"
    assert reply == "Teacher reply"
    assert [request.url.path for request in requests] == [
        "/v1/conversations",
        "/v1/conversations/conversation-1/messages",
    ]
    assert json.loads(requests[0].content) == {}
    assert json.loads(requests[1].content) == {"content": "hello"}


@pytest.mark.anyio
@pytest.mark.parametrize("status", [400, 404])
async def test_4xx_is_not_retryable(status: int) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(status)),
        base_url="http://127.0.0.1:8000",
    ) as http:
        with pytest.raises(TeacherClientError) as caught:
            await TeacherClient(http_client=http).create_conversation()
    assert caught.value.status_code == status
    assert caught.value.retryable is False


@pytest.mark.anyio
@pytest.mark.parametrize("status", [500, 502, 503])
async def test_5xx_is_retryable(status: int) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(status)),
        base_url="http://127.0.0.1:8000",
    ) as http:
        with pytest.raises(TeacherClientError) as caught:
            await TeacherClient(http_client=http).create_conversation()
    assert caught.value.retryable is True


@pytest.mark.anyio
async def test_timeout_is_retryable() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(timeout), base_url="http://127.0.0.1:8000"
    ) as http:
        with pytest.raises(TeacherClientError) as caught:
            await TeacherClient(http_client=http).create_conversation()
    assert caught.value.kind == "timeout"
    assert caught.value.retryable is True


@pytest.mark.anyio
async def test_malformed_response_is_not_retryable() -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"unexpected": "shape"})
        ),
        base_url="http://127.0.0.1:8000",
    ) as http:
        with pytest.raises(TeacherClientError) as caught:
            await TeacherClient(http_client=http).create_conversation()
    assert caught.value.kind == "malformed_response"
    assert caught.value.retryable is False


@pytest.mark.anyio
@pytest.mark.parametrize("retryable", [True, False])
async def test_200_generation_failure_preserves_retryability(retryable: bool) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "ok": False,
                    "assistant_message": None,
                    "error": "sensitive-provider-detail",
                    "retryable": retryable,
                    "user_message": {"id": "already-persisted"},
                },
            )
        ),
        base_url="http://127.0.0.1:8000",
    ) as http:
        with pytest.raises(TeacherClientError) as caught:
            await TeacherClient(http_client=http).send_message("conversation-1", "hello")

    assert caught.value.kind == "generation_failed"
    assert caught.value.retryable is retryable
    assert "sensitive-provider-detail" not in str(caught.value)


def test_non_local_teacher_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be"):
        TeacherClient(base_url="http://teacher.example:8000")
