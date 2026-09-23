"""FastAPI application for the LAN-facing Watcher ingress."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException

from bridge.config import Settings
from bridge.events import EventHandler, log_event, normalize_event
from bridge.models import (
    HealthResponse,
    TextRequest,
    TextResponse,
    WatcherNotification,
    WatcherResponse,
)
from bridge.security import authorize_device
from bridge.sessions import ConversationSessions
from bridge.teacher_client import TeacherClient, TeacherClientError


def create_app(
    settings: Settings | None = None,
    event_handler: EventHandler = log_event,
    teacher_client: TeacherClient | None = None,
) -> FastAPI:
    runtime_settings = settings or Settings.from_env()
    teacher = teacher_client or TeacherClient(
        runtime_settings.teacher_core_url, runtime_settings.teacher_timeout_seconds
    )
    sessions = ConversationSessions(teacher)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await teacher.close()

    app = FastAPI(
        title="Teacher Edge Watcher Bridge", version="0.1.0", lifespan=lifespan
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    @app.post("/v1/notification/event", response_model=WatcherResponse)
    def notification_event(
        notification: WatcherNotification,
        authorization: str | None = Header(default=None),
    ) -> WatcherResponse:
        authorize_device(authorization, notification.deviceEui, runtime_settings)
        event_handler(normalize_event(notification))
        return WatcherResponse()

    @app.post("/v1/text", response_model=TextResponse)
    async def text_turn(
        request: TextRequest,
        authorization: str | None = Header(default=None),
    ) -> TextResponse:
        authorize_device(authorization, request.device_eui, runtime_settings)
        try:
            conversation_id, assistant_text = await sessions.send(
                request.device_eui, request.session_id, request.text
            )
        except TeacherClientError as exc:
            # Do not expose upstream bodies, credentials, or provider details.
            status = 503 if exc.retryable else 502
            raise HTTPException(
                status_code=status,
                detail={"error": "teacher_core_unavailable", "retryable": exc.retryable},
            ) from exc
        return TextResponse(
            conversation_id=conversation_id, assistant_text=assistant_text
        )

    return app


app = create_app()
