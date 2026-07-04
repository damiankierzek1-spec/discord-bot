import discord
from discord.ext import commands
from discord import Intents, utils, Embed, File
from discord.ui import Button, View, Modal, TextInput
import os
from flask import Flask, render_template_string, request, redirect, session, jsonify
from threading import Thread
import asyncio
import io
from datetime import datetime
from typing import List

# ===============================
# 🚨 KONFIGURACJA GLOBALNA I ZMIENNE ŚRODOWISKOWE 🚨
# ===============================

ADMIN_IDS: List[int] = [652507356105539585, 550959315700154368, 590215623259193371]
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PWD", "Kuba123!")

# 🔥 WPISANE ID KANAŁU LOGÓW TICKETÓW (logi-ticketow):
LOGS_CHANNEL_ID = 1522639999869259916  

app = Flask('')
app.secret_key = os.environ.get("FLASK_SECRET", "super-tajny-klucz-kubusiowo")

bot_instance = None

# Słownik do przechowywania danych o ticketach w pamięci podręcznej
ticket_data_cache = {}

# ===============================
# 🎨 STYLE CSS DLA STRONY WWW
# ===============================

SHARED_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #0a0813 0%, #110d22 50%, #050307 100%); color: #e2e8f0; min-height: 100vh; margin: 0; }
    .dashboard-container { display: flex; min-height: 100vh; }
    .sidebar { width: 260px; background: rgba(15, 12, 30, 0.6); border-right: 1px solid rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); padding: 2rem 1.5rem; display: flex; flex-direction: column; justify-content: space-between; }
    .main-content { flex: 1; padding: 2.5rem; overflow-y: auto; }
    .menu-list a { color: #a0aec0; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 10px; transition: all 0.3s ease; font-weight: 500; }
    .menu-list a:hover, .menu-list a.is-active { background: rgba(88, 101, 242, 0.15); color: #fff; text-shadow: 0 0 10px rgba(88, 101, 242, 0.5); border-left: 4px solid #5865f2; padding-left: 12px; }
    .glass-box { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; backdrop-filter: blur(12px); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); transition: all 0.3s ease; }
    .glass-box:hover { transform: translateY(-3px); box-shadow: 0 12px 40px 0 rgba(88, 101, 242, 0.15); border-color: rgba(88, 101, 242, 0.25); }
    .glow-text { color: #fff; text-shadow: 0 0 12px rgba(88, 101, 242, 0.6); }
    .btn-glow { background: linear-gradient(45deg, #7289da, #5865f2); color: white; border: none; font-weight: 600; border-radius: 8px; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(88, 101, 242, 0.3); }
    .btn-glow:hover { background: linear-gradient(45deg, #5865f2, #4752c4); transform: scale(1.02); box-shadow: 0 6px 20px rgba(88, 101, 242, 0.5); color: white; }
    .btn-danger-glow { background: linear-gradient(45deg, #ff4757, #ee5253); color: white; border: none; font-weight: 600; border-radius: 8px; transition: all 0.3s ease; }
    .btn-danger-glow:hover { transform: scale(1.02); box-shadow: 0 6px 20px rgba(238, 82, 83, 0.4); }
    .custom-input, .custom-select select { background: rgba(0, 0, 0, 0.3) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; color: #fff !important; border-radius: 8px !important; }
    .tab-content { display: none; animation: fadeIn 0.4s ease forwards; }
    .tab-content.is-active { display: block; }
    .notification { background: rgba(46, 213, 115, 0.12) !important; border: 1px solid rgba(46, 213, 115, 0.4) !important; color: #2ed573 !important; border-radius: 8px; }
    .ticket-badge { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); padding: 12px 20px; border-radius: 10px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
"""

# ===============================
# 📄 SZABLONY HTML WWW
# ===============================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Panel</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {{ SHARED_STYLE | safe }}
</head>
<body>
    <div class="dashboard-container">
        <aside class="sidebar">
            <div>
                <div class="has-text-centered mb-6">
                    <h1 class="title is-4 glow-text mb-1">🎮 KUBUSIOWO</h1>
                    <p class="is-size-7 has-text-grey">tung tung tung sahur</p>
                </div>
                <ul class="menu-list">
                    <li><a href="#" class="is-active" onclick="switchTab(event, 'status-tab')">⚙️ Status bota</a></li>
                    <li><a href="#" onclick="switchTab(event, 'management-tab')">🛠️ Zarządzanie</a></li>
                    <li><a href="#" onclick="switchTab(event, 'tickets-tab')">🎫 Aktywne Tickety</a></li>
                </ul>
            </div>
            <div><a href="/logout" class="button btn-danger-glow is-fullwidth">Wyloguj się</a></div>
        </aside>

        <main class="main-content">
            {% if message %}<div class="notification p-3 mb-5">{{ message }}</div>{% endif %}

            <div id="status-tab" class="tab-content is-active">
                <div class="box glass-box p-6 mb-5">
                    <h2 class="title is-3 has-text-white mb-2">Ustawienia Aktywności</h2>
                    <form method="POST" action="/update-status">
                        <div class="field mb-4">
                            <input class="input custom-input" type="text" name="status_text" value="{{ current_status }}">
                        </div>
                        <button type="submit" class="button btn-glow px-5">Zaktualizuj status</button>
                    </form>
                </div>
            </div>

            <div id="management-tab" class="tab-content">
                <div class="columns">
                    <div class="column is-6">
                        <div class="box glass-box p-5">
                            <h3 class="title is-4 has-text-white mb-3">📁 Stwórz Kanał</h3>
                            <form method="POST" action="/create-channel">
                                <div class="field mb-3"><input class="input custom-input" type="text" name="channel_name" required placeholder="nazwa"></div>
                                <div class="field mb-4"><div class="select is-fullwidth custom-select"><select name="channel_type"><option value="text">Tekstowy</option><option value="voice">Głosowy</option></select></div></div>
                                <button type="submit" class="button btn-glow is-fullwidth">Stwórz</button>
                            </form>
                        </div>
                    </div>
                    <div class="column is-6">
                        <div class="box glass-box p-5">
                            <h3 class="title is-4 has-text-white mb-3">👤 Nadaj Rolę</h3>
                            <form method="POST" action="/assign-role">
                                <div class="field mb-3"><input class="input custom-input" type="text" name="user_id" required placeholder="User ID"></div>
                                <div class="field mb-4"><input class="input custom-input" type="text" name="role_name" required placeholder="Nazwa roli"></div>
                                <button type="submit" class="button btn-glow is-fullwidth">Nadaj Rolę</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <div id="tickets-tab" class="tab-content">
                <div class="box glass-box p-6">
                    <h2 class="title is-3 has-text-white mb-2">🎫 Monitor Otwartych Zgłoszeń</h2>
                    <div id="tickets-list"><p class="has-text-grey">Ładowanie...</p></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        function switchTab(evt, tabId) {
            document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("is-active"));
            document.querySelectorAll(".menu-list a").forEach(el => el.classList.remove("is-active"));
            document.getElementById(tabId).classList.add("is-active");
            evt.currentTarget.classList.add("is-active");
            if (tabId === 'tickets-tab') fetchTickets();
        }

        function fetchTickets() {
            const listDiv = document.getElementById('tickets-list');
            fetch('/api/tickets')
                .then(res => res.json())
                .then(data => {
                    listDiv.innerHTML = '';
                    if (data.length === 0) { listDiv.innerHTML = '<p class="has-text-grey-light">Brak ticketów.</p>'; return; }
                    data.forEach(t => {
                        const div = document.createElement('div');
                        div.className = 'ticket-badge';
                        div.innerHTML = `<div><strong style="color:#fff;">#${t.name}</strong></div>
                        <form method="POST" action="/close-ticket-dash" style="margin:0;"><input type="hidden" name="channel_id" value="${t.id}"><button type="submit" class="button is-small btn-danger-glow px-4">Usuń</button></form>`;
                        listDiv.appendChild(div);
                    });
                });
        }
        setInterval(() => { if (document.getElementById('tickets-tab').classList.contains('is-active')) fetchTickets(); }, 8000);
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Zaloguj</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">{{ SHARED_STYLE | safe }}</head>
<body style="display: flex; align-items: center; min-height: 100vh;"><div class="container"><div class="box glass-box p-6" style="max-width: 420px; margin: 0 auto;"><h1 class="title is-3 glow-text has-text-centered mb-5">🔒 Panel Logowania</h1><form method="POST" action="/login"><div class="field mb-5"><input class="input custom-input" type="password" name="password" required placeholder="Hasło"></div><button type="submit" class="button btn-glow is-fullwidth py-4">Zaloguj</button></form></div></div></body>
</html>
"""

# ===============================
# 🌐 TRASY FLASK (ZAPLECZE WWW)
# ===============================

@app.route('/')
def home():
    if not session.get('logged_in'): return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE)
    current_status = bot_instance.activity.name if bot_instance and bot_instance.activity else ""
    return render_template_string(HTML_TEMPLATE, SHARED_STYLE=SHARED_STYLE, current_status=current_status, message=request.args.get('msg'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == DASHBOARD_PASSWORD:
        session['logged_in'] = True
        return redirect('/')
    return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE, error="Złe hasło!")

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

@app.route('/update-status', methods=['POST'])
def update_status():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    asyncio.run_coroutine_threadsafe(bot_instance.change_presence(activity=discord.Game(name=request.form.get('status_text', ''))), bot_instance.loop)
    return redirect('/?msg=Zmieniono+status!')

@app.route('/api/tickets')
def api_tickets():
    if not session.get('logged_in') or not bot_instance: return jsonify([])
    return jsonify([{"id": str(c.id), "name": c.name} for g in bot_instance.guilds for c in g.text_channels if c.name.startswith("ticket-")])

@app.route('/close-ticket-dash', methods=['POST'])
def close_ticket_dash():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    ch_id = request.form.get('channel_id')
    if ch_id and ch_id.isdigit():
        asyncio.run_coroutine_threadsafe(trigger_ticket_close_flow(int(ch_id)), bot_instance.loop)
        return redirect('/?msg=Rozpoczeto+zamykanie+ticketu+z+ankieta!')
    return redirect('/')

@app.route('/create-channel', methods=['POST'])
def create_channel():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    asyncio.run_coroutine_threadsafe(create_channel_async(request.form.get('channel_name', ''), request.form.get('channel_type', 'text')), bot_instance.loop)
    return redirect('/?msg=Kanal+utworzony!')

@app.route('/assign-role', methods=['POST'])
def assign_role():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    asyncio.run_coroutine_threadsafe(assign_role_async(int(request.form.get('user_id')), request.form.get('role_name')), bot_instance.loop)
    return redirect('/?msg=Rola+nadana!')

# ===============================
# ⛓️ ASYNCHRONICZNE POMOCNIKI BOTA
# ===============================

async def trigger_ticket_close_flow(channel_id: int):
    channel = bot_instance.get_channel(channel_id) or await bot_instance.fetch_channel(channel_id)
    if channel:
        await channel.send("⚠️ Oceń pomoc.")
        await initiate_survey(channel)

async def create_channel_async(name: str, channel_type: str):
    for guild in bot_instance.guilds:
        if channel_type == "text": await guild.create_text_channel(name=name)
        elif channel_type == "voice": await guild.create_voice_channel(name=name)
        break

async def assign_role_async(user_id: int, role_name: str):
    for guild in bot_instance.guilds:
        member = guild.get_member(user_id) or await guild.fetch_member(user_id)
        role = utils.get(guild.roles, name=role_name)
        if member and role: await member.add_roles(role)

def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))))
    t.daemon = True
    t.start()

# ===============================
# 📊 NIEZAWODNY SILNIK GENEROWANIA LOGÓW
# ===============================

async def generate_and_send_ticket_logs(channel_id: int, closing_user, rating: int, guild):
    """Generuje pełną transkrypcję kanału tekstowego i przesyła spakowane dane na kanał logów"""
    if not LOGS_CHANNEL_ID or not bot_instance:
        print("❌ [LOGI BŁĄD] Brak ustawionego ID kanału logów lub bot_instance.")
        return

    # Pobieranie obiektów kanałów z gwarancją kontekstu serwera
    logs_channel = guild.get_channel(LOGS_CHANNEL_ID) or bot_instance.get_channel(LOGS_CHANNEL_ID)
    target_channel = guild.get_channel(channel_id)
    
    if not logs_channel:
        print(f"❌ [LOGI BŁĄD] Nie odnaleziono kanału tekstowego logów o ID: {LOGS_CHANNEL_ID}")
        return
        
    if not target_channel:
        print(f"❌ [LOGI BŁĄD] Nie udało się odnaleźć obiektu zamykanego kanału ticketu.")
        return

    # Wyciąganie metadanych ticketu z pamięci podręcznej podręcznej bota
    data = ticket_data_cache.get(channel_id, {
        "subject": "Nie zdefiniowano (Starszy ticket)",
        "description": "Nie zdefiniowano (Starszy ticket)",
        "creator_mention": "@Użytkownik",
        "claimer_mention": "@Brak"
    })

    # Ściąganie pełnej historii rozmowy na kanale ticketowym
    transcript_content = []
    try:
        async for msg in target_channel.history(limit=600, oldest_first=True):
            timestamp = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            transcript_content.append(f"[{timestamp}] {msg.author.name}: {msg.content}")
    except Exception as e:
        print(f"⚠️ Problem przy pobieraniu historii wiadomości (Zostanie pominięta): {e}")
        transcript_content.append("[Błąd pobierania historii wiadomości]")

    full_transcript_text = "\n".join(transcript_content)
    
    # Konwersja tekstu na obiekt pliku binarnego w pamięci podręcznej RAM
    file_stream = io.BytesIO(full_transcript_text.encode('utf-8'))
    discord_file = File(file_stream, filename=f"log-{target_channel.name}.txt")

    # Nagłówek tekstowy przed embedem
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header_text = (
        f"```\n"
        f"--- TRANSKRYPCJA TICKETU: {target_channel.name} ---\n"
        f"Wygenerowano: {now_str}\n"
        f"Obsługujący (Claim): {data.get('claimer_mention')}\n"
        f"Zamknięty przez: {closing_user.name}\n"
        f"Ocena użytkownika: {'★' * rating} ({rating}/5)\n"
        f"```"
    )

    # Budowanie profesjonalnego i estetycznego embedu logów
    log_embed = Embed(color=0xff4757) 
    log_embed.title = "🔒 Archiwum Zgłoszenia"
    log_embed.description = f"Kanał **{target_channel.name}** został pomyślnie zamknięty."
    
    log_embed.add_field(name="🛠️ Obsługujący admin:", value=data.get('claimer_mention'), inline=True)
    log_embed.add_field(name="🔒 Zamknął zgłoszenie:", value=closing_user.mention, inline=True)
    log_embed.add_field(name="⭐ Ocena pracy:", value=f"{'⭐' * rating} ({rating}/5)", inline=True)
    
    log_embed.add_field(name="📌 Temat zgłoszenia:", value=f"```\n{data.get('subject')}\n```", inline=False)
    log_embed.add_field(name="📝 Treść opisu zgłoszenia:", value=f"```\n{data.get('description')}\n```", inline=False)
    log_embed.set_footer(text=f"Dzisiaj o {datetime.now().strftime('%H:%M')}")

    # Wysłanie paczki danych na wyznaczony kanał logów
    await logs_channel.send(content=header_text, file=discord_file, embed=log_embed)
    print(f"✅ [SUKCES LOGOWANIA] Logi dla kanału {target_channel.name} zostały pomyślnie wysłane!")
    
    # Wyczyszczenie pamięci cache bota
    if channel_id in ticket_data_cache:
        del ticket_data_cache[channel_id]

# ===============================
# 📊 INTERAKTYWNA ANKIETA SATYSFAKCJI (ZABEZPIECZONA)
# ===============================

class TicketSurveyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_rating(self, interaction: discord.Interaction, rating: int):
        # Odroczenie odpowiedzi, aby zapobiec wygaśnięciu tokenu interakcji Discorda
        await interaction.response.defer(ephemeral=False)
        
        channel_id = interaction.channel_id
        closing_user = interaction.user
        guild = interaction.guild

        print(f"🔄 [PROCES] Zamykanie dla kanału o ID: {channel_id}")

        # KROK 1: Generowanie i wysyłanie logów (Najbardziej kluczowy krok przed destrukcją kanału)
        try:
            if guild:
                target_channel = guild.get_channel(channel_id) or await guild.fetch_channel(channel_id)
                if target_channel:
                    await generate_and_send_ticket_logs(channel_id, closing_user, rating, guild)
                else:
                    print("❌ [BŁĄD KRYTYCZNY] Bot nie znalazł kanału w pamięci serwera przed logowaniem.")
            else:
                print("❌ [BŁĄD KRYTYCZNY] Brak obiektu Guild w strukturze interakcji.")
        except Exception as e:
            print(f"❌ [CRITICAL ERROR PRZY LOGOWANIU]: {e}")

        # KROK 2: Blokowanie przycisków na kanale, by nikt więcej ich nie kliknął
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(content=f"⭐ Dziękujemy za ocenę: **{rating}/5**! Kanał zostanie usunięty.", view=self)
        except Exception:
            pass
        
        # KROK 3: Odczekanie chwili, aby użytkownik zdążył przeczytać podziękowanie i usunięcie kanału
        await asyncio.sleep(4)
        try:
            if guild:
                target_channel = guild.get_channel(channel_id)
                if target_channel:
                    await target_channel.delete()
                    print(f"🗑️ Kanał ticketu {channel_id} został pomyślnie usunięty.")
        except Exception as e:
            print(f"❌ Nie udało się usunąć kanału tekstowego: {e}")

    @discord.ui.button(label="1 ⭐", style=discord.ButtonStyle.secondary, custom_id="rate_1")
    async def rate_1(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 1)

    @discord.ui.button(label="2 ⭐", style=discord.ButtonStyle.secondary, custom_id="rate_2")
    async def rate_2(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 2)

    @discord.ui.button(label="3 ⭐", style=discord.ButtonStyle.secondary, custom_id="rate_3")
    async def rate_3(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 3)

    @discord.ui.button(label="4 ⭐", style=discord.ButtonStyle.secondary, custom_id="rate_4")
    async def rate_4(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 4)

    @discord.ui.button(label="5 ⭐", style=discord.ButtonStyle.success, custom_id="rate_5")
    async def rate_5(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 5)

async def initiate_survey(channel):
    embed = Embed(
        title="📊 Ankieta",
        description="Zgłoszenie zostało pomyślnie zamknięte. Oceń pracę administracji za pomocą przycisków:",
        color=0xffb900
    )
    await channel.send(embed=embed, view=TicketSurveyView())

# ===============================
# 📝 OKIENKO MODALNE (FORMULARZ TICKETU)
# ===============================

class TicketCreateModal(Modal):
    def __init__(self):
        super().__init__(title="Formularz Zgłoszenia")

        self.subject = TextInput(
            label="Temat zgłoszenia",
            placeholder="np. Błąd / Problem z zakupem / Skarga...",
            required=True,
            max_length=100
        )
        self.description = TextInput(
            label="Opis problemu",
            style=discord.TextStyle.paragraph,
            placeholder="Opisz tutaj szczegóły sprawy...",
            required=True,
            max_length=1000
        )
        self.add_item(self.subject)
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        channel_name = f"ticket-{member.name.lower()}".replace(" ", "-")
        
        if utils.get(guild.text_channels, name=channel_name):
            await interaction.response.send_message("❌ Masz już otwarte jedno zgłoszenie!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        
        # Zapis do cache - przypisanie wprowadzonych w Modalu danych
        ticket_data_cache[ticket_channel.id] = {
            "subject": self.subject.value,
            "description": self.description.value,
            "creator_mention": member.mention,
            "claimer_mention": member.mention # Domyślna wartość
        }

        embed = Embed(title="🎫 Nowe Zgłoszenie Otwarte!", color=0x5865f2)
        embed.add_field(name="Użytkownik", value=member.mention, inline=True)
        embed.add_field(name="Temat główny", value=f"**{self.subject.value}**", inline=False)
        embed.add_field(name="Szczegółowy opis", value=self.description.value, inline=False)
        
        await ticket_channel.send(embed=embed, view=TicketActionView())
        await interaction.response.send_message(f"✅ Otwarto ticket: {ticket_channel.mention}", ephemeral=True)

class TicketActionView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Zamknij Zgłoszenie", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        # Nadpisywanie osoby obsługującej zgłoszenie adminem, który je zamyka
        if interaction.channel_id in ticket_data_cache:
            ticket_data_cache[interaction.channel_id]["claimer_mention"] = interaction.user.mention

        await interaction.response.send_message("Generuję ankietę końcową...", ephemeral=True)
        await initiate_survey(interaction.channel)

class TicketSetupView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Otwórz zgłoszenie", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(TicketCreateModal())

# ===============================
# 🤖 KOMENDY BOTA DISCORD
# ===============================

intents = Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def setup_hook():
    global bot_instance
    bot_instance = bot
    bot.add_view(TicketSetupView())
    bot.add_view(TicketActionView())
    bot.add_view(TicketSurveyView())

@bot.event
async def on_ready(): print(f'🤖 Bot online jako: {bot.user}')

@bot.command(name="pomoc")
async def pomoc(ctx):
    embed = Embed(
        title="📚 Menu Pomocy - Lista Wszystkich Komend",
        description="Poniżej znajdziesz spis poleceń bota wraz z ich opisami i uprawnieniami.",
        color=0x5865f2
    )
    embed.add_field(
        name="👥 Komendy Użytkownika",
        value="• `!pomoc` - Wyświetla to pełne okno pomocy z listą poleceń.",
        inline=False
    )
    embed.add_field(
        name="🛠️ Komendy Administratora",
        value="• `!ticket` - Generuje panel ticketow.\n"
              "• *(Wymagane uprawnienie: Administrator)*",
        inline=False
    )
    embed.add_field(
        name="💻 Dashboard",
        value="Dostępny pod adresem IP bota z hasłem konfiguracyjnym:\n"
              "• **Status**: Zmiana statusu bota.\n"
              "• **Kanały**: Tworzenie nowych kanałów na serwerze.\n"
              "• **Role**: Nadawanie ról użytkownikom przez ID.\n"
              "• **Tickety**: Nie wiem co tu napisać no ale sa tickety .",
        inline=False
    )
    embed.set_footer(text=f"Wywołane przez: {ctx.author.name}")
    await ctx.send(embed=embed)

@bot.command(name="ticket")
@commands.has_permissions(administrator=True)
async def send_ticket_panel(ctx):
    embed = Embed(
        title="🎫 Ticket",
        description="Masz pytanie lub chcesz coś zgłosić? Kliknij przycisk poniżej, uzupełnij krótki formularz tematu, a otworzy się Twój prywatny kanał.",
        color=0x2ed573
    )
    await ctx.send(embed=embed, view=TicketSetupView())
    await ctx.message.delete()

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN: bot.run(TOKEN)
