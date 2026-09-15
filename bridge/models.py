"""Typed Watcher transport and normalized device-event models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Inference(BaseModel):
    model_config = ConfigDict(extra="allow")

    boxes: list[list[int | float]] = Field(default_factory=list)
    classes_name: list[str] = Field(default_factory=list)


class EventData(BaseModel):
    model_config = ConfigDict(extra="allow")

    inference: Inference | None = None


class WatcherEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: int
    text: str
    data: EventData = Field(default_factory=EventData)


class WatcherNotification(BaseModel):
    model_config = ConfigDict(extra="allow")

    requestId: str = Field(min_length=1)
    deviceEui: str = Field(min_length=1)
    events: WatcherEvent


class DeviceEvent(BaseModel):
    source: Literal["watcher"] = "watcher"
    device_id: str
    event_type: str
    timestamp: int
    text: str
    inference: Inference | None
    raw_request_id: str


class WatcherResponse(BaseModel):
    code: int = 200


class HealthResponse(BaseModel):
    status: Literal["healthy"] = "healthy"


class TextRequest(BaseModel):
    """Synthetic device text accepted by the edge transport boundary."""

    request_id: str = Field(min_length=1)
    device_eui: str = Field(min_length=1)
    text: str = Field(min_length=1)
    session_id: str | None = Field(default=None, min_length=1)


class TextResponse(BaseModel):
    conversation_id: str
    assistant_text: str
