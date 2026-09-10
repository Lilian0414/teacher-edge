"""Normalization and the narrow in-process event-handler boundary."""

from collections.abc import Callable
import logging

from bridge.models import DeviceEvent, WatcherNotification

EventHandler = Callable[[DeviceEvent], None]

logger = logging.getLogger(__name__)


def normalize_event(notification: WatcherNotification) -> DeviceEvent:
    inference = notification.events.data.inference
    classes = inference.classes_name if inference else []
    event_type = "human_detection" if "person" in classes else "notification"
    return DeviceEvent(
        device_id=notification.deviceEui,
        event_type=event_type,
        timestamp=notification.events.timestamp,
        text=notification.events.text,
        inference=inference,
        raw_request_id=notification.requestId,
    )


def log_event(event: DeviceEvent) -> None:
    """Default M1 sink; deliberately logs metadata rather than raw requests."""
    logger.info(
        "Watcher event accepted device_id=%s event_type=%s request_id=%s",
        event.device_id,
        event.event_type,
        event.raw_request_id,
    )
