
"""
SERVICES/CAMPAIGN_SERVICE.PY
Application service for campaign registry, active campaign selection, and status.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from models.campaign import CampaignRecord, CampaignStatus


class CampaignService:
    def __init__(
        self,
        campaign_repo,
        channel_repo,
        location_repo=None,
        rag_chunk_repo=None,
        memory_repo=None,
    ) -> None:
        self.campaign_repo = campaign_repo
        self.channel_repo = channel_repo
        self.location_repo = location_repo
        self.rag_chunk_repo = rag_chunk_repo
        self.memory_repo = memory_repo
        self.campaign_repo.ensure_schema()

    def ensure_campaign(
        self,
        campaign_id: str,
        name: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CampaignRecord:
        self.campaign_repo.upsert_campaign(campaign_id, name=name, description=description, metadata=metadata or {})
        record = self.campaign_repo.get_campaign(campaign_id)
        if not record:
            raise RuntimeError(f"Campaign could not be created: {campaign_id}")
        return record

    def set_active_campaign(self, channel_id: str, campaign_id: str) -> str:
        campaign_id = str(campaign_id or "").strip()
        if not campaign_id:
            return "Hiányzó campaign_id."
        self.ensure_campaign(campaign_id)
        self.channel_repo.update_field(channel_id, "campaign_id", campaign_id)
        return f"Aktív kampány beállítva ezen a csatornán: `{campaign_id}`"

    def get_active_campaign_id(self, channel_id: str) -> str:
        state = self.channel_repo.get_state(channel_id)
        return str(state.get("campaign_id") or "default")

    def list_campaigns_text(self) -> str:
        campaigns = self.campaign_repo.list_campaigns()
        if not campaigns:
            return "Nincs regisztrált kampány."
        lines = ["**Regisztrált kampányok:**"]
        for campaign in campaigns:
            lines.append(f"- `{campaign.campaign_id}` — {campaign.name}")
        return "\n".join(lines)

    def status_text(self, channel_id: str) -> str:
        campaign_id = self.get_active_campaign_id(channel_id)
        campaign = self.campaign_repo.get_campaign(campaign_id)
        room_count = self._room_count(campaign_id)
        rag_count = self._rag_count(campaign_id)
        memory_count = self._memory_count(channel_id)
        name = campaign.name if campaign else campaign_id
        description = campaign.description if campaign else ""
        return (
            "**Campaign status**\n"
            f"**Channel:** `{channel_id}`\n"
            f"**Active campaign:** `{campaign_id}`\n"
            f"**Name:** {name}\n"
            f"**Description:** {description or '-'}\n"
            f"**Rooms:** `{room_count}`\n"
            f"**RAG chunks:** `{rag_count}`\n"
            f"**Memory events in channel:** `{memory_count}`"
        )

    def _room_count(self, campaign_id: str) -> int:
        if not self.location_repo:
            return 0
        try:
            return len(self.location_repo.list_rooms(campaign_id=campaign_id))
        except TypeError:
            return len(self.location_repo.list_rooms())
        except Exception:
            return 0

    def _rag_count(self, campaign_id: str) -> int:
        if not self.rag_chunk_repo:
            return 0
        try:
            return len(self.rag_chunk_repo.list_chunks(campaign_id=campaign_id, limit=10000))
        except Exception:
            return 0

    def _memory_count(self, channel_id: str) -> int:
        if not self.memory_repo:
            return 0
        try:
            return len(self.memory_repo.list_recent_events(channel_id, limit=500))
        except Exception:
            return 0
