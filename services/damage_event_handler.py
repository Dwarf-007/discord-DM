"""
SERVICES/DAMAGE_EVENT_HANDLER.PY
Converts DAMAGE domain events into Avrae damage commands.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.game_events import EventTypes, GameEvent


class DamageEventHandler:
    """
    Handles EventTypes.DAMAGE.

    Expected payload examples:
        {"amount": 5, "type": "piercing", "target": "@Player"}
        {"amount": "1d6", "type": "fire"}

    If target is missing, the command contains PLAYER as a placeholder so the
    caller can replace it during multi-targeting.
    """

    def handle(self, event: GameEvent) -> Optional[Dict[str, Any]]:
        if event.type != EventTypes.DAMAGE:
            return None

        payload = event.payload or {}
        amount = self._format_amount(payload.get("amount", 0))
        damage_type = self._format_damage_type(payload.get("type"))
        target = str(payload.get("target") or payload.get("player_id") or "PLAYER")

        command = f"!damage {target} {amount}{damage_type}"
        return {
            "type": "avrae_command",
            "command": command,
            "reason": str(payload.get("source") or "damage_event"),
        }

    @staticmethod
    def _format_amount(value: Any) -> str:
        text = str(value).strip()
        return text if text else "0"

    @staticmethod
    def _format_damage_type(value: Any) -> str:
        damage_type = str(value or "").strip()
        return f"[{damage_type}]" if damage_type else ""
