import os
import json
import asyncio
import threading
from typing import List

import discord
from discord import app_commands, Intents
from flask import Flask, render_template_string, request, redirect, session, jsonify

# ===============================
# KONFIGURACJA
# ===============================

ADMIN_IDS: List[int] = [652507356105539585, 550959315700154368, 590215623259193371]
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PWD", "Kuba123!")
ARCHIVE_FILE = "ticket_archive.json"

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "super-tajny-klucz-kubusiowo")

current_status_text = "Zarządzanie serwerem"

# ===============================
# PLIKI
# ===============================

def load_archive():
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_whole_archive(archive_data):
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive_data, f, ensure_ascii=False, indent=4)

# ===============================
# BOT
# ===============================

class ManagementBot(discord.Client):
    def __init__(self):
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(TicketPanelView())

bot = ManagementBot()

# ===============================
# TICKETY
# ===============================

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Otwórz ticket",
        style=discord.ButtonStyle.green,
        custom_id="kubusiowo:open_ticket_button"
    )
    async def open_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            await interaction.response.send_message("❌ To działa tylko na serwerze.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name="TICKETY")
        if category is None:
            category = await guild.create_category("TICKETY")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        channel_name = f"ticket-{user.name}".lower().replace(" ", "-")
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Ticket utworzony",
            description=f"Cześć {user.mention}, opisz swój problem tutaj.",
            color=discord.Color.blurple()
        )
        await ticket_channel.send(embed=embed)
        await interaction.followup.send(f"✅ Ticket utworzony: {ticket_channel.mention}", ephemeral=True)

ticket_group = app_commands.Group(name="ticket", description="Komendy związane z ticketami")

@ticket_group.command(name="panel", description="Wysyła panel ticketów")
@app_commands.describe(channel="Kanał, na który wysłać panel")
async def ticket_panel(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎫 Panel Ticketów",
        description="Kliknij przycisk poniżej, aby otworzyć ticket.",
        color=discord.Color.blurple()
    )
    await channel.send(embed=embed, view=TicketPanelView())
    await interaction.response.send_message(f"✅ Panel ticketów wysłany na {channel.mention}", ephemeral=True)

@ticket_group.command(name="close", description="Zamyka aktualny ticket")
async def ticket_close(interaction: discord.Interaction):
    if not interaction.channel or not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message("❌ To nie jest kanał tekstowy.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        archive = load_archive()
        archive.append({
            "channel_name": interaction.channel.name,
            "closed_by": str(interaction.user),
            "closed_at": discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_whole_archive(archive)

        await interaction.followup.send("🔒 Ticket zostanie zamknięty za chwilę.", ephemeral=True)
        await interaction.channel.delete()
    except Exception as e:
        await interaction.followup.send(f"❌ Błąd: {e}", ephemeral=True)

@ticket_group.command(name="archive", description="Dodaje ticket do archiwum bez usuwania kanału")
async def ticket_archive(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        archive = load_archive()
        archive.append({
            "channel_name": interaction.channel.name,
            "closed_by": str(interaction.user),
            "closed_at": discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_whole_archive(archive)
        await interaction.followup.send("📜 Ticket zapisany do archiwum.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Błąd: {e}", ephemeral=True)

bot.tree.add_command(ticket_group)

# ===============================
# SLASH KOMENDY
# ===============================

@bot.tree.command(name="sync", description="Synchronizuje komendy ukośnika z API Discorda (Tylko Admin)")
async def sync_commands(interaction: discord.Interaction):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Nie posiadasz uprawnień do synchronizacji.", ephemeral=True)
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
    await interaction.response.send_message(f"✅ Status bota został zmieniony na: `Playing {tekst}`", ephemeral=True)

@bot.tree.command(name="clear", description="Czyści określoną ilość wiadomości na kanale")
@app_commands.describe(ilosc="Ilość wiadomości do usunięcia")
async def clear_messages(interaction: discord.Interaction, ilosc: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Wymagane uprawnienia: Zarządzanie Wiadomościami.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        deleted = await interaction.channel.purge(limit=ilosc)
        await interaction.followup.send(f"🗑️ Usunięto {len(deleted)} wiadomości.")
    except Exception as e:
        await interaction.followup.send(f"❌ Błąd podczas czyszczenia: {e}", ephemeral=True)

@bot.tree.command(name="ping", description="Test odpowiedzi bota")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! `{round(bot.latency * 1000)}ms`", ephemeral=True)

@bot.event
async def on_ready():
    print(f"⚡ Zalogowano jako {bot.user} | Gotowy na komendy /")
    bot.add_view(TicketPanelView())
    await bot.change_presence(activity=discord.Game(name=current_status_text))
    try:
        synced = await bot.tree.sync()
        print(f"✅ Zsynchronizowano {len(synced)} komend")
    except Exception as e:
        print(f"❌ Błąd sync: {e}")

# ===============================
# STYLE HTML
# ===============================

SHARED_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    :root {
        --bg-gradient: radial-gradient(circle at 50% 50%, #080512 0%, #020105 100%);
        --primary-glow: #5865f2;
        --panel-bg: rgba(10, 7, 22, 0.55);
        --border-glow: rgba(88, 101, 242, 0.2);
    }
    body { font-family: 'Space Grotesk', sans-serif; background: var(--bg-gradient); color: #e2e8f0; min-height: 100vh; margin: 0; overflow-x: hidden; position: relative; }
    #space-canvas { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; pointer-events: none; }
    .animated-bg { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; background: radial-gradient(circle at 15% 25%, rgba(88, 101, 242, 0.15) 0%, transparent 45%), radial-gradient(circle at 85% 75%, rgba(0, 242, 254, 0.1) 0%, transparent 50%), radial-gradient(circle at 50% 50%, rgba(255, 0, 127, 0.05) 0%, transparent 40%); filter: blur(80px); animation: pulseBackground 20s ease-in-out infinite alternate; }
    @keyframes pulseBackground { 0% { transform: scale(1) translate(0, 0); } 100% { transform: scale(1.1) translate(10px, -10px); } }
    .dashboard-container { display: flex; min-height: 100vh; position: relative; z-index: 1; }
    .sidebar { width: 280px; background: rgba(8, 5, 18, 0.75); border-right: 1px solid var(--border-glow); backdrop-filter: blur(30px); padding: 2.5rem 1.5rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 8px 0 35px rgba(0,0,0,0.6); z-index: 2; }
    .main-content { flex: 1; padding: 3rem; overflow-y: auto; height: 100vh; position: relative; z-index: 1; }
    .menu-list a { color: #8a8da4; padding: 0.9rem 1.2rem; border-radius: 12px; margin-bottom: 0.6rem; display: flex; align-items: center; gap: 14px; transition: all 0.3s ease; font-weight: 500; border: 1px solid transparent; }
    .menu-list a.is-active { background: rgba(88, 101, 242, 0.25); color: #fff; }
    .glass-box { background: var(--panel-bg); border: 1px solid var(--border-glow); border-radius: 20px; backdrop-filter: blur(20px); box-shadow: 0 20px 45px rgba(0, 0, 0, 0.5); }
    .glow-text { color: #fff; text-shadow: 0 0 15px rgba(88, 101, 242, 0.8), 0 0 30px rgba(88, 101, 242, 0.3); }
    .btn-glow { background: linear-gradient(135deg, #6c7fff, #5865f2); color: white; border: none; font-weight: 600; border-radius: 10px; }
    .btn-danger-glow { background: linear-gradient(135deg, #ff4757, #ff0055); color: white; border: none; font-weight: 600; border-radius: 10px; }
    .custom-input, .custom-select select { background: rgba(5, 3, 10, 0.6) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; color: #fff !important; border-radius: 10px !important; }
    .tab-content { display: none; }
    .tab-content.is-active { display: block; }
    .live-pulse-dot { width: 10px; height: 10px; background: #00ffa3; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .chat-container { display: flex; height: 650px; gap: 25px; }
    .chat-channels-list { width: 260px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
    .chat-channel-item { padding: 14px; border-radius: 12px; cursor: pointer; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.04); }
    .chat-channel-item.active { background: rgba(88,101,242,0.25); border-color: var(--primary-glow); color: #fff; }
    .chat-window { flex: 1; display: flex; flex-direction: column; height: 100%; }
    .chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; background: rgba(0,0,0,0.3); border-radius: 16px; }
    .chat-msg-row { display: flex; flex-direction: column; max-width: 70%; padding: 10px 15px; border-radius: 14px; }
    .chat-msg-row.bot { background: rgba(88, 101, 242, 0.18); align-self: flex-end; }
    .chat-msg-row.user { background: rgba(255, 255, 255, 0.04); align-self: flex-start; }
    .chat-msg-author { font-size: 0.8rem; font-weight: 600; color: #a0aec0; margin-bottom: 4px; }
    .chat-msg-time { font-size: 0.65rem; color: #5a6578; align-self: flex-end; margin-top: 6px; }
    .user-split { display: flex; gap: 25px; height: 700px; }
    .user-list-side { width: 320px; display: flex; flex-direction: column; gap: 12px; }
    .user-scroll-area { flex: 1; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 12px; border-radius: 16px; }
    .user-list-item { display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 10px; cursor: pointer; margin-bottom: 8px; }
    .user-list-item.active { background: rgba(88, 101, 242, 0.15); }
    .user-list-item img { width: 36px; height: 36px; border-radius: 50%; }
    .user-profile-side { flex: 1; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); padding: 30px; border-radius: 20px; overflow-y: auto; }
    .role-tag { display: inline-block; background: rgba(88,101,242,0.12); border: 1px solid rgba(88,101,242,0.4); color: #babcff; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; margin: 4px; }
    .ticket-badge, .archive-item { background: rgba(255, 255, 255, 0.01); border: 1px solid rgba(255, 255, 255, 0.04); padding: 16px 24px; border-radius: 14px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; }
    .chat-input-area { display: flex; gap: 10px; margin-top: 15px; }
    .chat-input-area input { flex: 1; }
</style>
"""

# ===============================
# HTML
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
                    <li><a href="#" class="is-active" onclick="switchTab(event, 'status-tab')">⚙️ Status bota</a></li>
                    <li><a href="#" onclick="switchTab(event, 'management-tab')">🛠️ Stwórz Kanał</a></li>
                    <li><a href="#" onclick="switchTab(event, 'users-tab')">👥 Baza Użytkowników</a></li>
                    <li><a href="#" onclick="switchTab(event, 'tickets-tab')">🎫 Aktywne Tickety</a></li>
                    <li><a href="#" onclick="switchTab(event, 'chat-tab')">💬 Czat Ticketów</a></li>
                    <li><a href="#" onclick="switchTab(event, 'archive-tab')">📜 Archiwum Ticketów</a></li>
                </ul>
            </div>
            <div><a href="/logout" class="button btn-danger-glow is-fullwidth py-4">Wyloguj system</a></div>
        </aside>

        <main class="main-content">
            <div id="status-tab" class="tab-content is-active">
                <div class="box glass-box p-6" style="max-width: 600px;">
                    <h2 class="title is-3 has-text-white mb-4">Ustawienia Aktywności Bota</h2>
                    <form method="POST" action="/update-status">
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
                    <form method="POST" action="/create-channel">
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
                            <p class="has-text-grey has-text-centered" style="margin-top: 200px;">Wybierz osobę z bazy danych, aby otworzyć profil.</p>
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
                                <input type="text" id="chat-input-msg" class="input custom-input" placeholder="Napisz coś jako bot na kanale..." disabled>
                                <button id="chat-send-btn" class="button btn-glow" disabled>Wyślij</button>
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
function switchTab(evt, tabId) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("is-active"));
    document.querySelectorAll(".menu-list a").forEach(el => el.classList.remove("is-active"));
    document.getElementById(tabId).classList.add("is-active");
    evt.currentTarget.classList.add("is-active");
    if (tabId === 'tickets-tab') fetchTickets();
    if (tabId === 'chat-tab') fetchChatChannels();
    if (tabId === 'users-tab') fetchUsers();
    if (tabId === 'archive-tab') fetchArchive();
}
function fetchTickets() { fetch('/api/tickets').then(r=>r.json()).then(data=>{ document.getElementById('tickets-list').innerHTML = data.length ? data.map(t=>`<div class="ticket-badge"><strong>#${t.name}</strong></div>`).join('') : '<p class="has-text-grey-light">Brak otwartych procesów zgłoszeniowych.</p>'; }); }
function fetchChatChannels() { fetch('/api/tickets').then(r=>r.json()).then(data=>{ document.getElementById('chat-channels').innerHTML = data.length ? data.map(t=>`<div class="chat-channel-item" onclick="selectChatChannel(${t.id})">#${t.name}</div>`).join('') : '<p class="has-text-grey is-size-7">Brak otwartych kanałów.</p>'; }); }
function selectChatChannel(channelId) { document.getElementById('chat-input-msg').disabled = false; document.getElementById('chat-send-btn').disabled = false; }
function fetchUsers() { fetch('/api/users').then(r=>r.json()).then(data=>{ window.allUsersData = data; renderUsersList(data); }); }
function renderUsersList(users) { document.getElementById('user-scroll-container').innerHTML = users.length ? users.map(u=>`<div class="user-list-item" onclick="selectUser(${u.id})"><img src="${u.avatar}"><span>${u.name}</span></div>`).join('') : '<p class="has-text-grey is-size-7 p-2">Brak użytkowników.</p>'; }
function filterUsers() { const q = document.getElementById('user-search-input').value.toLowerCase().trim(); renderUsersList((window.allUsersData || []).filter(u => u.name.toLowerCase().includes(q))); }
function selectUser(userId) { fetch(`/api/users/${userId}`).then(r=>r.json()).then(u=>{ document.getElementById('user-profile').innerHTML = u.error ? `<p class="has-text-danger">${u.error}</p>` : `<h3 class="title is-4 has-text-white">${u.name}</h3><p>ID: ${u.id}</p>`; }); }
function fetchArchive() { fetch('/api/archive').then(r=>r.json()).then(data=>{ document.getElementById('archive-list').innerHTML = data.length ? data.map(item=>`<div class="archive-item"><div><strong>#${item.channel_name}</strong></div></div>`).join('') : '<p class="has-text-grey">Archiwum systemowe jest puste.</p>'; }); }
</script>

</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Autoryzacja Matrix</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {{ SHARED_STYLE | safe }}
    <style>.login-box { max-width: 450px; margin: 15vh auto; padding: 3rem; }</style>
</head>
<body>
    <div class="animated-bg"></div>
    <div class="box glass-box login-box">
        <h2 class="title is-3 has-text-centered glow-text mb-5">SECURE LOGIN</h2>
        {% if error %}<p class="notification is-danger is-light p-3 mb-4">{{ error }}</p>{% endif %}
        <form method="POST">
            <div class="field mb-4">
                <label class="label has-text-grey-light is-size-7">PASSWORD CONTROL STRIP</label>
                <input class="input custom-input py-4" type="password" name="password" required placeholder="••••••••">
            </div>
            <button type="submit" class="button btn-glow is-fullwidth py-4">Inicjalizuj Sesję</button>
        </form>
    </div>
</body>
</html>
"""

# ===============================
# FLASK
# ===============================

@app.before_request
def require_login():
    if request.path in ['/login', '/logout'] or request.path.startswith('/api/'):
        return
    if 'authorized' not in session:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        pwd = request.form.get('password')
        if pwd == DASHBOARD_PASSWORD:
            session['authorized'] = True
            return redirect('/')
        error = "Błędny klucz dostępu."
    return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE, error=error)

@app.route('/logout')
def logout():
    session.pop('authorized', None)
    return redirect('/login')

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, SHARED_STYLE=SHARED_STYLE, current_status=current_status_text)

@app.route('/update-status', methods=['POST'])
def update_status():
    global current_status_text
    status_text = request.form.get('status_text', 'Zarządzanie serwerem')
    current_status_text = status_text
    if bot.loop and bot.is_ready():
        asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord.Game(name=status_text)), bot.loop)
    return redirect('/')

@app.route('/create-channel', methods=['POST'])
def create_channel():
    ch_name = request.form.get('channel_name')
    ch_type = request.form.get('channel_type')

    async def _create():
        if bot.guilds:
            guild = bot.guilds[0]
            if ch_type == 'text':
                await guild.create_text_channel(name=ch_name)
            elif ch_type == 'voice':
                await guild.create_voice_channel(name=ch_name)

    if bot.loop and bot.is_ready():
        asyncio.run_coroutine_threadsafe(_create(), bot.loop)
    return redirect('/')

@app.route('/close-ticket-dash', methods=['POST'])
def close_ticket_dash():
    return redirect('/')

@app.route('/api/tickets')
def api_tickets():
    return jsonify([])

@app.route('/api/chat/history/<int:channel_id>')
def api_chat_history(channel_id):
    return jsonify([])

@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    return jsonify({"success": True})

@app.route('/api/users')
def api_users():
    users_list = []
    if bot.guilds:
        guild = bot.guilds[0]
        for m in list(guild.members)[:50]:
            users_list.append({"id": str(m.id), "name": m.name, "avatar": str(m.display_avatar.url)})
    return jsonify(users_list)

@app.route('/api/users/<int:user_id>')
def api_user_detail(user_id):
    if not bot.guilds:
        return jsonify({"error": "Brak bazy danych serwera."})
    guild = bot.guilds[0]
    member = guild.get_member(user_id)
    if not member:
        return jsonify({"error": "Użytkownik nieaktywny w sieci serwera."})
    return jsonify({
        "id": str(member.id),
        "name": member.name,
        "avatar": str(member.display_avatar.url),
        "created_at": member.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "roles": [r.name for r in member.roles if r.name != "@everyone"],
        "server_all_roles": [r.name for r in guild.roles if r.name != "@everyone"]
    })

@app.route('/api/archive')
def api_archive():
    return jsonify(load_archive())

# ===============================
# START
# ===============================

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ BŁĄD: Brak zmiennej środowiskowej DISCORD_TOKEN!")
    else:
        threading.Thread(target=run_flask, daemon=True).start()
        bot.run(TOKEN)
