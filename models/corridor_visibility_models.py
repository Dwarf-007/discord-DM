from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

Cell = Tuple[int, int]

@dataclass
class VisibilitySegment:
    segment_id: str
    level: int
    segment_type: str  # corridor_segment | junction | doorway | stair | dead_end
    cells: List[Cell] = field(default_factory=list)
    endpoints: List[Cell] = field(default_factory=list)
    connected_segments: List[str] = field(default_factory=list)
    adjacent_rooms: List[str] = field(default_factory=list)
    direction_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['cells'] = [[r, c] for r, c in self.cells]
        data['endpoints'] = [[r, c] for r, c in self.endpoints]
        return data

@dataclass
class VisibilityPosition:
    node_id: str
    node_type: str  # room | segment
    level: int
    room_id: Optional[str] = None
    segment_id: Optional[str] = None
    cell: Optional[Cell] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.cell is not None:
            data['cell'] = [self.cell[0], self.cell[1]]
        return data

@dataclass
class VisibilityState:
    campaign_id: str
    current: VisibilityPosition
    visited_rooms: List[str] = field(default_factory=list)
    visited_segments: List[str] = field(default_factory=list)
    visible_cells: List[Cell] = field(default_factory=list)
    path_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['current'] = self.current.to_dict()
        data['visible_cells'] = [[r, c] for r, c in self.visible_cells]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VisibilityState':
        cur = data.get('current') or {}
        pos = VisibilityPosition(
            node_id=str(cur.get('node_id') or ''),
            node_type=str(cur.get('node_type') or 'room'),
            level=int(cur.get('level') or 1),
            room_id=cur.get('room_id'),
            segment_id=cur.get('segment_id'),
            cell=tuple(cur['cell']) if cur.get('cell') else None,
        )
        return cls(
            campaign_id=str(data.get('campaign_id') or ''),
            current=pos,
            visited_rooms=list(data.get('visited_rooms') or []),
            visited_segments=list(data.get('visited_segments') or []),
            visible_cells=[tuple(x) for x in (data.get('visible_cells') or [])],
            path_history=list(data.get('path_history') or []),
        )
