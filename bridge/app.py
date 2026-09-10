"""FastAPI application for the LAN-facing Watcher ingress."""

from fastapi import FastAPI, Header

from bridge.config import Settings
from bridge.events import EventHandler, log_event, normalize_event
from bridge.models import HealthResponse, WatcherNotification, WatcherResponse
from bridge.security import authorize_device


def create_app(
    settings: Settings | None = None, event_handler: EventHandler = log_event
) -> FastAPI:
    runtime_settings = settings or Settings.from_env()
    app = FastAPI(title="Teacher Edge Watcher Bridge", version="0.1.0")

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

    return app


app = create_app()
