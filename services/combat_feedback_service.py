"""
SERVICES/COMBAT_FEEDBACK_SERVICE.PY
Processes Avrae bot feedback and emits combat lifecycle events.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from avrae.avrae_parser import AvraeParserService
from core.game_events import EventBus, EventTypes, GameEvent
from models.combat_feedback import CombatFeedbackResult


class CombatFeedbackService:
    def __init__(self, combat_repo, event_bus: EventBus, parser: Optional[AvraeParserService] = None) -> None:
        self.combat_repo = combat_repo
        self.event_bus = event_bus
        self.parser = parser or AvraeParserService()
        self.combat_repo.ensure_schema()

    def register_encounter(
        self,
        channel_id: str,
        monsters: List[Dict[str, Any]],
        room_id: Optional[str] = None,
        xp_reward_total: int = 0,
    ) -> None:
        self.combat_repo.start_combat(
            channel_id=str(channel_id),
            room_id=room_id,
            monsters=monsters,
            xp_reward_total=int(xp_reward_total or 0),
        )

    async def process_avrae_message(self, message) -> CombatFeedbackResult:
        channel_id = str(message.channel.id)
        text = self.parser.extract_full_text(message)
        return self.process_text(channel_id, text)

    def process_text(self, channel_id: str, text: str) -> CombatFeedbackResult:
        defeated = self.parser.extract_defeated_names(text)
        if not defeated:
            snapshot = self.combat_repo.get_combat_state(channel_id)
            return CombatFeedbackResult(
                defeated_names=[],
                all_monsters_defeated=False,
                remaining_monsters=snapshot.monsters,
                raw_text=text,
            )

        matched: List[str] = []
        for name in defeated:
            if self.combat_repo.register_defeated_monster(channel_id, name):
                matched.append(name)

        snapshot = self.combat_repo.get_combat_state(channel_id)
        all_dead = bool(matched) and not snapshot.active

        if all_dead:
            self.event_bus.emit(
                GameEvent(
                    EventTypes.ALL_MONSTERS_DEFEATED,
                    {
                        "channel_id": str(channel_id),
                        "room_id": snapshot.room_id,
                        "xp_reward_total": snapshot.xp_reward_total,
                        "defeated_names": matched,
                    },
                )
            )
            self.event_bus.emit(
                GameEvent(
                    EventTypes.COMBAT_END,
                    {
                        "channel_id": str(channel_id),
                        "room_id": snapshot.room_id,
                    },
                )
            )
            self.combat_repo.clear_combat(channel_id)

        return CombatFeedbackResult(
            combat_ended=all_dead,
            defeated_names=matched,
            all_monsters_defeated=all_dead,
            remaining_monsters=snapshot.monsters,
            raw_text=text,
        )
