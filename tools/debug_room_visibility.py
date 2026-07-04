from __future__ import annotations
import argparse, json
from services.visibility.visibility_engine import CorridorVisibilityEngine
from models.corridor_visibility_models import VisibilityPosition, VisibilityState


def main() -> int:
    p=argparse.ArgumentParser(description='Debug room visibility segments')
    p.add_argument('--bundle-dir', required=True)
    p.add_argument('--room', required=True)
    args=p.parse_args()
    engine=CorridorVisibilityEngine(args.bundle_dir)
    rid=engine.nav_repo.resolve_room_id(args.room) or args.room
    lvl=engine._level_from_room_id(rid)
    state=VisibilityState(campaign_id='', current=VisibilityPosition(rid,'room',lvl,room_id=rid), visited_rooms=[rid])
    print(json.dumps(engine.look(state), ensure_ascii=False, indent=2))
    return 0
if __name__ == '__main__': raise SystemExit(main())
