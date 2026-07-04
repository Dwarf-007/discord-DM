
"""
TOOLS/RUN_SMOKE_TESTS.PY
Runs available smoke tests in subprocesses.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


SMOKE_TESTS = [
    "tests/smoke_test_game_turn.py",
    "tests/smoke_test_combat_feedback.py",
    "tests/smoke_test_encounter_start.py",
    "tests/smoke_test_navigation.py",
    "tests/smoke_test_trap_movement_failure.py",
    "tests/smoke_test_rest.py",
    "tests/smoke_test_memory.py",
    "tests/smoke_test_admin_debug.py",
    "tests/smoke_test_key_rotation.py",
    "tests/smoke_test_existing_rag_schema.py",
    "tests/smoke_test_campaign_registry.py",
    "tests/smoke_test_room_alias.py",
    "tests/smoke_test_progress.py",
    "tests/smoke_test_runtime_health.py",
]


def main() -> int:
    root = Path.cwd()
    failures: list[str] = []
    for rel_path in SMOKE_TESTS:
        test_path = root / rel_path
        if not test_path.exists():
            print(f"SKIP  {rel_path} (not found)")
            continue
        print(f"RUN   {rel_path}")
        result = subprocess.run([sys.executable, str(test_path)], cwd=str(root), text=True)
        if result.returncode != 0:
            failures.append(rel_path)
            print(f"FAIL  {rel_path}")
        else:
            print(f"OK    {rel_path}")
    if failures:
        print("\nSmoke test failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nAll available smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
