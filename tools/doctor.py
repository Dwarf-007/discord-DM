
"""
TOOLS/DOCTOR.PY
Command line runtime diagnostics.
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from app.bootstrap import build_runtime
from config import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="AI DM runtime doctor.")
    parser.add_argument("--campaign-id", default="default")
    parser.add_argument("--channel-id", default=None)
    parser.add_argument("--strict", action="store_true", help="Return non-zero on WARN as well as FAIL.")
    args = parser.parse_args()

    load_dotenv()
    config = load_config(require_discord_token=False)
    runtime = build_runtime(config=config)
    report = runtime.runtime_health_service.run_all(campaign_id=args.campaign_id, channel_id=args.channel_id)
    print(report.to_text())
    if report.status == "FAIL":
        return 1
    if args.strict and report.status == "WARN":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
