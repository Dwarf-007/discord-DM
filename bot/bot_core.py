"""
BOT/BOT_CORE.PY

Discord bot wiring with Avrae feedback routing, legacy admin commands, and
optional generator/admin Cogs from Sprint 4-9.

This is a compatibility replacement for the uploaded older runtime branch. It
keeps the existing player-message routing intact and only adds safe optional Cog
registration for the generator stack.
"""
from __future__ import annotations

import logging
import discord
from discord.ext import commands

from avrae.avrae_parser import AvraeParserService
from bot.admin_commands import DMAdminCommands
from bot.discord_router import DiscordTurnRouter

logger = logging.getLogger(__name__)


def create_bot(runtime, command_prefix: str = "!"):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    intents.members = True
    bot = commands.Bot(command_prefix=command_prefix, intents=intents)
    router = DiscordTurnRouter(runtime.game_turn_service)

    @bot.event
    async def on_ready():
        print(f"✅ AI DM bot bejelentkezett: {bot.user}")

    @bot.event
    async def setup_hook():
        await bot.add_cog(DMAdminCommands(bot, runtime))
        print("🔧 AI DM admin/debug parancsok betöltve.")
        await _try_add_optional_cogs(bot, runtime)

    @bot.event
    async def on_message(message):
        if message.author.bot:
            if runtime.combat_feedback_service and AvraeParserService.is_avrae_message(message):
                await runtime.combat_feedback_service.process_avrae_message(message)
            await bot.process_commands(message)
            return
        if not message.content:
            await bot.process_commands(message)
            return
        if message.content.startswith(command_prefix):
            await bot.process_commands(message)
            return
        await router.handle_player_message(message)
        await bot.process_commands(message)

    return bot


async def _try_add_optional_cogs(bot, runtime) -> None:
    """Register Sprint 4-9 Cogs when their files are installed.

    Missing generator packages should never prevent the base AI DM bot from
    starting.
    """
    optional_cogs = [
        ("bot.generate_commands", "DMGenerateCommands", "generator CLI/admin commands"),
        ("bot.donjon_web_commands", "DMDonjonWebCommands", "Donjon web commands"),
        ("bot.generator_admin_commands", "DMGeneratorAdminCommands", "generator health/artifacts commands"),
    ]
    for module_name, class_name, label in optional_cogs:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            await bot.add_cog(cls(bot, runtime))
            print(f"🔧 Opcionális Cog betöltve: {label}")
        except ModuleNotFoundError:
            logger.info("Optional Cog module not installed: %s", module_name)
        except Exception:
            logger.exception("Optional Cog registration failed: %s.%s", module_name, class_name)
