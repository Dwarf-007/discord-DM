from __future__ import annotations
import argparse, json
from services.generators.generator_runtime_health_service import GeneratorRuntimeHealthService

def main():
    ap=argparse.ArgumentParser(description='Generator stack health check')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--no-playwright', action='store_true')
    a=ap.parse_args()
    report=GeneratorRuntimeHealthService().run_all(include_playwright=not a.no_playwright)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) if a.json else report.to_text())
    return 1 if report.status=='FAIL' else 0
if __name__=='__main__': raise SystemExit(main())
