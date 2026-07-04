"""
DEPRECATED shim for root-level bot_core.py

This module used to contain a (now-obsolete) bot implementation. The maintained
implementation lives in bot/bot_core.py. This shim preserves a compatible
create_bot() function while warning developers not to import the root module.
"""

import warnings

try:
    from bot.bot_core import create_bot as _create_bot  # type: ignore
except Exception:
    _create_bot = None


def create_bot(*args, **kwargs):
    warnings.warn(
        "Deprecated module 'bot_core' imported — use 'bot.bot_core.create_bot' instead.",
        DeprecationWarning,
    )
    if _create_bot is None:
        raise RuntimeError("Active bot implementation not available; import 'bot.bot_core' instead.")
    return _create_bot(*args, **kwargs)
