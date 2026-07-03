import discord

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
import os

# Bot pobierze token z bezpiecznych ustawień hostingu
TOKEN = os.environ.get("DISCORD_TOKEN")
client.run(TOKEN)
