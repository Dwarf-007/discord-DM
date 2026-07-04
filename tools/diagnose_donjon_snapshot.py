from __future__ import annotations
import argparse, json
from pathlib import Path
from services.generators.export_discovery import ExportDiscovery
from services.generators.selector_diagnostics import SelectorDiagnostics

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('html_file'); ap.add_argument('--base-url', default=''); ap.add_argument('--output-dir')
    a=ap.parse_args(); out=Path(a.output_dir) if a.output_dir else Path(a.html_file).parent; out.mkdir(parents=True, exist_ok=True)
    diag=SelectorDiagnostics().analyze_file(a.html_file, out/'selector_diagnostics.json')
    disc=ExportDiscovery().discover_file(a.html_file, a.base_url, out/'export_discovery.json')
    print(json.dumps({'selector_diagnostics':diag.to_dict(),'export_discovery':disc.to_dict()}, ensure_ascii=False, indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
