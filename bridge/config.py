"""Environment-driven bridge configuration."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Secrets are read only from the process environment."""

    shared_token: str | None
    allowed_device_euis: frozenset[str]
    teacher_core_url: str = "http://127.0.0.1:8000"
    teacher_timeout_seconds: float = 15.0

    @classmethod
    def from_env(cls) -> "Settings":
        device_euis = os.getenv("TEACHER_EDGE_ALLOWED_DEVICE_EUIS", "")
        return cls(
            shared_token=os.getenv("TEACHER_EDGE_SHARED_TOKEN"),
            allowed_device_euis=frozenset(
                value.strip() for value in device_euis.split(",") if value.strip()
            ),
            teacher_core_url=os.getenv(
                "TEACHER_CORE_URL", "http://127.0.0.1:8000"
            ),
            teacher_timeout_seconds=float(
                os.getenv("TEACHER_CORE_TIMEOUT_SECONDS", "15")
            ),
        )
