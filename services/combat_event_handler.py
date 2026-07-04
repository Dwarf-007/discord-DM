"""
SERVICES/COMBAT_EVENT_HANDLER.PY
Converts COMBAT_START domain events into initial Avrae commands.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.game_events import EventTypes, GameEvent


class CombatEventHandler:
    """
    Handles EventTypes.COMBAT_START.

    Basic behavior:
        - Always emits !init begin.
        - If payload contains monsters/units, also emits !init add commands.

    Accepted monster item formats:
        {"name": "Goblin", "count": 2}
        {"monster_name": "Goblin", "count": 2}
    """

    def handle(self, event: GameEvent) -> Optional[List[Dict[str, Any]]]:
        if event.type != EventTypes.COMBAT_START:
            return None

        commands: List[Dict[str, Any]] = [
            {
                "type": "avrae_command",
                "command": "!init begin",
                "reason": str(event.payload.get("source") or "combat_start"),
            }
        ]

        for monster in self._extract_monsters(event.payload):
            name = monster["name"]
            count = monster["count"]
            commands.append(
                {
                    "type": "avrae_command",
                    "command": f"!init add {name} {count}",
                    "reason": "combat_start_monster_add",
                }
            )

        return commands

    @staticmethod
    def _extract_monsters(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        raw_units = payload.get("monsters") or payload.get("units") or []
        monsters: List[Dict[str, Any]] = []

        for item in raw_units:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("monster_name") or "").strip()
            if not name:
                continue
            try:
                count = int(item.get("count", 1))
            except (TypeError, ValueError):
                count = 1
            monsters.append({"name": name, "count": max(1, count)})

        return monsters
