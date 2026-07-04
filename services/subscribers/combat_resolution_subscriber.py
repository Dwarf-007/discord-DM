
class CombatResolutionSubscriber:

    def __init__(self, bot, party_repo, player_repo):
        self.bot = bot
        self.party_repo = party_repo
        self.player_repo = player_repo

    async def on_all_monsters_defeated(self, payload):

        channel = self.bot.get_channel(int(payload["channel_id"]))

        party = self.party_repo.get_party_members(payload["channel_id"])

        if not party:
            await channel.send("Nincs party.")
            return

        xp = int(payload.get("xp_reward_total", 100))
        xp_each = xp // len(party)

        for p in party:
            self.player_repo.add_xp(channel.id, p, xp_each)

        await channel.send(f"XP kiosztva: {xp_each}/fő")
