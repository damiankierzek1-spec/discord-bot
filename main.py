import discord

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run('MTUyMjU5NzUwMDQ1NDgzMDE1MA.GR_E9S.rV7JMe3oJ6G1tLTXwVcNOMKZjOIvz7nskzkjvM')
