import asyncio
import struct

from fastapi.testclient import TestClient

from bridge.app import create_app
from bridge.config import Settings
from bridge.watcher_audio import RESPONSE_BOUNDARY, TEST_MESSAGE, deterministic_test_wav
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


def split_multipart(body: bytes) -> list[tuple[bytes, bytes]]:
    parts = []
    for framed in body.split(f"--{RESPONSE_BOUNDARY}".encode())[1:-1]:
        headers, content = framed.removeprefix(b"\r\n").split(b"\r\n\r\n", 1)
        parts.append((headers, content.removesuffix(b"\r\n")))
    return parts


def test_stock_audio_upload_returns_json_then_deterministic_wav() -> None:
    response = client().post(URL, content=b"RIFFsynthetic-capture", headers=AUTH)
    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == f'multipart/mixed; boundary="{RESPONSE_BOUNDARY}"'
    )
    json_part, audio_part = split_multipart(response.content)
    assert b"Content-Type: application/json" in json_part[0]
    assert TEST_MESSAGE.encode() in json_part[1]
    assert b"Content-Type: audio/wav" in audio_part[0]
    assert audio_part[1] == deterministic_test_wav()
    assert audio_part[1][:12] == b"RIFF" + struct.pack("<I", 4836) + b"WAVE"


def test_bare_auth_and_header_device_identity_are_stock_compatible() -> None:
    response = client().post(
        "/v2/watcher/talk/audio_stream",
        content=b"captured-audio-placeholder",
        headers={
            "Authorization": "test-token",
            "Content-Type": "audio/wav",
            "X-Device-Eui": "watcher-abc",
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
