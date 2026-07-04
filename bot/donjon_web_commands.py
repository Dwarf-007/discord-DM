"""Optional Discord Cog for Donjon web generation commands."""

from __future__ import annotations

from discord.ext import commands

from services.generators.donjon_web_command_parser import DonjonWebCommandParser
from services.generators.donjon_web_pipeline import DonjonWebPipeline


class DMDonjonWebCommands(commands.Cog):
    def __init__(self, bot, runtime):
        self.bot = bot
        self.runtime = runtime
        self.parser = DonjonWebCommandParser()
        self.pipeline = DonjonWebPipeline(runtime=runtime, llm_adapter=getattr(runtime, "llm_adapter", None))

    async def cog_check(self, ctx):
        return bool(ctx.guild and (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild))

    async def _send_chunked(self, ctx, text: str, chunk_size: int = 1800):
        value = str(text or "")
        for index in range(0, max(len(value), 1), chunk_size):
            await ctx.send(value[index:index + chunk_size] or "Nincs megjeleníthető adat.")

    @commands.command(name="dm_generate_donjon_web")
    async def dm_generate_donjon_web(self, ctx, *, args: str = ""):
        try:
            request, options = self.parser.parse(args)
            result = self.pipeline.generate_campaign_from_web(
                web_request=request,
                enrich=options.get("enrich", True),
                import_to_runtime=options.get("import_to_runtime", False),
                clear_rag=options.get("clear_rag", False),
                max_rooms=options.get("max_rooms"),
            )
            text = "**Donjon web generation finished**\n" + "```json\n" + str(result)[:1600] + "\n```"
        except Exception as exc:
            text = f"Donjon web generálás sikertelen: `{type(exc).__name__}: {exc}`\n" + self.help_text()
        await self._send_chunked(ctx, text)

    @staticmethod
    def help_text() -> str:
        return (
            "Használat:\n"
            "`!dm_generate_donjon_web sakka --name \"Sakka\" --theme Undead --size Large --import --clear-rag`\n"
            "Megjegyzés: a szerveren Playwright + Chromium szükséges."
        )
