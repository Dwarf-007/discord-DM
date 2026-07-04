
"""
TOOLS/INTEGRATION_CHECK.PY
Compact integration check for the refactor-20 compatibility patch.

Run:
    python tools/integration_check.py
"""

from __future__ import annotations

from app.bootstrap import build_runtime


def main() -> int:
    runtime = build_runtime()
    channel_id = "integration-check-channel"
    campaign_id = "INTEGRATION_CHECK"
    runtime.campaign_service.ensure_campaign(campaign_id, name="Integration Check")
    runtime.campaign_service.set_active_campaign(channel_id, campaign_id)
    runtime.location_repo.upsert_room({
        "campaign_id": campaign_id,
        "room_id": "room_a",
        "title": "Room A",
        "facts": "Start room.",
        "exits": {"north": "room_b"},
    })
    runtime.location_repo.upsert_room({
        "campaign_id": campaign_id,
        "room_id": "room_b",
        "title": "Room B",
        "facts": "Target room.",
        "exits": {"south": "room_a"},
    })
    runtime.room_alias_service.ensure_room_aliases_from_room(campaign_id, {"room_id": "room_a", "title": "Room A", "room_slug": "room_a"})
    runtime.room_alias_service.ensure_room_aliases_from_room(campaign_id, {"room_id": "room_b", "title": "Room B", "room_slug": "room_b"})
    runtime.admin_debug_service.set_room(channel_id, "Room A")
    output = runtime.movement_service.try_handle_movement(channel_id, "Megyünk észak felé.", player_id="p1")
    print(output)
    report = runtime.runtime_health_service.run_all(campaign_id=campaign_id, channel_id=channel_id)
    print(report.to_text())
    return 1 if report.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
