from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description='Debug merged corridor visibility graph stats')
    p.add_argument('graph_file')
    args = p.parse_args()
    graph = json.loads(Path(args.graph_file).read_text(encoding='utf-8'))
    segments = graph.get('segments', {})
    types = Counter(seg.get('segment_type') for seg in segments.values())
    lens = [len(seg.get('cells') or []) for seg in segments.values()]
    connected = [len(seg.get('connected_segments') or []) for seg in segments.values()]
    out = {
        'schema_version': graph.get('schema_version'),
        'segments': len(segments),
        'rooms_with_segments': len(graph.get('room_to_segments', {})),
        'segment_types': dict(types),
        'cell_length': {
            'min': min(lens) if lens else 0,
            'max': max(lens) if lens else 0,
            'avg': round(sum(lens) / len(lens), 2) if lens else 0,
        },
        'connectivity_degree': {
            'min': min(connected) if connected else 0,
            'max': max(connected) if connected else 0,
            'avg': round(sum(connected) / len(connected), 2) if connected else 0,
        },
        'reports': graph.get('reports', []),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
