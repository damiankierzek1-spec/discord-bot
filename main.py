import discord
from discord import app_commands, Intents, Embed, File
from discord.ui import Button, View, Modal, TextInput
import os
import json
import random
import io
import asyncio
from datetime import datetime, timedelta
from typing import List
from flask import Flask, render_template_string, request, redirect, session, jsonify, Response
from PIL import Image, ImageDraw, ImageFont

# ===============================
# 🚨 KONFIGURACJA GLOBALNA 🚨
# ===============================

ADMIN_IDS: List[int] = [652507356105539585, 550959315700154368, 590215623259193371]
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PWD", "Kuba123!")
ARCHIVE_FILE = "ticket_archive.json"

# Inicjalizacja aplikacji Flask
app = Flask('')
app.secret_key = os.environ.get("FLASK_SECRET", "super-tajny-klucz-kubusiowo")

# Globalny stan bota
current_status_text = "Zarządzanie serwerem"
ticket_data_cache = {}
captcha_sessions = {}

def load_archive():
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f: 
                return json.load(f)
        except: 
            return []
    return []

def save_whole_archive(archive_data):
    with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f: 
        json.dump(archive_data, f, ensure_ascii=False, indent=4)

# ===============================
# 🤖 ARCHITEKTURA BOTA (discord.py)
# ===============================

class ManagementBot(discord.Client):
    def __init__(self):
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(intents=intents)
        # Drzewo komend aplikacji (Slash Commands)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Uruchomienie Flaska w pętli asynchronicznej bota
        self.loop.create_task(run_flask())

bot = ManagementBot()

# ===============================
# 🛠️ SYSTEM KOMEND UKOŚNIKA (Slash Commands)
# ===============================

@bot.tree.command(name="sync", description="Synchronizuje komendy ukośnika z API Discorda (Tylko Admin)")
async def sync_commands(interaction: discord.Interaction):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Nie posiadasz uprawnień do synchronizacji sieciowej.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    try:
        synced = await bot.tree.sync()
        await interaction.followup.send(f"✅ Pomyślnie zsynchronizowano {len(synced)} komend globalnie.")
    except Exception as e:
        await interaction.followup.send(f"❌ Błąd synchronizacji: {e}")

@bot.tree.command(name="status", description="Zmienia status aktywności bota")
@app_commands.describe(tekst="Nowa treść statusu bota")
async def change_status(interaction: discord.Interaction, tekst: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień developerskich.", ephemeral=True)
        return
    
    global current_status_text
    current_status_text = tekst
    await bot.change_presence(activity=discord.Game(name=tekst))
    await interaction.response.send_message(f"✅ Status bota został zmieniony na: `Playing {tekst}`")

@bot.tree.command(name="clear", description="Czyści określoną ilość wiadomości na kanale")
@app_commands.describe(ilosc="Ilość wiadomości do usunięcia")
async def clear_messages(interaction: discord.Interaction, ilosc: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Wymagane uprawnienia: Zarządzanie Wiadomościami.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=ilosc)
    await interaction.followup.send(f"🗑️ Usunięto {len(deleted)} wiadomości.")

@bot.event
async def on_ready():
    print(f"⚡ Zalogowano jako {bot.user} | Gotowy na komendy /")
    await bot.change_presence(activity=discord.Game(name=current_status_text))

# ===============================
# 🎨 ANiMOWANE I BOGATE STYLE CSS (CYBERPUNK GLOW SYSTEM)
# ===============================

SHARED_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght=300;400;500;600;700&display=swap');
    
    :root {
        --bg-gradient: radial-gradient(circle at 50% 50%, #080512 0%, #020105 100%);
        --primary-glow: #5865f2;
        --accent-neon: #00f2fe;
        --danger-neon: #ff007f;
        --warning-neon: #ffae00;
        --panel-bg: rgba(10, 7, 22, 0.55);
        --border-glow: rgba(88, 101, 242, 0.2);
    }

    body { 
        font-family: 'Space Grotesk', sans-serif; 
        background: var(--bg-gradient);
        color: #e2e8f0; 
        min-height: 100vh; 
        margin: 0;
        overflow-x: hidden;
        position: relative;
    }

    #space-canvas {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: 0; pointer-events: none;
    }

    .animated-bg {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: -1;
        background: radial-gradient(circle at 15% 25%, rgba(88, 101, 242, 0.15) 0%, transparent 45%),
                    radial-gradient(circle at 85% 75%, rgba(0, 242, 254, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 50% 50%, rgba(255, 0, 127, 0.05) 0%, transparent 40%);
        filter: blur(80px);
        animation: pulseBackground 20s ease-in-out infinite alternate;
    }

    @keyframes pulseBackground {
        0% { transform: scale(1) translate(0, 0); }
        100% { transform: scale(1.1) translate(10px, -10px); }
    }

    .dashboard-container { display: flex; min-height: 100vh; position: relative; z-index: 1; }
    
    .sidebar { 
        width: 280px; 
        background: rgba(8, 5, 18, 0.75); 
        border-right: 1px solid var(--border-glow); 
        backdrop-filter: blur(30px); 
        padding: 2.5rem 1.5rem; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between;
        box-shadow: 8px 0 35px rgba(0,0,0,0.6);
        z-index: 2;
    }

    .main-content { flex: 1; padding: 3rem; overflow-y: auto; height: 100vh; position: relative; z-index: 1; }

    .menu-list a { 
        color: #8a8da4; 
        padding: 0.9rem 1.2rem; 
        border-radius: 12px; 
        margin-bottom: 0.6rem; 
        display: flex; 
        align-items: center; 
        gap: 14px; 
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
        font-weight: 500;
        border: 1px solid transparent;
    }
    .menu-list a:hover {
        color: #fff;
        background: rgba(255, 255, 255, 0.04);
        transform: translateX(6px);
        border-color: rgba(88, 101, 242, 0.2);
        box-shadow: 0 0 15px rgba(88, 101, 242, 0.1);
    }
    .menu-list a.is-active { 
        background: linear-gradient(90deg, rgba(88, 101, 242, 0.25) 0%, rgba(88, 101, 242, 0.02) 100%); 
        color: #fff; 
        border-left: 4px solid var(--primary-glow);
        padding-left: 14px;
        text-shadow: 0 0 15px rgba(88, 101, 242, 0.6);
        border-color: rgba(88, 101, 242, 0.3);
    }

    .glass-box { 
        background: var(--panel-bg); 
        border: 1px solid var(--border-glow); 
        border-radius: 20px; 
        backdrop-filter: blur(20px); 
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.5);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
    }
    .glass-box:hover {
        border-color: rgba(88, 101, 242, 0.4);
        box-shadow: 0 25px 55px rgba(88, 101, 242, 0.15);
        transform: translateY(-3px);
    }

    .glow-text { 
        color: #fff; 
        text-shadow: 0 0 15px rgba(88, 101, 242, 0.8), 0 0 30px rgba(88, 101, 242, 0.3); 
    }

    .btn-glow { 
        background: linear-gradient(135deg, #6c7fff, #5865f2); 
        color: white; border: none; font-weight: 600; border-radius: 10px; 
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
        box-shadow: 0 4px 20px rgba(88, 101, 242, 0.4);
    }
    .btn-glow:hover { 
        background: linear-gradient(135deg, #5865f2, #4752c4); 
        transform: translateY(-2px); 
        box-shadow: 0 6px 25px rgba(88, 101, 242, 0.7); 
        color: white; 
    }

    .btn-danger-glow { 
        background: linear-gradient(135deg, #ff4757, #ff0055); 
        color: white; border: none; font-weight: 600; border-radius: 10px; transition: all 0.3s ease; 
        box-shadow: 0 4px 15px rgba(255, 0, 85, 0.3);
    }
    .btn-danger-glow:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(255, 0, 85, 0.6); }

    .btn-warning-glow { 
        background: linear-gradient(135deg, #ffa502, #ff7f50); 
        color: white; border: none; font-weight: 600; border-radius: 10px; transition: all 0.3s ease; 
        box-shadow: 0 4px 15px rgba(255, 165, 2, 0.3);
    }
    .btn-warning-glow:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(255, 165, 2, 0.6); }

    .custom-input, .custom-select select { 
        background: rgba(5, 3, 10, 0.6) !important; 
        border: 1px solid rgba(255, 255, 255, 0.08) !important; 
        color: #fff !important; 
        border-radius: 10px !important; 
        transition: all 0.3s ease;
    }
    .custom-input:focus, .custom-select select:focus { 
        border-color: var(--primary-glow) !important; 
        box-shadow: 0 0 15px rgba(88, 101, 242, 0.3) !important; 
    }

    .tab-content { display: none; }
    .tab-content.is-active { 
        display: block; 
        animation: cyberSlideIn 0.5s cubic-bezier(0.19, 1, 0.22, 1) forwards; 
    }

    @keyframes cyberSlideIn { 
        from { opacity: 0; transform: translateY(25px) scale(0.97); filter: blur(6px); } 
        to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); } 
    }

    .live-pulse-dot {
        width: 10px; height: 10px; background: #00ffa3; border-radius: 50%; display: inline-block;
        box-shadow: 0 0 10px #00ffa3, 0 0 20px #00ffa3;
        animation: pulseDot 1.8s infinite;
        margin-right: 8px;
    }
    @keyframes pulseDot {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 163, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 255, 163, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 163, 0); }
    }

    .chat-container { display: flex; height: 650px; gap: 25px; }
    .chat-channels-list { width: 260px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
    
    .chat-channel-item { 
        padding: 14px; border-radius: 12px; cursor: pointer; 
        background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.04);
        transition: all 0.3s ease;
    }
    .chat-channel-item:hover, .chat-channel-item.active { 
        background: linear-gradient(135deg, rgba(88,101,242,0.25), rgba(0,242,254,0.05));
        border-color: var(--primary-glow); color: #fff; 
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }

    .chat-window { flex: 1; display: flex; flex-direction: column; height: 100%; }
    .chat-messages { 
        flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; 
        background: rgba(0,0,0,0.3); border-radius: 16px; border: 1px solid rgba(255,255,255,0.04);
        scroll-behavior: smooth;
    }
    
    .chat-msg-row { 
        display: flex; flex-direction: column; max-width: 70%; padding: 10px 15px; 
        border-radius: 14px; animation: msgFadeIn 0.3s ease-out forwards;
    }
    @keyframes msgFadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    
    .chat-msg-row.bot { background: rgba(88, 101, 242, 0.18); border: 1px solid rgba(88, 101, 242, 0.3); align-self: flex-end; border-bottom-right-radius: 2px; }
    .chat-msg-row.user { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); align-self: flex-start; border-bottom-left-radius: 2px; }
    .chat-msg-author { font-size: 0.8rem; font-weight: 600; color: #a0aec0; margin-bottom: 4px; }
    .chat-msg-time { font-size: 0.65rem; color: #5a6578; align-self: flex-end; margin-top: 6px; }

    .user-split { display: flex; gap: 25px; height: 700px; }
    .user-list-side { width: 320px; display: flex; flex-direction: column; gap: 12px; }
    .user-scroll-area { flex: 1; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 12px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.04); }
    
    .user-list-item { 
        display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 10px; 
        cursor: pointer; margin-bottom: 8px; background: rgba(255,255,255,0.01); 
        border: 1px solid transparent; transition: all 0.25s ease; 
    }
    .user-list-item:hover, .user-list-item.active { 
        background: rgba(88, 101, 242, 0.15); border-color: rgba(88, 101, 242, 0.3); 
        color: #fff; transform: translateX(4px);
    }
    .user-list-item img { width: 36px; height: 36px; border-radius: 50%; box-shadow: 0 0 10px rgba(0,0,0,0.5); }
    .user-profile-side { flex: 1; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); padding: 30px; border-radius: 20px; overflow-y: auto; }
    
    .role-tag { 
        display: inline-block; background: rgba(88,101,242,0.12); border: 1px solid rgba(88,101,242,0.4); 
        color: #babcff; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; margin: 4px; 
        transition: all 0.2s ease;
    }
    .role-tag:hover { background: rgba(88,101,242,0.3); transform: scale(1.05); }

    .ticket-badge, .archive-item { 
        background: rgba(255, 255, 255, 0.01); border: 1px solid rgba(255, 255, 255, 0.04); 
        padding: 16px 24px; border-radius: 14px; margin-bottom: 14px; 
        display: flex; justify-content: space-between; align-items: center;
        transition: all 0.3s ease;
    }
    .chat-input-area { display: flex; gap: 10px; margin-top: 15px; }
    .chat-input-area input { flex: 1; }
</style>
"""

# ===============================
# 📄 MATRYCA TEMPLATÓW HTML WWW
# ===============================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Panel VIP</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {{ SHARED_STYLE | safe }}
</head>
<body>
    <div class="animated-bg"></div>
    <canvas id="space-canvas"></canvas>

    <div class="dashboard-container">
        <aside class="sidebar">
            <div>
                <div class="has-text-centered mb-6">
                    <h1 class="title is-4 glow-text mb-2" style="letter-spacing: 2px;">🎮 KUBUSIOWO</h1>
                    <div class="is-flex is-align-items-center is-justify-content-center">
                        <span class="live-pulse-dot"></span>
                        <p class="is-size-7 has-text-grey-light font-weight-bold">LIVE CONSOLE ACTIVE</p>
                    </div>
                </div>
                <ul class="menu-list">
                    <li><a href="#" class="is-active" onmouseenter="playHoverSound()" onclick="switchTab(event, 'status-tab')">⚙️ Status bota</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'management-tab')">🛠️ Stwórz Kanał</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'users-tab')">👥 Baza Użytkowników</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'tickets-tab')">🎫 Aktywne Tickety</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'chat-tab')">💬 Czat Ticketów</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'archive-tab')">📜 Archiwum Ticketów</a></li>
                </ul>
            </div>
            <div><a href="/logout" class="button btn-danger-glow is-fullwidth py-4" onmouseenter="playHoverSound()" onclick="playClickSound()">Wyloguj system</a></div>
        </aside>

        <main class="main-content">
            <div id="status-tab" class="tab-content is-active">
                <div class="box glass-box p-6" style="max-width: 600px;">
                    <h2 class="title is-3 has-text-white mb-4">Ustawienia Aktywności Bota</h2>
                    <form method="POST" action="/update-status" onclick="playClickSound()">
                        <div class="field mb-5">
                            <label class="label has-text-grey-light is-size-7 mb-2">Treść statusu gry (Playing...)</label>
                            <input class="input custom-input py-4" type="text" name="status_text" value="{{ current_status }}">
                        </div>
                        <button type="submit" class="button btn-glow px-6 py-4">Zaktualizuj status</button>
                    </form>
                </div>
            </div>

            <div id="management-tab" class="tab-content">
                <div class="box glass-box p-5" style="max-width: 500px;">
                    <h3 class="title is-4 has-text-white mb-4">📁 Kreator Kanałów Serwerowych</h3>
                    <form method="POST" action="/create-channel" onclick="playClickSound()">
                        <div class="field mb-3"><input class="input custom-input" type="text" name="channel_name" required placeholder="Nazwa nowego kanału..."></div>
                        <div class="field mb-5"><div class="select is-fullwidth custom-select"><select name="channel_type"><option value="text">Tekstowy</option><option value="voice">Głosowy</option></select></div></div>
                        <button type="submit" class="button btn-glow is-fullwidth py-4">Wygeneruj kanał</button>
                    </form>
                </div>
            </div>

            <div id="users-tab" class="tab-content">
                <div class="box glass-box p-5">
                    <h2 class="title is-4 has-text-white mb-4">👥 Menedżer Użytkowników</h2>
                    <div class="user-split">
                        <div class="user-list-side">
                            <input type="text" id="user-search-input" class="input custom-input mb-3" placeholder="🔍 Wpisz nick, aby szukać..." oninput="filterUsers()">
                            <div id="user-scroll-container" class="user-scroll-area"><p class="has-text-grey is-size-7 p-3">Inicjalizacja rekordów...</p></div>
                        </div>
                        <div id="user-profile" class="user-profile-side">
                            <p class="has-text-grey has-text-centered" style="margin-top: 200px;">Wybierz osobę z bazy danych, aby otworzyć profil cyber-karty.</p>
                        </div>
                    </div>
                </div>
            </div>

            <div id="tickets-tab" class="tab-content">
                <div class="box glass-box p-6">
                    <h2 class="title is-3 has-text-white mb-4">🎫 Aktywne Kanały Ticketów</h2>
                    <div id="tickets-list"><p class="has-text-grey">Wyszukiwanie otwartych zgłoszeń...</p></div>
                </div>
            </div>

            <div id="chat-tab" class="tab-content">
                <div class="box glass-box p-5">
                    <h2 class="title is-4 has-text-white mb-4">💬 Live Chat Matrix (Pisz jako BOT)</h2>
                    <div class="chat-container">
                        <div id="chat-channels" class="chat-channels-list"><p class="has-text-grey is-size-7">Ładowanie kanałów...</p></div>
                        <div class="chat-window">
                            <div id="chat-messages" class="chat-messages">
                                <p class="has-text-grey" style="margin:auto;">Wybierz aktywny strumień kanału z listy obok.</p>
                            </div>
                            <div class="chat-input-area">
                                <input type="text" id="chat-input-msg" class="input custom-input" placeholder="Napisz coś jako bot na kanale..." disabled onkeydown="if(event.key==='Enter') sendWebMessage()">
                                <button id="chat-send-btn" class="button btn-glow" disabled onclick="sendWebMessage()">Wyślij</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div id="archive-tab" class="tab-content">
                <div class="box glass-box p-5">
                    <h2 class="title is-4 has-text-white mb-4">📜 Lokalne Archiwum Transkrypcji Ticketów</h2>
                    <div id="archive-list"><p class="has-text-grey">Parsowanie historii transkrypcji...</p></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        const hoverAudio = new Audio('https://assets.mixkit.co/active_storage/sfx/2568/2568-84.wav');
        const clickAudio = new Audio('https://assets.mixkit.co/active_storage/sfx/2753/2753-84.wav');
        hoverAudio.volume = 0.15; clickAudio.volume = 0.25;

        function playHoverSound() { hoverAudio.currentTime = 0; hoverAudio.play().catch(() => {}); }
        function playClickSound() { clickAudio.currentTime = 0; clickAudio.play().catch(() => {}); }

        const canvas = document.getElementById('space-canvas');
        const ctx = canvas.getContext('2d');
        let stars = []; let meteors = [];

        function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
        window.addEventListener('resize', resizeCanvas); resizeCanvas();

        for (let i = 0; i < 120; i++) {
            stars.push({
                x: Math.random() * canvas.width, y: Math.random() * canvas.height,
                size: Math.random() * 1.8, alpha: Math.random(), speed: 0.2 + Math.random() * 0.4
            });
        }

        function spawnMeteor() {
            if (meteors.length < 3 && Math.random() < 0.015) {
                meteors.push({
                    x: Math.random() * canvas.width * 0.8, y: -20,
                    length: 40 + Math.random() * 80, speedX: 4 + Math.random() * 6, speedY: 4 + Math.random() * 6, alpha: 1
                });
            }
        }

        function drawSpace() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            stars.forEach(star => {
                ctx.fillStyle = `rgba(255, 255, 255, ${star.alpha})`;
                ctx.beginPath(); ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2); ctx.fill();
                star.y += star.speed;
                if (star.y > canvas.height) { star.y = 0; star.x = Math.random() * canvas.width; }
            });
            spawnMeteor();
            meteors.forEach((m, idx) => {
                let gradient = ctx.createLinearGradient(m.x, m.y, m.x + m.length, m.y + m.length);
                gradient.addColorStop(0, `rgba(0, 242, 254, ${m.alpha})`);
                gradient.addColorStop(0.5, `rgba(88, 101, 242, ${m.alpha * 0.5})`);
                gradient.addColorStop(1, 'rgba(0,0,0,0)');
                ctx.strokeStyle = gradient; ctx.lineWidth = 2;
                ctx.beginPath(); ctx.moveTo(m.x, m.y); ctx.lineTo(m.x - m.length, m.y - m.length); ctx.stroke();
                m.x += m.speedX; m.y += m.speedY; m.alpha -= 0.012;
                if (m.alpha <= 0 || m.x > canvas.width || m.y > canvas.height) { meteors.splice(idx, 1); }
            });
            requestAnimationFrame(drawSpace);
        }
        drawSpace();

        let currentActiveChannelId = null; let selectedUserId = null; let allUsersData = [];

        function switchTab(evt, tabId) {
            playClickSound();
            document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("is-active"));
            document.querySelectorAll(".menu-list a").forEach(el => el.classList.remove("is-active"));
            document.getElementById(tabId).classList.add("is-active");
            evt.currentTarget.classList.add("is-active");
            if (tabId === 'tickets-tab') fetchTickets();
            if (tabId === 'chat-tab') fetchChatChannels();
            if (tabId === 'users-tab') fetchUsers();
            if (tabId === 'archive-tab') fetchArchive();
        }

        function fetchTickets() {
            const listDiv = document.getElementById('tickets-list');
            fetch('/api/tickets').then(res => res.json()).then(data => {
                listDiv.innerHTML = '';
                if (data.length === 0) { listDiv.innerHTML = '<p class="has-text-grey-light">Brak otwartych procesów zgłoszeniowych.</p>'; return; }
                data.forEach(t => {
                    const div = document.createElement('div'); div.className = 'ticket-badge';
                    div.innerHTML = `<div><strong style="color:#fff; font-size:1.1rem;">#${t.name}</strong></div>
                    <form method="POST" action="/close-ticket-dash" style="margin:0;"><input type="hidden" name="channel_id" value="${t.id}"><button type="submit" class="button is-small btn-danger-glow px-5" onclick="playClickSound()">Wymuś Zamknięcie</button></form>`;
                    listDiv.appendChild(div);
                });
            });
        }

        function fetchChatChannels() {
            const channelsDiv = document.getElementById('chat-channels');
            fetch('/api/tickets').then(res => res.json()).then(data => {
                channelsDiv.innerHTML = '';
                if(data.length === 0){ channelsDiv.innerHTML = '<p class="has-text-grey is-size-7">Brak otwartych kanałów.</p>'; return; }
                data.forEach(t => {
                    const div = document.createElement('div');
                    div.className = `chat-channel-item ${currentActiveChannelId === t.id ? 'active' : ''}`;
                    div.innerText = `#${t.name}`; div.onmouseenter = playHoverSound;
                    div.onclick = () => { playClickSound(); selectChatChannel(t.id); };
                    channelsDiv.appendChild(div);
                });
            });
        }

        function selectChatChannel(channelId) {
            currentActiveChannelId = channelId;
            document.getElementById('chat-input-msg').disabled = false;
            document.getElementById('chat-send-btn').disabled = false;
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML = '<p class="has-text-grey">Pobieranie strumienia historii...</p>';
            fetch(`/api/chat/history/${channelId}`).then(res => res.json()).then(messages => {
                messagesDiv.innerHTML = ''; messages.forEach(msg => appendMessageDOM(msg));
            });
        }

        function appendMessageDOM(msg) {
            const messagesDiv = document.getElementById('chat-messages');
            const row = document.createElement('div');
            row.className = `chat-msg-row ${msg.is_bot ? 'bot' : 'user'}`;
            row.innerHTML = `<div class="chat-msg-author">${msg.author}</div><div>${msg.content}</div><div class="chat-msg-time">${msg.time}</div>`;
            messagesDiv.appendChild(row); messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function sendWebMessage() {
            playClickSound();
            const input = document.getElementById('chat-input-msg'); const content = input.value.trim();
            if(!content || !currentActiveChannelId) return;
            fetch('/api/chat/send', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ channel_id: currentActiveChannelId, message: content })
            }).then(() => { input.value = ''; selectChatChannel(currentActiveChannelId); });
        }

        function fetchUsers() { fetch('/api/users').then(res => res.json()).then(data => { allUsersData = data; renderUsersList(allUsersData); }); }

        function renderUsersList(users) {
            const container = document.getElementById('user-scroll-container'); container.innerHTML = '';
            if(users.length === 0) { container.innerHTML = '<p class="has-text-grey is-size-7 p-2">Nie odnaleziono kryteriów.</p>'; return; }
            users.forEach(u => {
                const div = document.createElement('div');
                div.className = `user-list-item ${selectedUserId === u.id ? 'active' : ''}`;
                div.innerHTML = `<img src="${u.avatar}" alt="avatar"> <span>${u.name}</span>`;
                div.onmouseenter = playHoverSound; div.onclick = () => { playClickSound(); selectUser(u.id); };
                container.appendChild(div);
            });
        }

        function filterUsers() {
            const query = document.getElementById('user-search-input').value.toLowerCase().trim();
            const filtered = allUsersData.filter(u => u.name.toLowerCase().includes(query));
            renderUsersList(filtered);
        }

        function selectUser(userId) {
            selectedUserId = userId; const profileDiv = document.getElementById('user-profile');
            profileDiv.innerHTML = '<p class="has-text-grey">Wczytywanie architektury profilu...</p>';
            fetch(`/api/users/${userId}`).then(res => res.json()).then(u => {
                if(u.error) { profileDiv.innerHTML = `<p class='has-text-danger'>${u.error}</p>`; return; }
                let rolesHtml = u.roles.map(r => `<span class="role-tag">${r}</span>`).join('');
                let dropdownOptions = u.server_all_roles.map(rName => `<option value="${rName}">${rName}</option>`).join('');
                profileDiv.innerHTML = `
                    <div class="columns is-mobile is-vcentered mb-4">
                        <div class="column is-narrow"><img src="${u.avatar}" style="width:80px; height:80px; border-radius:50%; border:2px solid var(--primary-glow); box-shadow: 0 0 15px var(--primary-glow);"></div>
                        <div class="column"><h3 class="title is-4 has-text-white mb-1 glow-text">${u.name}</h3><p class="is-size-7 has-text-grey-light">ID: ${u.id}</p></div>
                    </div>
                    <div class="is-size-7 mb-4 p-3" style="background:rgba(0,0,0,0.15); border-radius:10px;">
                        <p>📅 Rejestracja: <span class="has-text-white">${u.created_at}</span></p>
                    </div>
                    <p class="label has-text-grey-light mb-2 is-size-7">AKTYWNE RANGI:</p>
                    <div class="mb-4">${rolesHtml || '<span class="has-text-grey-light is-size-7">Brak uprawnień</span>'}</div>
                    <div class="box mb-4 p-4" style="background:rgba(0,0,0,0.2); border:1px solid rgba(255,255,255,0.05); border-radius:12px;">
                        <div class="field has-addons">
                            <div class="control is-expanded"><div class="select is-small is-fullwidth custom-select"><select id="role-dropdown">${dropdownOptions}</select></div></div>
                            <div class="control"><button class="button is-small btn-glow px-4" onclick="modifyUserRole('add')">Nadaj</button></div>
                        </div>
                    </div>`;
            });
        }

        function fetchArchive() {
            const archiveDiv = document.getElementById('archive-list');
            fetch('/api/archive').then(res => res.json()).then(data => {
                archiveDiv.innerHTML = ''; if(data.length === 0) { archiveDiv.innerHTML = '<p class="has-text-grey">Archiwum systemowe jest puste.</p>'; return; }
                data.forEach((item, index) => {
                    const div = document.createElement('div'); div.className = 'archive-item';
                    div.innerHTML = `<div><span class="has-text-grey-light">[${item.closed_at}]</span> <strong>Ticket: ${item.channel_name}</strong></div>`;
                    archiveDiv.appendChild(div);
                });
            });
        }
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Zaloguj do centrali</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {{ SHARED_STYLE | safe }}
</head>
<body>
    <div class="is-flex is-justify-content-center is-align-items-center" style="height: 100vh;">
        <div class="box glass-box p-6 animate__animated animate__fadeIn" style="width: 400px;">
            <h2 class="title is-4 has-text-white glow-text has-text-centered mb-5">🛡️ SECURE LOGIN</h2>
            {% if error %}<p class="has-text-danger is-size-7 mb-3 has-text-centered">{{ error }}</p>{% endif %}
            <form method="POST">
                <div class="field mb-4"><input class="input custom-input py-4" type="password" name="password" placeholder="Wprowadź kod dostępu..." required></div>
                <button type="submit" class="button btn-glow is-fullwidth py-4">Inicjalizuj sesję</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

# ===============================
# 🌐 ENDPOINTY API DLA BACKENDU FLASK
# ===============================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == DASHBOARD_PASSWORD:
            session['logged_in'] = True
            return redirect('/dashboard')
        return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE, error="Nieautoryzowana próba logowania. Klucz odrzucony.")
    return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE, error=None)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect('/')
    return render_template_string(HTML_TEMPLATE, SHARED_STYLE=SHARED_STYLE, current_status=current_status_text)

@app.route('/update-status', methods=['POST'])
def update_status():
    if not session.get('logged_in'): return redirect('/')
    text = request.form.get('status_text', 'Zarządzanie serwerem')
    asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord.Game(name=text)), bot.loop)
    global current_status_text
    current_status_text = text
    return redirect('/dashboard')

@app.route('/api/tickets')
def api_tickets():
    if not session.get('logged_in'): return jsonify([])
    # Pobieranie kanałów z pierwszej dostępnej bazy gildii bota
    if not bot.guilds: return jsonify([])
    guild = bot.guilds[0]
    tickets = [{"id": str(ch.id), "name": ch.name} for ch in guild.text_channels if "ticket" in ch.name.lower()]
    return jsonify(tickets)

@app.route('/api/users')
def api_users():
    if not session.get('logged_in'): return jsonify([])
    if not bot.guilds: return jsonify([])
    guild = bot.guilds[0]
    users = [{"id": str(m.id), "name": m.name, "avatar": m.display_avatar.url} for m in guild.members if not m.bot]
    return jsonify(users)

@app.route('/api/archive')
def api_archive():
    if not session.get('logged_in'): return jsonify([])
    return jsonify(load_archive())

# Async Flask Bootstrapper
async def run_flask():
    from workbook import serve # Przykładowy minimalistyczny serwer ASGI lub tradycyjny Werkzeug w trybie non-blocking
    # Dla kompatybilności środowiskowej stawiamy tradycyjnego dev-servera
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()

# ===============================
# 🚀 ODPAŁ SYSTEMU (Main Execution)
# ===============================

if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Krytyczny błąd: Brak zmiennej środowiskowej 'DISCORD_TOKEN'.")
