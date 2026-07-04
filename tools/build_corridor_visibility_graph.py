from __future__ import annotations
import argparse
import json
from services.visibility.visibility_graph_builder import VisibilityGraphBuilder


def main() -> int:
    parser = argparse.ArgumentParser(description='Build merged corridor visibility graph from v3 bundle TSV files')
    parser.add_argument('--bundle-dir', required=True)
    args = parser.parse_args()
    graph = VisibilityGraphBuilder(args.bundle_dir).build_and_save()
    print(json.dumps({
        'status': 'OK',
        'schema_version': graph.get('schema_version'),
        'segments': len(graph.get('segments', {})),
        'rooms_with_segments': len(graph.get('room_to_segments', {})),
        'reports': graph.get('reports', []),
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
