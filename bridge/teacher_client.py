"""Narrow HTTP adapter for the Pi-local Teacher Core conversation API."""

from dataclasses import dataclass
import logging
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError


logger = logging.getLogger(__name__)


class CreateConversationRequest(BaseModel):
    """The current Teacher endpoint accepts an empty JSON object."""


class CreateConversationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str


class SendMessageRequest(BaseModel):
    content: str


class TeacherMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    content: str


class SendMessageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ok: bool
    assistant_message: TeacherMessage | None = None
    error: str | None = None
    retryable: bool


@dataclass(frozen=True)
class TeacherClientError(Exception):
    """A sanitized failure at the Teacher HTTP boundary."""

    kind: str
    retryable: bool
    status_code: int | None = None

    def __str__(self) -> str:
        return f"Teacher Core request failed ({self.kind})"


class TeacherClient:
    """Call only Teacher's documented conversation endpoints on localhost."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout_seconds: float = 15.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if base_url.rstrip("/") != "http://127.0.0.1:8000":
            raise ValueError("Teacher Core URL must be http://127.0.0.1:8000")
        self._client = http_client or httpx.AsyncClient(
            base_url=base_url, timeout=timeout_seconds
        )
        self._owns_client = http_client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def create_conversation(self) -> str:
        response = await self._post(
            "/v1/conversations", CreateConversationRequest().model_dump()
        )
        try:
            conversation = CreateConversationResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise TeacherClientError("malformed_response", False) from exc
        if not conversation.id:
            raise TeacherClientError("malformed_response", False)
        return conversation.id

    async def send_message(self, conversation_id: str, content: str) -> str:
        payload = SendMessageRequest(content=content)
        response = await self._post(
            f"/v1/conversations/{conversation_id}/messages",
            payload.model_dump(),
        )
        try:
            result = SendMessageResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise TeacherClientError("malformed_response", False) from exc
        if not result.ok:
            # Teacher's provider error text is deliberately not logged or propagated.
            raise TeacherClientError("generation_failed", result.retryable)
        if result.assistant_message is None:
            raise TeacherClientError("malformed_response", False)
        return result.assistant_message.content

    async def _post(self, path: str, payload: dict[str, Any]) -> httpx.Response:
        logger.info("teacher_request path=%s", path)
        try:
            response = await self._client.post(path, json=payload)
        except httpx.TimeoutException as exc:
            logger.warning("teacher_request_failed path=%s kind=timeout", path)
            raise TeacherClientError("timeout", True) from exc
        except httpx.RequestError as exc:
            logger.warning("teacher_request_failed path=%s kind=unavailable", path)
            raise TeacherClientError("unavailable", True) from exc

        if response.is_success:
            logger.info("teacher_request_complete path=%s status=%s", path, response.status_code)
            return response

        retryable = response.status_code >= 500
        logger.warning(
            "teacher_request_failed path=%s kind=http_error status=%s retryable=%s",
            path,
            response.status_code,
            retryable,
        )
        raise TeacherClientError("http_error", retryable, response.status_code)
