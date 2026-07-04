from __future__ import annotations

import argparse
from services.dungeons.fog_of_war_renderer import FogOfWarRenderer


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a fog-of-war map from map_geometry.json")
    parser.add_argument("--map-geometry", required=True)
    parser.add_argument("--level", type=int, required=True)
    parser.add_argument("--visited", required=True, help="Comma-separated room IDs")
    parser.add_argument("--current-room", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--show-adjacent", action="store_true")
    parser.add_argument("--graph", default=None)
    args = parser.parse_args()
    visited = [x.strip() for x in args.visited.split(",") if x.strip()]
    result = FogOfWarRenderer().render(args.map_geometry, args.level, visited, args.output, current_room_id=args.current_room, show_adjacent=args.show_adjacent, graph_file=args.graph)
    print(result)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
