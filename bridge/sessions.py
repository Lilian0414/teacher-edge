"""Transient device-to-Teacher conversation mapping."""

import asyncio

from bridge.teacher_client import TeacherClient


class ConversationSessions:
    """Keep transport session IDs only; Teacher owns all conversation state."""

    def __init__(self, teacher: TeacherClient) -> None:
        self._teacher = teacher
        self._conversation_ids: dict[tuple[str, str], str] = {}
        self._locks: dict[tuple[str, str], asyncio.Lock] = {}

    async def send(
        self, device_eui: str, session_id: str | None, text: str
    ) -> tuple[str, str]:
        session_key = (device_eui, session_id or device_eui)
        lock = self._locks.setdefault(session_key, asyncio.Lock())
        async with lock:
            conversation_id = self._conversation_ids.get(session_key)
            if conversation_id is None:
                conversation_id = await self._teacher.create_conversation()
                self._conversation_ids[session_key] = conversation_id
            reply = await self._teacher.send_message(conversation_id, text)
            return conversation_id, reply
