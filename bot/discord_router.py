"""
BOT/DISCORD_ROUTER.PY
Discord adapter helpers for sending TurnOutput.

This module is intentionally thin: all game logic remains in services/.
"""

from __future__ import annotations

from core.turn_output import TurnOutput


class DiscordTurnRouter:
    def __init__(self, game_turn_service) -> None:
        self.game_turn_service = game_turn_service

    async def handle_player_message(self, message) -> None:
        output = self.game_turn_service.process(
            channel_id=str(message.channel.id),
            player_id=str(message.author.id),
            text=message.content or "",
        )
        await self.send_turn_output(message, output)

    async def send_turn_output(self, message, output: TurnOutput) -> None:
        if output.public_narrative:
            await message.channel.send(output.public_narrative)

        for command in output.avrae_commands:
            await message.channel.send(command)

        for secret in output.secret_messages:
            await self._send_secret_message(message, secret.player_id, secret.text)

    @staticmethod
    async def _send_secret_message(message, player_id: str, text: str) -> None:
        try:
            guild = getattr(message, "guild", None)
            member = guild.get_member(int(player_id)) if guild else None
            user = member or await message.client.fetch_user(int(player_id))
            if user:
                await user.send(f"👁️ **Titkos információ:**\n{text}")
        except Exception:
            # Do not break the public game flow if a DM cannot be delivered.
            await message.channel.send(f"⚠️ Nem sikerült privát üzenetet küldeni ennek a játékosnak: <@{player_id}>")
