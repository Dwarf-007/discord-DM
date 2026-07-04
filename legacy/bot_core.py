"""
LEGACY: root-level bot_core.py

Ez a fájl az eredeti, gyökérben lévő bot_core.py tartalmát tartalmazza. Áthelyezés célja: a működő és karbantartott implementáció a bot/bot_core.py alatt található. Ne használd ezt a fájlt új kódok importálására; ez csak az eredeti tartalom archiválására szolgál.
"""

import discord
from discord.ext import commands

from core.game_events import EventBus, GameEvent, EventTypes
from services.game_turn_service import GameTurnService
from services.combat_feedback_service import CombatFeedbackService
from services.subscribers.combat_resolution_subscriber import CombatResolutionSubscriber
from repositories.party_repository import PartyRepository

import database as db

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

event_bus = EventBus()
eventchestrator = StateOrchestrator(channel_repo, event_bus)

party_repo = PartyRepository(db)
combat_repo = None  # use your own
player_repo = None  # use your own

combat_feedback = CombatFeedbackService(combat_repo, event_bus)

turn_service = GameTurnService(event_bus, combat_feedback)

subscriber = CombatResolutionSubscriber(bot, party_repo, player_repo)

event_bus.register(EventTypes.STATE_CHANGED, logging_subscriber.on_state_changed)
event_bus.register(EventTypes.COMBAT_START, logging_subscriber.on_combat_started)
event_bus.register(EventTypes.PLAYER_MOVED, logging_subscriber.on_player_moved)

event_bus.register(
    EventTypes.ALL_MONSTERS_DEFEATED,
    combat_resolution_subscriber.on_all_monsters_defeated
)

event_bus.register(
    EventTypes.COMBAT_ENDED,
    combat_resolution_subscriber.on_combat_ended
)


@bot.event
async def on_message(message):

    if message.author.bot:
        await combat_feedback.process_avrae_message(message)
        return

    await turn_service.process_turn(message, [str(message.author.id)])

    await bot.process_commands(message)
