from __future__ import annotations
import argparse
import json
from pathlib import Path

from services.visibility.player_look_sanitizer import PlayerLookSanitizer


def main() -> int:
    p = argparse.ArgumentParser(description='Sanitize a saved movement look JSON file for player output')
    p.add_argument('input_json')
    p.add_argument('--output', default=None)
    p.add_argument('--include-dm', action='store_true')
    args = p.parse_args()

    data = json.loads(Path(args.input_json).read_text(encoding='utf-8'))
    sanitizer = PlayerLookSanitizer()
    if 'look' in data:
        data['look'] = sanitizer.sanitize_look(data['look'], include_dm=args.include_dm)
    else:
        data = sanitizer.sanitize_look(data, include_dm=args.include_dm)

    out_text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out_text, encoding='utf-8')
    print(out_text)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
