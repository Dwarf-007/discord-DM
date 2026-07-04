from __future__ import annotations
import argparse
import json
from services.movement.navigation_repository import NavigationRepository
from services.movement.movement_engine import MovementEngine
from models.movement_models import MovementState


def main() -> int:
    p = argparse.ArgumentParser(description='Debug one room navigation options')
    p.add_argument('--bundle-dir', required=True)
    p.add_argument('--room', required=True)
    args = p.parse_args()
    repo = NavigationRepository(args.bundle_dir)
    rid = repo.resolve_room_id(args.room)
    if not rid:
        raise SystemExit(f'Unknown room: {args.room}')
    state = MovementState(campaign_id='', current_room_id=rid)
    result = MovementEngine(repo).exits(state)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    print('\n---\n' + result.message)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
