"""The small, stock-Watcher-compatible push-to-talk transport boundary."""

from __future__ import annotations

import json
import math
import struct
from fastapi import HTTPException, Request, status
from starlette.requests import ClientDisconnect


RESPONSE_SEPARATOR = b"---sensecraftboundary---\n"
TEST_MESSAGE = "Teacher Edge audio transport test"
TEST_AUDIO_DURATION_MS = 2_000


async def read_bounded_audio(request: Request, maximum_bytes: int) -> bytes:
    """Read a binary upload without ever buffering more than the configured limit."""

    if maximum_bytes < 1:
        raise RuntimeError("watcher audio upload limit must be positive")

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared = int(content_length)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="Invalid Content-Length"
            ) from exc
        if declared < 1:
            raise HTTPException(status_code=400, detail="Audio upload is empty")
        if declared > maximum_bytes:
            raise HTTPException(status_code=413, detail="Audio upload is too large")

    body = bytearray()
    try:
        async for chunk in request.stream():
            if len(body) + len(chunk) > maximum_bytes:
                raise HTTPException(status_code=413, detail="Audio upload is too large")
            body.extend(chunk)
    except ClientDisconnect as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio upload disconnected",
        ) from exc
    if not body:
        raise HTTPException(status_code=400, detail="Audio upload is empty")
    return bytes(body)


def deterministic_test_wav() -> bytes:
    """Return a short, reproducible 16-kHz mono PCM tone; no provider is contacted."""

    sample_rate = 16_000
    # Stock firmware presents ``screen_text`` while the response audio is active.
    # Keep the transport tone long enough for that presentation to be visible.
    sample_count = sample_rate * TEST_AUDIO_DURATION_MS // 1_000
    samples = bytearray()
    for index in range(sample_count):
        # Fade the 440-Hz tone to avoid clicks on the Watcher speaker.
        envelope = min(index / 160, (sample_count - index - 1) / 160, 1.0)
        value = round(
            4_000 * envelope * math.sin(2 * math.pi * 440 * index / sample_rate)
        )
        samples.extend(struct.pack("<h", value))
    size = len(samples)
    header = (
        b"RIFF"
        + struct.pack("<I", 36 + size)
        + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", size)
    )
    return header + samples


def framed_test_response() -> bytes:
    """Build the stock compact-JSON, separator, and WAV response body."""

    metadata = json.dumps(
        {
            "code": 200,
            "data": {
                "stt_result": TEST_MESSAGE,
                "screen_text": TEST_MESSAGE,
                "mode": 0,
                "duration": TEST_AUDIO_DURATION_MS,
            },
        },
        separators=(",", ":"),
    ).encode()
    return metadata + RESPONSE_SEPARATOR + deterministic_test_wav()
