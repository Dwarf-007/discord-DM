
"""
REPOSITORIES/CAMPAIGN_REPOSITORY.PY
Persistence abstraction for campaign registry.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from models.campaign import CampaignRecord
from repositories.base import BaseRepository


class CampaignRepository(BaseRepository):
    def ensure_schema(self) -> None:
        with self.db.get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS Campaigns (
                    campaign_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def upsert_campaign(
        self,
        campaign_id: str,
        name: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.ensure_schema()
        cid = str(campaign_id or "").strip()
        if not cid:
            raise ValueError("campaign_id is required")
        display_name = str(name or cid)
        with self.db.get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO Campaigns (campaign_id, name, description, metadata_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(campaign_id)
                DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    metadata_json = excluded.metadata_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (cid, display_name, str(description or ""), self.db.safe_json_dump(metadata or {})),
            )
            conn.commit()

    def get_campaign(self, campaign_id: str) -> Optional[CampaignRecord]:
        self.ensure_schema()
        with self.db.get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT campaign_id, name, description, metadata_json, created_at, updated_at
                FROM Campaigns
                WHERE campaign_id = ?
                """,
                (str(campaign_id),),
            ).fetchone()
        return self._row_to_record(row) if row else None

    def list_campaigns(self) -> List[CampaignRecord]:
        self.ensure_schema()
        with self.db.get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT campaign_id, name, description, metadata_json, created_at, updated_at
                FROM Campaigns
                ORDER BY campaign_id
                """
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def delete_campaign(self, campaign_id: str) -> None:
        self.ensure_schema()
        with self.db.get_db_connection() as conn:
            conn.execute("DELETE FROM Campaigns WHERE campaign_id = ?", (str(campaign_id),))
            conn.commit()

    def _row_to_record(self, row) -> CampaignRecord:
        return CampaignRecord(
            campaign_id=str(row["campaign_id"]),
            name=str(row["name"]),
            description=str(row["description"] or ""),
            metadata=self.db.safe_json_load(row["metadata_json"], {}),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
