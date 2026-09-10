"""Watcher credential validation without secret disclosure."""

import secrets

from fastapi import HTTPException, status

from bridge.config import Settings


def authorize_device(authorization: str | None, device_eui: str, settings: Settings) -> None:
    if not settings.shared_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Watcher ingress authentication is not configured",
        )

    supplied = authorization or ""
    if supplied.lower().startswith("bearer "):
        supplied = supplied[7:]
    token_valid = secrets.compare_digest(supplied, settings.shared_token)
    device_valid = (
        not settings.allowed_device_euis or device_eui in settings.allowed_device_euis
    )
    if not token_valid or not device_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
        )
