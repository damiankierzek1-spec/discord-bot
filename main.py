import discord
import os
import xml.etree.ElementTree as ET
from flask import Flask, request
from threading import Thread

app = Flask('')

# Pamięć podręczna na ID filmów, żeby bot nie wysyłał spamu (duplikatów)
PROCESSED_VIDEOS = set()

# Weryfikacja subskrypcji od Google (wymagana przez YouTube)
@app.route('/youtube', methods=['GET'])
def youtube_verify():
    challenge = request.args.get('hub.challenge')
    if challenge:
        return challenge, 200
    return "Brak challenge", 400

# Odbieranie powiadomienia o nowym filmie z YouTube
@app.route('/youtube', methods=['POST'])
def youtube_webhook():
    try:
        xml_data = request.data
        root = ET.fromstring(xml_data)
        
        # Przestrzenie nazw w pliku XML od YT
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015'
        }
        
        entry = root.find('atom:entry', namespaces)
        if entry is not None:
            video_id = entry.find('yt:videoId', namespaces).text
            title = entry.find('atom:title', namespaces).text
            link = entry.find('atom:link', namespaces).attrib['href']
            
            # Sprawdzamy, czy film nie był już wysłany
            if video_id not in PROCESSED_VIDEOS:
                PROCESSED_VIDEOS.add(video_id)
                
                # Wysyłamy powiadomienie na Discordzie przez bota
                if client.is_ready():
                    channel = client.get_channel(DISCORD_CHANNEL_ID)
                    if channel:
                        # Treść wiadomości wysyłanej na Discordzie
                        msg = f"🚀 **Nowy film na kanale!** \n🎬 **{title}**\n👉 Oglądaj tutaj: {link}"
                        client.loop.create_task(channel.send(msg))
                        print(f"Wysłano powiadomienie o filmie: {title}")
                        
    except Exception as e:
        print(f"Błąd podczas odbierania danych z YT: {e}")
        
    return "Odebrano", 200

@app.route('/')
def home():
    return "Kubusiowo - BOT żyje i działa!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

intents = discord.Intents.default()
intents.message_content = True
client = Client(intents=intents)

if __name__ == "__main__":
    keep_alive()
    
    # === KONFIGURACJA KANAŁÓW ===
    # 1. Wklej TUTAJ ID swojego kanału tekstowego na Discordzie (same cyfry, bez cudzysłowu!)
    DISCORD_CHANNEL_ID = 1047814798978592788  
    
    # 2. ID Twojego kanału YouTube (zostaw tak jak jest, już wyciągnięte!)
    YT_CHANNEL_ID = 'UCm1fX1O8H1jG5rFq4_o-0xw'
    
    TOKEN = os.environ.get("DISCORD_TOKEN")
    client.run(TOKEN)
