"""
CORE/TURN_OUTPUT.PY
Canonical output object returned by the game turn pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from core.llm_response import SecretMessage


@dataclass
class TurnOutput:
    """
    Final application-level output after deterministic processing.

    Discord layer should send:
    - public_narrative to the channel
    - avrae_commands as separate messages or queued commands
    - secret_messages via DM
    """

    public_narrative: str = ""
    avrae_commands: List[str] = field(default_factory=list)
    secret_messages: List[SecretMessage] = field(default_factory=list)
    debug_notes: List[str] = field(default_factory=list)
    state_changed: bool = False
    next_room_id: str | None = None
