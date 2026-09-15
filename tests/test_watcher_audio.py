import asyncio
import json
import struct

from fastapi.testclient import TestClient

from bridge.app import create_app
from bridge.config import Settings
from bridge.watcher_audio import (
    RESPONSE_SEPARATOR,
    TEST_MESSAGE,
    deterministic_test_wav,
)
from bridge.watcher_audio import read_bounded_audio
from fastapi import HTTPException
from starlette.requests import ClientDisconnect


AUTH = {"Authorization": "test-token", "Content-Type": "application/octet-stream"}
URL = "/v2/watcher/talk/audio_stream?deviceEui=watcher-abc"


def client(maximum: int = 2_000_000) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                shared_token="test-token",
                allowed_device_euis=frozenset({"watcher-abc"}),
                watcher_audio_max_bytes=maximum,
            )
        )
    )


def test_stock_audio_upload_returns_json_then_deterministic_wav() -> None:
    response = client().post(URL, content=b"RIFFsynthetic-capture", headers=AUTH)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert int(response.headers["content-length"]) == len(response.content)
    metadata_bytes, wav = response.content.split(RESPONSE_SEPARATOR, 1)
    assert metadata_bytes == (
        b'{"code":200,"data":{"stt_result":"Teacher Edge audio transport test",'
        b'"screen_text":"Teacher Edge audio transport test","mode":"text",'
        b'"duration":0.15}}'
    )
    assert json.loads(metadata_bytes) == {
        "code": 200,
        "data": {
            "stt_result": TEST_MESSAGE,
            "screen_text": TEST_MESSAGE,
            "mode": "text",
            "duration": 0.15,
        },
    }
    assert wav == deterministic_test_wav()
    assert wav[:12] == b"RIFF" + struct.pack("<I", 4836) + b"WAVE"


def test_stock_headers_authenticate_device_identity() -> None:
    response = client().post(
        "/v2/watcher/talk/audio_stream",
        content=b"captured-audio-placeholder",
        headers={
            "Authorization": "test-token",
            "Content-Type": "application/octet-stream",
            "API-OBITER-DEVICE-EUI": "watcher-abc",
            "Session-Id": "session-123",
        },
    )
    assert response.status_code == 200


def test_audio_auth_is_enforced_before_body_parsing() -> None:
    response = client().post(URL, content=b"", headers={**AUTH, "Authorization": "bad"})
    assert response.status_code == 401


def test_empty_oversize_and_content_type_are_bounded() -> None:
    assert client().post(URL, content=b"", headers=AUTH).status_code == 400
    too_large = client(maximum=4).post(URL, content=b"12345", headers=AUTH)
    assert too_large.status_code == 413
    assert too_large.json() == {"detail": "Audio upload is too large"}
    wrong_type = client().post(
        URL, content=b"audio", headers={**AUTH, "Content-Type": "application/json"}
    )
    assert wrong_type.status_code == 415


def test_malformed_length_and_disconnect_are_sanitized() -> None:
    class MalformedRequest:
        headers = {"content-length": "not-a-number"}

    class DisconnectedRequest:
        headers = {}

        async def stream(self):
            yield b"partial"
            raise ClientDisconnect

    for request, detail in (
        (MalformedRequest(), "Invalid Content-Length"),
        (DisconnectedRequest(), "Audio upload disconnected"),
    ):
        try:
            asyncio.run(read_bounded_audio(request, 100))  # type: ignore[arg-type]
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == detail
        else:
            raise AssertionError("malformed upload unexpectedly succeeded")
