
"""
LLM response domain models.

These dataclasses define the canonical contract expected from Gemini.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InventoryUpdate:
    """Structured inventory delta emitted by the LLM."""

    gold: float = 0.0
    items: Dict[str, int] = field(default_factory=dict)
    ammo: Dict[str, int] = field(default_factory=dict)


@dataclass
class RestConsequence:
    """Structured rest outcome emitted by the LLM."""

    rest_type: str = "NONE"
    status: str = "NONE"
    ambush_monster: Optional[str] = None


@dataclass
class SecretMessage:
    """Private lore or hidden information to be routed to one player."""

    player_id: str
    text: str


@dataclass
class LLMResponse:
    """
    Canonical normalized LLM output.

    This becomes the single contract between the LLM layer and the game
    pipeline.
    """

    narrative: str
    required_check: str = "None"
    dc: int = 0
    next_room_id: Optional[str] = None
    xp_reward: int = 0
    milestone_reached: bool = False
    inventory_update: InventoryUpdate = field(default_factory=InventoryUpdate)
    avrae_sync_damage: Optional[int] = None
    secret_messages: List[SecretMessage] = field(default_factory=list)
    rest_consequence: RestConsequence = field(default_factory=RestConsequence)
