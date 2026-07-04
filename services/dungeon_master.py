
"""
DUNGEON_MASTER.PY

Stateless dungeon lookup + room graph + navigation engine.

Responsibilities:
- Load and expose immutable dungeon map data
- Resolve room lookups by explicit room_id
- Detect valid movement based on the current room and player message
- Expose room exits and monster presence without storing runtime state
- Build a room graph from the immutable map
- Compute shortest routes between rooms
- Resolve destination lookup by room title fragment

IMPORTANT:
- This service is intentionally stateless
- It does not persist channel state
- It does not own the current room
- It does not track combat flags
- All runtime state must live in repositories / database layer
"""

from __future__ import annotations

import json
import os
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# GRAPH MODELS
# =============================================================================

@dataclass(frozen=True)
class RoomNode:
    """
    Immutable room node built from dungeon map data.
    """
    room_id: str
    title: str
    exits: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteStep:
    """
    One navigation step in a computed path.
    """
    from_room_id: str
    direction: str
    to_room_id: str


@dataclass(frozen=True)
class RouteResult:
    """
    Result of a graph pathfinding operation.
    """
    found: bool
    start_room_id: str
    target_room_id: Optional[str]
    steps: List[RouteStep] = field(default_factory=list)


# =============================================================================
# ROOM GRAPH BUILDER
# =============================================================================

class RoomGraphBuilder:
    """
    Builds a directed room graph from the immutable dungeon map structure.
    """

    def __init__(self, dungeon_map: Dict[str, Dict[str, Any]]) -> None:
        self._dungeon_map = dungeon_map or {}
        self._graph = self._build_graph()

    def _build_graph(self) -> Dict[str, RoomNode]:
        graph: Dict[str, RoomNode] = {}

        for room_id, room_data in self._dungeon_map.items():
            if not isinstance(room_data, dict):
                continue

            title = str(room_data.get("title") or room_id)
            exits = room_data.get("exits", {})
            exits = dict(exits) if isinstance(exits, dict) else {}

            normalized_exits: Dict[str, str] = {}
            for direction, target_room_id in exits.items():
                if not direction or not target_room_id:
                    continue
                normalized_exits[str(direction).strip()] = str(target_room_id).strip()

            graph[str(room_id)] = RoomNode(
                room_id=str(room_id),
                title=title,
                exits=normalized_exits,
            )

        return graph

    def get_graph(self) -> Dict[str, RoomNode]:
        return dict(self._graph)

    def get_room(self, room_id: Optional[str]) -> Optional[RoomNode]:
        if not room_id:
            return None
        return self._graph.get(str(room_id))

    def room_exists(self, room_id: Optional[str]) -> bool:
        return self.get_room(room_id) is not None

    def get_exits(self, room_id: Optional[str]) -> Dict[str, str]:
        room = self.get_room(room_id)
        if not room:
            return {}
        return dict(room.exits)

    def validate_graph(self) -> Dict[str, List[str]]:
        """
        Returns structural validation information.

        warnings:
        - dangling exits (target room missing)
        - rooms without exits
        """
        dangling_exits: List[str] = []
        rooms_without_exits: List[str] = []

        for room_id, node in self._graph.items():
            if not node.exits:
                rooms_without_exits.append(room_id)

            for direction, target_room_id in node.exits.items():
                if target_room_id not in self._graph:
                    dangling_exits.append(
                        f"{room_id} --[{direction}]--> {target_room_id}"
                    )

        return {
            "dangling_exits": dangling_exits,
            "rooms_without_exits": rooms_without_exits,
        }

    def get_reverse_edges(self) -> Dict[str, List[str]]:
        reverse_edges: Dict[str, List[str]] = defaultdict(list)

        for room_id, node in self._graph.items():
            for _direction, target_room_id in node.exits.items():
                reverse_edges[target_room_id].append(room_id)

        return dict(reverse_edges)

    def find_room_ids_by_title(self, title_fragment: str) -> List[str]:
        """
        Simple title lookup helper for navigation by destination name.
        """
        if not title_fragment:
            return []

        query = title_fragment.casefold().strip()
        results: List[str] = []

        for room_id, node in self._graph.items():
            if query in node.title.casefold():
                results.append(room_id)

        return results


# =============================================================================
# NAVIGATION ENGINE
# =============================================================================

class NavigationEngine:
    """
    Navigation logic on top of the room graph.

    Responsibilities:
    - resolve immediate directional movement
    - parse rough direction aliases
    - find shortest route between rooms
    - generate human-readable navigation hints
    """

    DIRECTION_ALIASES: Dict[str, List[str]] = {
        "north": ["north", "n", "észak", "északra"],
        "south": ["south", "s", "dél", "délre"],
        "east": ["east", "e", "kelet", "keletre"],
        "west": ["west", "w", "nyugat", "nyugatra"],
        "up": ["up", "u", "felfelé", "fel", "létra fel"],
        "down": ["down", "d", "lefelé", "le", "létra le", "csapóajtón le"],
    }

    def __init__(self, graph_builder: RoomGraphBuilder) -> None:
        self.graph_builder = graph_builder

    # ------------------------------------------------------------------
    # Immediate movement
    # ------------------------------------------------------------------

    def resolve_direction_from_message(self, message_content: str) -> Optional[str]:
        if not message_content:
            return None

        message = message_content.casefold()

        for canonical, aliases in self.DIRECTION_ALIASES.items():
            for alias in aliases:
                if alias in message:
                    return canonical

        return None

    def resolve_direct_movement(
        self,
        current_room_id: Optional[str],
        message_content: str,
    ) -> Dict[str, Optional[str]]:
        """
        Resolves a single-step movement from a player message.
        """
        exits = self.graph_builder.get_exits(current_room_id)
        if not exits:
            return {
                "moved": False,
                "previous_room_id": current_room_id,
                "next_room_id": None,
                "direction": None,
            }

        message = (message_content or "").casefold()

        # 1) Exact exit label match first
        for direction_label, target_room_id in exits.items():
            if str(direction_label).casefold() in message:
                return {
                    "moved": True,
                    "previous_room_id": current_room_id,
                    "next_room_id": target_room_id,
                    "direction": direction_label,
                }

        # 2) Canonical alias fallback
        canonical_direction = self.resolve_direction_from_message(message_content)
        if canonical_direction:
            for direction_label, target_room_id in exits.items():
                if canonical_direction in direction_label.casefold():
                    return {
                        "moved": True,
                        "previous_room_id": current_room_id,
                        "next_room_id": target_room_id,
                        "direction": direction_label,
                    }

        return {
            "moved": False,
            "previous_room_id": current_room_id,
            "next_room_id": None,
            "direction": None,
        }

    # ------------------------------------------------------------------
    # Pathfinding
    # ------------------------------------------------------------------

    def find_shortest_route(
        self,
        start_room_id: str,
        target_room_id: str,
    ) -> RouteResult:
        if not self.graph_builder.room_exists(start_room_id):
            return RouteResult(
                found=False,
                start_room_id=start_room_id,
                target_room_id=target_room_id,
            )

        if not self.graph_builder.room_exists(target_room_id):
            return RouteResult(
                found=False,
                start_room_id=start_room_id,
                target_room_id=target_room_id,
            )

        if start_room_id == target_room_id:
            return RouteResult(
                found=True,
                start_room_id=start_room_id,
                target_room_id=target_room_id,
                steps=[],
            )

        queue = deque([start_room_id])
        visited = {start_room_id}
        parent: Dict[str, Tuple[str, str]] = {}
        # parent[child] = (parent_room_id, direction_label)

        while queue:
            room_id = queue.popleft()
            exits = self.graph_builder.get_exits(room_id)

            for direction_label, next_room_id in exits.items():
                if next_room_id in visited:
                    continue

                visited.add(next_room_id)
                parent[next_room_id] = (room_id, direction_label)

                if next_room_id == target_room_id:
                    return self._reconstruct_route(
                        start_room_id=start_room_id,
                        target_room_id=target_room_id,
                        parent=parent,
                    )

                queue.append(next_room_id)

        return RouteResult(
            found=False,
            start_room_id=start_room_id,
            target_room_id=target_room_id,
        )

    def _reconstruct_route(
        self,
        start_room_id: str,
        target_room_id: str,
        parent: Dict[str, Tuple[str, str]],
    ) -> RouteResult:
        steps_reversed: List[RouteStep] = []
        current = target_room_id

        while current != start_room_id:
            previous_room_id, direction_label = parent[current]
            steps_reversed.append(
                RouteStep(
                    from_room_id=previous_room_id,
                    direction=direction_label,
                    to_room_id=current,
                )
            )
            current = previous_room_id

        steps = list(reversed(steps_reversed))
        return RouteResult(
            found=True,
            start_room_id=start_room_id,
            target_room_id=target_room_id,
            steps=steps,
        )

    # ------------------------------------------------------------------
    # Human-readable helpers
    # ------------------------------------------------------------------

    def render_route_text(self, route: RouteResult) -> str:
        if not route.found:
            return "Nem találtam útvonalat a célhoz."

        if not route.steps:
            return "Már a célhelyszínen vagytok."

        parts: List[str] = []
        for index, step in enumerate(route.steps, 1):
            target_room = self.graph_builder.get_room(step.to_room_id)
            target_title = target_room.title if target_room else step.to_room_id
            parts.append(f"{index}. {step.direction} → {target_title} ({step.to_room_id})")

        return "\n".join(parts)

    def resolve_destination_by_title(
        self,
        destination_text: str,
    ) -> List[str]:
        return self.graph_builder.find_room_ids_by_title(destination_text)


# =============================================================================
# DUNGEON MASTER SERVICE
# =============================================================================

class DungeonMasterService:
    """
    Stateless helper around the immutable dungeon map.

    Runtime state such as:
    - current room
    - current combat state
    - active campaign progression
    must be stored outside this service (for example in
    ChannelRepository / SQLite channel state), then supplied explicitly.
    """

    def __init__(self, map_filename: str = "dungeon_map.json") -> None:
        """
        Initializes the service and loads the dungeon map once.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.map_path = os.path.join(base_dir, map_filename)
        self.dungeon_map = self._load_map()

        self.room_graph_builder = RoomGraphBuilder(self.dungeon_map)
        self.navigation_engine = NavigationEngine(self.room_graph_builder)

    def _load_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads the dungeon map JSON into memory.

        Returns:
            Dictionary keyed by room_id.

        Raises:
            FileNotFoundError: If the map file does not exist.
            ValueError: If the loaded JSON root is not a dictionary.
        """
        if not os.path.exists(self.map_path):
            raise FileNotFoundError(f"A térképfájl nem található: {self.map_path}")

        with open(self.map_path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)

        if not isinstance(data, dict):
            raise ValueError("A dungeon map gyökérelemének szótárnak kell lennie.")

        return data

    # ------------------------------------------------------------------
    # Existing stateless room helpers
    # ------------------------------------------------------------------

    def get_room_data(self, room_id: Optional[str]) -> Dict[str, Any]:
        """
        Returns all known data for the specified room.

        Args:
            room_id: Explicit room identifier.

        Returns:
            Room data dictionary, or an empty dictionary if the room is unknown.
        """
        if not room_id:
            return {}

        room = self.dungeon_map.get(str(room_id), {})
        return dict(room) if isinstance(room, dict) else {}

    def room_exists(self, room_id: Optional[str]) -> bool:
        """
        Returns whether the given room exists in the loaded map.
        """
        return self.room_graph_builder.room_exists(room_id)

    def get_available_exits(self, room_id: Optional[str]) -> Dict[str, str]:
        """
        Returns the available exits for the specified room.

        Args:
            room_id: Explicit room identifier.

        Returns:
            Mapping of direction -> target room_id.
        """
        return self.room_graph_builder.get_exits(room_id)

    def get_available_exits_text(self, room_id: Optional[str]) -> str:
        """
        Returns exits as a human-readable comma-separated string.

        Args:
            room_id: Explicit room identifier.

        Returns:
            Comma-separated exit list, or fallback message.
        """
        exits = self.get_available_exits(room_id)
        if not exits:
            return "Nincs látható kijárat."

        return ", ".join(exits.keys())

    def has_hostile_monsters(self, room_id: Optional[str]) -> bool:
        """
        Returns whether the specified room contains hostile monsters.

        Args:
            room_id: Explicit room identifier.

        Returns:
            True if the room has at least one monster entry, otherwise False.
        """
        room_data = self.get_room_data(room_id)
        monsters = room_data.get("monsters", [])
        return isinstance(monsters, list) and len(monsters) > 0

    def get_room_title(self, room_id: Optional[str]) -> str:
        """
        Returns the room title, or a fallback value if unavailable.
        """
        room = self.room_graph_builder.get_room(room_id)
        if room:
            return room.title

        room_data = self.get_room_data(room_id)
        title = room_data.get("title")
        return str(title) if title else "Ismeretlen helyszín"

    def get_starting_room_id(self) -> Optional[str]:
        """
        Returns a deterministic starting room identifier.

        Current strategy:
        - if the canonical level_1_room_4 exists, use it
        - otherwise return the first map key
        - if the map is empty, return None
        """
        if "level_1_room_4" in self.dungeon_map:
            return "level_1_room_4"

        for room_id in self.dungeon_map.keys():
            return str(room_id)

        return None

    # ------------------------------------------------------------------
    # Movement resolution (backward-compatible)
    # ------------------------------------------------------------------

    def check_movement(
        self,
        current_room_id: Optional[str],
        message_content: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Checks whether the player message contains a valid movement direction.

        Args:
            current_room_id: Explicit current room identifier.
            message_content: Raw player message.

        Returns:
            Tuple of (next_room_id, matched_direction), or (None, None)
            if no valid movement is found.
        """
        movement = self.navigation_engine.resolve_direct_movement(
            current_room_id=current_room_id,
            message_content=message_content,
        )

        return movement["next_room_id"], movement["direction"]

    def resolve_movement(
        self,
        current_room_id: Optional[str],
        message_content: str,
    ) -> Dict[str, Any]:
        """
        Resolves movement in one call and returns a structured result object.

        Args:
            current_room_id: Explicit current room identifier.
            message_content: Raw player message.

        Returns:
            Dictionary with keys:
            - moved: bool
            - previous_room_id: Optional[str]
            - next_room_id: Optional[str]
            - direction: Optional[str]
            - room_data: Dict[str, Any]
        """
        movement = self.navigation_engine.resolve_direct_movement(
            current_room_id=current_room_id,
            message_content=message_content,
        )

        next_room_id = movement["next_room_id"]
        if not next_room_id:
            return {
                "moved": False,
                "previous_room_id": current_room_id,
                "next_room_id": None,
                "direction": None,
                "room_data": self.get_room_data(current_room_id),
            }

        return {
            "moved": True,
            "previous_room_id": current_room_id,
            "next_room_id": next_room_id,
            "direction": movement["direction"],
            "room_data": self.get_room_data(next_room_id),
        }

    # ------------------------------------------------------------------
    # Graph / navigation features
    # ------------------------------------------------------------------

    def get_graph_validation_report(self) -> Dict[str, List[str]]:
        """
        Returns graph structure validation warnings.
        """
        return self.room_graph_builder.validate_graph()

    def get_route_to_room_id(
        self,
        current_room_id: Optional[str],
        target_room_id: str,
    ) -> str:
        """
        Returns a human-readable route from current room to explicit target room_id.
        """
        if not current_room_id:
            return "Nincs aktuális helyszín."

        route = self.navigation_engine.find_shortest_route(
            start_room_id=str(current_room_id),
            target_room_id=str(target_room_id),
        )
        return self.navigation_engine.render_route_text(route)

    def get_route_to_room_title(
        self,
        current_room_id: Optional[str],
        destination_text: str,
    ) -> str:
        """
        Returns a human-readable route from current room to the first room
        whose title contains the provided text fragment.
        """
        if not current_room_id:
            return "Nincs aktuális helyszín."

        matches = self.navigation_engine.resolve_destination_by_title(destination_text)
        if not matches:
            return "Nem találtam ilyen célhelyszínt."

        route = self.navigation_engine.find_shortest_route(
            start_room_id=str(current_room_id),
            target_room_id=matches[0],
        )
        return self.navigation_engine.render_route_text(route)

    def find_room_ids_by_title(self, title_fragment: str) -> List[str]:
        """
        Title fragment based lookup helper.
        """
        return self.room_graph_builder.find_room_ids_by_title(title_fragment)
