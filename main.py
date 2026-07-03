import discord
import os
from flask import Flask
from threading import Thread

# 1. Tworzymy prosty serwer WWW, na który Render będzie mógł "pukać"
app = Flask('')

@app.route('/')
def home():
    return "Kubusiowo - BOT żyje i działa!"

def run_web_server():
    # Render automatycznie przypisuje port w zmiennej środowiskowej PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# 2. Oryginalny kod Twojego bota
class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)

# 3. Odpalamy serwer WWW i bota
if __name__ == "__main__":
    keep_alive()  # Uruchamia serwer w tle
    TOKEN = os.environ.get("DISCORD_TOKEN")
    client.run(TOKEN)
