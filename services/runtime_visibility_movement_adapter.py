from __future__ import annotations

import copy
import inspect
from pathlib import Path
from typing import Any, Dict, Optional

from services.runtime_campaign_bundle_resolver import RuntimeCampaignBundleResolver, ResolvedCampaignBundle
from services.runtime_visibility_intents import RuntimeVisibilityIntentParser, RuntimeVisibilityIntent
from services.visibility_runtime_formatter import VisibilityRuntimeFormatter


class RuntimeVisibilityMovementAdapter:
    """Adapter between GameTurnService/MovementService and bundle visibility engines."""

    def __init__(self, campaign_repo: Any = None, project_root: str | Path = ".") -> None:
        self.resolver = RuntimeCampaignBundleResolver(campaign_repo=campaign_repo, project_root=project_root)
        self.intent_parser = RuntimeVisibilityIntentParser()
        self.formatter = VisibilityRuntimeFormatter()

    def try_handle(self, *, channel_id: str, player_id: str, campaign_id: str, text: str) -> Optional[Dict[str, Any]]:
        intent = self.intent_parser.parse(text)
        if intent.kind == "NONE":
            return None
        bundle = self.resolver.resolve(campaign_id)
        if not bundle or not bundle.visibility_available:
            return None
        try:
            return self._handle_with_engine(bundle, channel_id, player_id, intent)
        except Exception as exc:
            return {"handled": True, "ok": False, "text": f"A visibility runtime hibát jelzett: {exc}", "raw": {"error": str(exc)}}

    def _handle_with_engine(self, bundle: ResolvedCampaignBundle, channel_id: str, player_id: str, intent: RuntimeVisibilityIntent) -> Dict[str, Any]:
        if intent.kind == "MAP":
            raw = self._render_map(bundle, channel_id)
            return {"handled": True, "ok": bool(raw.get("ok")), "text": self._format_map(raw), "raw": raw}

        engine = self._create_engine(bundle)
        state = self._load_or_init_state(bundle, channel_id, player_id)

        if intent.kind == "LOOK":
            raw = engine.look(state)
            self._save_state(bundle, channel_id, state)
            return {"handled": True, "ok": bool(raw.get("ok", True)), "text": self.formatter.format_look(raw), "raw": raw}

        if intent.kind == "MOVE":
            if intent.direction == "back":
                raw = self._backtrack(engine, state)
                save_state = self._state_from_raw(raw) or state
                self._save_state(bundle, channel_id, save_state)
                return {"handled": True, "ok": bool(raw.get("ok")), "text": self._format_backtrack(raw), "raw": raw}

            previous_position = self._clone_position(getattr(state, "current", None))
            before_history_len = len(getattr(state, "path_history", []) or [])
            raw = engine.move(state, intent.direction, intent.choice)
            save_state = self._state_from_raw(raw) or state
            if raw.get("ok"):
                self._ensure_previous_position_recorded(save_state, previous_position, before_history_len)
            self._save_state(bundle, channel_id, save_state)
            return {"handled": True, "ok": bool(raw.get("ok")), "text": self.formatter.format_move(raw), "raw": raw}

        if intent.kind == "SEARCH_SECRET":
            raw = self._search_secret(bundle, state)
            self._save_state(bundle, channel_id, state)
            return {"handled": True, "ok": bool(raw.get("ok", True)), "text": self.formatter.format_secret_search(raw), "raw": raw}

        return {"handled": False, "ok": False, "text": "", "raw": {}}

    def _render_map(self, bundle: ResolvedCampaignBundle, channel_id: str) -> Dict[str, Any]:
        from services.runtime_visibility_map_service import RuntimeVisibilityMapService
        return RuntimeVisibilityMapService(bundle.bundle_dir, bundle.campaign_id).render_for_channel(channel_id).to_dict()

    def _format_map(self, raw: Dict[str, Any]) -> str:
        if not raw.get("ok"):
            return str(raw.get("message") or "Nem sikerült elkészíteni a térképet.")
        return (
            f"A látható térképrészlet elkészült.\n"
            f"Fájl: `{raw.get('output_file')}`\n"
            f"Szint: {raw.get('level')}, látható cellák: {raw.get('visible_cells_count')}"
        )

    def _create_engine(self, bundle: ResolvedCampaignBundle) -> Any:
        from services.movement.visibility_aware_movement_engine import VisibilityAwareMovementEngine
        candidates = [
            {"bundle_dir": str(bundle.bundle_dir), "campaign_id": bundle.campaign_id},
            {"bundle_dir": str(bundle.bundle_dir)},
            {"bundle_dir": bundle.bundle_dir},
            {},
        ]
        last_error: Optional[Exception] = None
        for kwargs in candidates:
            try:
                sig = inspect.signature(VisibilityAwareMovementEngine)
                accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}
                return VisibilityAwareMovementEngine(**accepted)
            except Exception as exc:
                last_error = exc
                try:
                    if kwargs:
                        return VisibilityAwareMovementEngine(str(bundle.bundle_dir))
                except Exception as exc2:
                    last_error = exc2
        raise RuntimeError(f"Cannot construct VisibilityAwareMovementEngine: {last_error}")

    def _state_file(self, bundle: ResolvedCampaignBundle, channel_id: str) -> Path:
        safe = str(channel_id).replace("/", "_").replace("\\", "_")
        return bundle.bundle_dir / f"visibility_runtime_state_{safe}.json"

    def _load_or_init_state(self, bundle: ResolvedCampaignBundle, channel_id: str, player_id: str) -> Any:
        from services.visibility.visibility_state_store import VisibilityStateStore
        from models.corridor_visibility_models import VisibilityPosition, VisibilityState

        store = VisibilityStateStore(self._state_file(bundle, channel_id))
        loaded = store.load()
        if loaded:
            self._ensure_history_attr(loaded)
            return loaded

        legacy_last = bundle.bundle_dir / "visibility_runtime_state_last.json"
        if legacy_last.exists():
            loaded = VisibilityStateStore(legacy_last).load()
            if loaded:
                self._ensure_history_attr(loaded)
                store.save(loaded)
                return loaded

        start_room = self._infer_start_room(bundle, channel_id)
        state = VisibilityState(
            campaign_id=bundle.campaign_id,
            current=VisibilityPosition(
                node_id=start_room,
                node_type="room",
                level=self._level_from_room_id(start_room),
                room_id=start_room,
                segment_id=None,
                cell=None,
            ),
            visited_rooms=[start_room],
            visited_segments=[],
            visible_cells=[],
            path_history=[],
        )
        store.save(state)
        return state

    def _save_state(self, bundle: ResolvedCampaignBundle, channel_id: str, state: Any) -> None:
        from services.visibility.visibility_state_store import VisibilityStateStore
        self._ensure_history_attr(state)
        VisibilityStateStore(self._state_file(bundle, channel_id)).save(state)
        try:
            VisibilityStateStore(bundle.bundle_dir / "visibility_runtime_state_last.json").save(state)
        except Exception:
            pass

    def _state_from_raw(self, raw: Dict[str, Any]) -> Optional[Any]:
        if not isinstance(raw, dict) or not isinstance(raw.get("state"), dict):
            return None
        from models.corridor_visibility_models import VisibilityState
        try:
            st = VisibilityState.from_dict(raw["state"]) if hasattr(VisibilityState, "from_dict") else None
            if st:
                self._ensure_history_attr(st)
            return st
        except Exception:
            return None

    def _ensure_history_attr(self, state: Any) -> None:
        if not hasattr(state, "path_history") or getattr(state, "path_history", None) is None:
            try:
                state.path_history = []
            except Exception:
                pass

    def _clone_position(self, position: Any) -> Any:
        if position is None:
            return None
        try:
            if hasattr(position, "to_dict"):
                return self._position_from_any(position.to_dict())
            return copy.deepcopy(position)
        except Exception:
            return position

    def _ensure_previous_position_recorded(self, state: Any, previous_position: Any, before_history_len: int) -> None:
        if previous_position is None:
            return
        self._ensure_history_attr(state)
        if len(state.path_history) > before_history_len:
            return
        if self._same_position(previous_position, getattr(state, "current", None)):
            return
        state.path_history.append(previous_position)

    def _same_position(self, a: Any, b: Any) -> bool:
        if a is None or b is None:
            return False
        return (
            getattr(a, "node_id", None) == getattr(b, "node_id", None)
            and getattr(a, "node_type", None) == getattr(b, "node_type", None)
            and getattr(a, "room_id", None) == getattr(b, "room_id", None)
            and getattr(a, "segment_id", None) == getattr(b, "segment_id", None)
        )

    def _backtrack(self, engine: Any, state: Any) -> Dict[str, Any]:
        self._ensure_history_attr(state)
        history = getattr(state, "path_history", None)
        if not history:
            return {"ok": False, "message": "Nem egyértelmű, merre van vissza. Válassz a látható lehetőségek közül.", "look": engine.look(state).get("look") if hasattr(engine, "look") else None, "state": state.to_dict() if hasattr(state, "to_dict") else None}
        previous_position = self._position_from_any(history.pop())
        if previous_position is None:
            return {"ok": False, "message": "A visszalépési előzmény sérült.", "look": engine.look(state).get("look") if hasattr(engine, "look") else None, "state": state.to_dict() if hasattr(state, "to_dict") else None}
        state.current = previous_position
        self._mark_current_visited(state)
        look_raw = engine.look(state) if hasattr(engine, "look") else {"ok": True, "look": {}}
        return {"ok": True, "message": self._backtrack_message(previous_position), "look": look_raw.get("look") if isinstance(look_raw, dict) else None, "state": state.to_dict() if hasattr(state, "to_dict") else None}

    def _position_from_any(self, value: Any) -> Any:
        from models.corridor_visibility_models import VisibilityPosition
        if isinstance(value, VisibilityPosition):
            return value
        if hasattr(value, "to_dict"):
            value = value.to_dict()
        if isinstance(value, dict):
            if hasattr(VisibilityPosition, "from_dict"):
                return VisibilityPosition.from_dict(value)
            return VisibilityPosition(node_id=value.get("node_id") or value.get("room_id") or value.get("segment_id") or "unknown", node_type=value.get("node_type") or ("room" if value.get("room_id") else "segment"), level=int(value.get("level") or 1), room_id=value.get("room_id"), segment_id=value.get("segment_id"), cell=value.get("cell"))
        return None

    def _mark_current_visited(self, state: Any) -> None:
        current = getattr(state, "current", None)
        if not current:
            return
        room_id = getattr(current, "room_id", None)
        segment_id = getattr(current, "segment_id", None)
        if room_id and hasattr(state, "visited_rooms") and room_id not in state.visited_rooms:
            state.visited_rooms.append(room_id)
        if segment_id and hasattr(state, "visited_segments") and segment_id not in state.visited_segments:
            state.visited_segments.append(segment_id)

    def _backtrack_message(self, position: Any) -> str:
        node_type = getattr(position, "node_type", "")
        if node_type == "room" or getattr(position, "room_id", None):
            return "Visszatértek a korábbi helyiség bejáratához."
        return "Visszaléptek az előző folyosószakaszra."

    def _format_backtrack(self, raw: Dict[str, Any]) -> str:
        if not raw.get("ok"):
            msg = str(raw.get("message") or "Nem sikerült visszalépni.")
            look = raw.get("look")
            return f"{msg}\n\n{self.formatter.format_look({'look': look})}" if isinstance(look, dict) else msg
        msg = str(raw.get("message") or "Visszaléptetek.")
        look = raw.get("look")
        return f"{msg}\n\n{self.formatter.format_look({'look': look})}" if isinstance(look, dict) else msg

    def _infer_start_room(self, bundle: ResolvedCampaignBundle, channel_id: str) -> str:
        import json
        p = bundle.bundle_dir / "visibility_state.json"
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                cur = data.get("current") or {}
                if cur.get("room_id"):
                    return str(cur["room_id"])
            except Exception:
                pass
        room_data = bundle.bundle_dir / "room_data.json"
        data = json.loads(room_data.read_text(encoding="utf-8")) if room_data.exists() else {}
        rooms = data.get("rooms") or []
        return str(rooms[0].get("room_id")) if rooms else f"{bundle.campaign_id}:L01:R001"

    def _level_from_room_id(self, room_id: str) -> int:
        import re
        m = re.search(r":L(\d+):", str(room_id))
        return int(m.group(1)) if m else 1

    def _search_secret(self, bundle: ResolvedCampaignBundle, state: Any) -> Dict[str, Any]:
        from services.visibility.secret_door_discovery_engine import SecretDoorDiscoveryEngine
        from services.visibility.secret_discovery_state_store import SecretDiscoveryStateStore
        store = SecretDiscoveryStateStore(bundle.bundle_dir / "secret_discovery_state.json")
        try:
            discovery = SecretDoorDiscoveryEngine(bundle.bundle_dir, store)
        except Exception:
            discovery = SecretDoorDiscoveryEngine(store)
        current_room = getattr(getattr(state, "current", None), "room_id", None)
        if not current_room:
            return {"ok": False, "message": "Jelenleg nem szobában állsz; menj közelebb egy falhoz vagy ajtóhoz."}
        for name, kwargs in [("search_room", {"room_id": current_room, "trait": "secret", "auto_success": True}), ("search_room", {"room_id": current_room, "trait": "secret", "roll_total": 99, "dc": 1}), ("reveal_room", {"room_id": current_room, "trait": "secret"})]:
            if hasattr(discovery, name):
                try:
                    result = getattr(discovery, name)(**kwargs)
                    if hasattr(result, "to_dict"):
                        return result.to_dict()
                    if isinstance(result, dict):
                        return result
                    return {"ok": True, "found": bool(result), "message": "A keresés lefutott."}
                except TypeError:
                    continue
        return {"ok": False, "message": "A SecretDoorDiscoveryEngine API nem ismert ebben a verzióban."}
