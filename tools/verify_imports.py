"""
TOOLS/VERIFY_IMPORTS.PY
Lightweight import verifier for the refactored package layout.
"""

from __future__ import annotations

import importlib


MODULES = [
    "app.bootstrap",
    "bot.bot_core",
    "core.game_events",
    "core.llm_response",
    "repositories.channel_repository",
    "services.game_turn_service",
    "services.context_service",
    "llm.key_manager",
    "llm.gemini_client",
    "llm.provider_router",
    "llm.ollama_adapter",
    "llm.llm_response_parser",
    "avrae.avrae_parser",
    "avrae.avrae_command_builder",
    "config",
    "utils.logging_config",
]


def main() -> int:
    failures: list[tuple[str, str]] = []
    for name in MODULES:
        try:
            importlib.import_module(name)
            print(f"OK    {name}")
        except Exception as exc:
            failures.append((name, repr(exc)))
            print(f"FAIL  {name}: {exc!r}")

    if failures:
        print("\nImport failures:")
        for name, error in failures:
            print(f"- {name}: {error}")
        return 1
    print("\nAll imports passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
