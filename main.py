import discord
from discord.ext import commands
from discord import Intents, utils
import os
from flask import Flask, render_template_string, request, redirect, session, jsonify
from threading import Thread
import asyncio
from typing import List

# ===============================
# 🚨 KONFIGURACJA GLOBALNA I ZMIENNE ŚRODOWISKOWE 🚨
# ===============================

ADMIN_IDS: List[int] = [652507356105539585, 550959315700154368, 590215623259193371]
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PWD", "Kuba123!")

app = Flask('')
app.secret_key = os.environ.get("FLASK_SECRET", "super-tajny-klucz-kubusiowo")

bot_instance = None

# ===============================
# 🎨 NOWOCZESNE STYLE CSS
# ===============================

SHARED_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    body {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #0a0813 0%, #110d22 50%, #050307 100%);
        color: #e2e8f0;
        min-height: 100vh;
        margin: 0;
    }
    
    .dashboard-container {
        display: flex;
        min-height: 100vh;
    }
    
    .sidebar {
        width: 260px;
        background: rgba(15, 12, 30, 0.6);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        padding: 2rem 1.5rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .main-content {
        flex: 1;
        padding: 2.5rem;
        overflow-y: auto;
    }
    
    .menu-list a {
        color: #a0aec0;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    .menu-list a:hover, .menu-list a.is-active {
        background: rgba(88, 101, 242, 0.15);
        color: #fff;
        text-shadow: 0 0 10px rgba(88, 101, 242, 0.5);
        border-left: 4px solid #5865f2;
        padding-left: 12px;
    }
    
    .glass-box {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }
    
    .glass-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px 0 rgba(88, 101, 242, 0.15);
        border-color: rgba(88, 101, 242, 0.25);
    }
    
    .glow-text {
        color: #fff;
        text-shadow: 0 0 12px rgba(88, 101, 242, 0.6);
    }
    
    .btn-glow {
        background: linear-gradient(45deg, #7289da, #5865f2);
        color: white;
        border: none;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(88, 101, 242, 0.3);
    }
    
    .btn-glow:hover {
        background: linear-gradient(45deg, #5865f2, #4752c4);
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(88, 101, 242, 0.5);
        color: white;
    }

    .btn-action {
        background: linear-gradient(45deg, #2ed573, #1abc9c);
    }
    
    .btn-danger-glow {
        background: linear-gradient(45deg, #ff4757, #ee5253);
        color: white;
        border: none;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .btn-danger-glow:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(238, 82, 83, 0.4);
    }
    
    .custom-input, .custom-textarea, .custom-select select {
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #fff !important;
        border-radius: 8px !important;
    }
    
    .custom-input:focus, .custom-textarea:focus {
        border-color: #5865f2 !important;
        box-shadow: 0 0 0 3px rgba(88, 101, 242, 0.2) !important;
    }
    
    .tab-content {
        display: none;
        animation: fadeIn 0.4s ease forwards;
    }
    
    .tab-content.is-active {
        display: block;
    }
    
    .notification {
        background: rgba(46, 213, 115, 0.12) !important;
        border: 1px solid rgba(46, 213, 115, 0.4) !important;
        color: #2ed573 !important;
        border-radius: 8px;
    }

    .ticket-badge {
        background: rgba(88, 101, 242, 0.2);
        border: 1px solid #5865f2;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
"""

# ===============================
# 📄 SZABLONY HTML (JINJA2 SAFE)
# ===============================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Zarządzanie Serwerem</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {{ SHARED_STYLE | safe }}
</head>
<body>
    <div class="dashboard-container">
        <aside class="sidebar">
            <div>
                <div class="has-text-centered mb-6">
                    <h1 class="title is-4 glow-text mb-1">🎮 KUBUSIOWO</h1>
                    <p class="is-size-7 has-text-grey">v3.0 Control & Tickets</p>
                </div>
                <ul class="menu-list">
                    <li><a href="#" class="is-active" onclick="switchTab(event, 'status-tab')">⚙️ Status bota</a></li>
                    <li><a href="#" onclick="switchTab(event, 'management-tab')">🛠️ Zarządzanie</a></li>
                    <li><a href="#" onclick="switchTab(event, 'tickets-tab')">🎫 Aktywne Tickety</a></li>
                </ul>
            </div>
            <div>
                <a href="/logout" class="button btn-danger-glow is-fullwidth">Wyloguj się</a>
            </div>
        </aside>

        <main class="main-content">
            {% if message %}
                <div class="notification p-3 mb-5">{{ message }}</div>
            {% endif %}

            <!-- ZAKŁADKA 1: STATUS -->
            <div id="status-tab" class="tab-content is-active">
                <div class="box glass-box p-6 mb-5">
                    <h2 class="title is-3 has-text-white mb-2">Ustawienia Aktywności</h2>
                    <p class="subtitle is-6 has-text-grey-light">Zmień opis wyświetlany pod nickiem bota na Discordzie.</p>
                    <hr style="background-color: rgba(255,255,255,0.05)">
                    <form method="POST" action="/update-status">
                        <div class="field mb-4">
                            <label class="label has-text-grey-light">Tekst aktywności (Gra w...):</label>
                            <div class="control">
                                <input class="input custom-input" type="text" name="status_text" placeholder="np. Zarządzam serwerem..." value="{{ current_status }}">
                            </div>
                        </div>
                        <button type="submit" class="button btn-glow px-5">Zaktualizuj status</button>
                    </form>
                </div>
            </div>

            <!-- ZAKŁADKA 2: ZARZĄDZANIE (KANAŁY I ROLE) -->
            <div id="management-tab" class="tab-content">
                <div class="columns">
                    <!-- Tworzenie Kanałów -->
                    <div class="column is-6">
                        <div class="box glass-box p-5">
                            <h3 class="title is-4 has-text-white mb-3">📁 Stwórz Nowy Kanał</h3>
                            <form method="POST" action="/create-channel">
                                <div class="field mb-3">
                                    <label class="label has-text-grey-light">Nazwa kanału:</label>
                                    <input class="input custom-input" type="text" name="channel_name" required placeholder="np. ogólny">
                                </div>
                                <div class="field mb-4">
                                    <label class="label has-text-grey-light">Typ kanału:</label>
                                    <div class="control is-expanded">
                                        <div class="select is-fullwidth custom-select">
                                            <select name="channel_type">
                                                <option value="text">Tekstowy</option>
                                                <option value="voice">Głosowy</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <button type="submit" class="button btn-glow btn-action is-fullwidth">Stwórz Kanał</button>
                            </form>
                        </div>
                    </div>

                    <!-- Nadawanie Ról -->
                    <div class="column is-6">
                        <div class="box glass-box p-5">
                            <h3 class="title is-4 has-text-white mb-3">👤 Nadaj Rolę Użytkownikowi</h3>
                            <form method="POST" action="/assign-role">
                                <div class="field mb-3">
                                    <label class="label has-text-grey-light">ID Użytkownika:</label>
                                    <input class="input custom-input" type="text" name="user_id" required placeholder="np. 652507356105539585">
                                </div>
                                <div class="field mb-4">
                                    <label class="label has-text-grey-light">Nazwa Roli:</label>
                                    <input class="input custom-input" type="text" name="role_name" required placeholder="np. ZWERYFIKOWANY">
                                </div>
                                <button type="submit" class="button btn-glow is-fullwidth">Nadaj Rolę</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ZAKŁADKA 3: AKTYWNE TICKETY (ZAKŁADKA LIVE) -->
            <div id="tickets-tab" class="tab-content">
                <div class="box glass-box p-6">
                    <h2 class="title is-3 has-text-white mb-2">🎫 Aktywne Zgłoszenia (Tickety)</h2>
                    <p class="subtitle is-6 has-text-grey-light">Kanały ticketów aktualnie otwarte na serwerze Discord.</p>
                    <hr style="background-color: rgba(255,255,255,0.05)">
                    
                    <div id="tickets-list">
                        <p class="has-text-grey">Ładowanie ticketów...</p>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        function switchTab(evt, tabId) {
            let i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].classList.remove("is-active");
            }
            tablinks = document.querySelectorAll(".menu-list a");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].classList.remove("is-active");
            }
            document.getElementById(tabId).classList.add("is-active");
            evt.currentTarget.classList.add("is-active");
            
            if (tabId === 'tickets-tab') {
                fetchTickets();
            }
        }

        // Funkcja pobierająca tickety w tle (AJAX)
        function fetchTickets() {
            const listDiv = document.getElementById('tickets-list');
            fetch('/api/tickets')
                .then(response => response.json())
                .then(data => {
                    listDiv.innerHTML = '';
                    if (data.length === 0) {
                        listDiv.innerHTML = '<p class="has-text-grey">Brak aktywnych ticketów na serwerze.</p>';
                        return;
                    }
                    data.forEach(ticket => {
                        const div = document.createElement('div');
                        div.className = 'ticket-badge';
                        div.innerHTML = `
                            <div>
                                <strong style="color: #fff;">#${ticket.name}</strong> 
                                <span class="has-text-grey-light is-size-7" style="margin-left: 10px;">(ID: ${ticket.id})</span>
                            </div>
                            <form method="POST" action="/close-ticket-dash" style="margin: 0;">
                                <input type="hidden" name="channel_id" value="${ticket.id}">
                                <button type="submit" class="button is-small btn-danger-glow">Zamknij z poziomu WWW</button>
                            </form>
                        `;
                        listDiv.appendChild(div);
                    });
                })
                .catch(err => {
                    listDiv.innerHTML = '<p class="has-text-danger">Błąd podczas pobierania danych.</p>';
                });
        }

        // Odświeżaj listę ticketów automatycznie co 10 sekund, jeśli zakładka jest włączona
        setInterval(() => {
            if (document.getElementById('tickets-tab').classList.contains('is-active')) {
                fetchTickets();
            }
        }, 10000);
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Zaloguj</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {{ SHARED_STYLE | safe }}
</head>
<body style="display: flex; align-items: center; min-height: 100vh;">
    <div class="container">
        <div class="box glass-box p-6" style="max-width: 420px; margin: 0 auto;">
            <h1 class="title is-3 glow-text has-text-centered mb-5">🔒 Dostęp Admina</h1>
            {% if error %}
                <div class="notification is-danger p-3 mb-4" style="background: rgba(255,71,87,0.15)!important; border:1px solid #ff4757; color:#ff4757!important;">{{ error }}</div>
            {% endif %}
            <form method="POST" action="/login">
                <div class="field mb-5">
                    <label class="label has-text-grey-light">Wpisz Klucz Autoryzacji:</label>
                    <div class="control">
                        <input class="input custom-input" type="password" name="password" required placeholder="••••••••">
                    </div>
                </div>
                <button type="submit" class="button btn-glow is-fullwidth py-4">Autoryzuj Wjazd</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

# ===============================
# 🌐 TRASY FLASK (LOGIKA WWW)
# ===============================

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE)
    
    current_status = ""
    if bot_instance and bot_instance.activity:
        current_status = bot_instance.activity.name

    return render_template_string(HTML_TEMPLATE, SHARED_STYLE=SHARED_STYLE, current_status=current_status, message=request.args.get('msg'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == DASHBOARD_PASSWORD:
        session['logged_in'] = True
        return redirect('/')
    return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE, error="Błędne hasło administratora!")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/update-status', methods=['POST'])
def update_status():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    status_text = request.form.get('status_text', '')
    asyncio.run_coroutine_threadsafe(
        bot_instance.change_presence(activity=discord.Game(name=status_text)),
        bot_instance.loop
    )
    return redirect('/?msg=Status+zostal+zaktualizowany!')

# [NOWOŚĆ] Trasa API zwracająca aktywne kanały ticketów w formacie JSON
@app.route('/api/tickets')
def api_tickets():
    if not session.get('logged_in') or not bot_instance: 
        return jsonify([])
    
    active_tickets = []
    for guild in bot_instance.guilds:
        for channel in guild.text_channels:
            if channel.name.startswith("ticket-"):
                active_tickets.append({
                    "id": str(channel.id),
                    "name": channel.name
                })
    return jsonify(active_tickets)

# [NOWOŚĆ] Zamykanie ticketów bezpośrednio z panelu WWW
@app.route('/close-ticket-dash', methods=['POST'])
def close_ticket_dash():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    ch_id = request.form.get('channel_id')
    
    if ch_id and ch_id.isdigit():
        asyncio.run_coroutine_threadsafe(delete_channel_async(int(ch_id)), bot_instance.loop)
        return redirect('/?msg=Kanal+ticketu+zostal+usuniety!')
    return redirect('/?msg=Blad+podczas+usuwania+ticketu.')

# [NOWOŚĆ] Tworzenie nowych kanałów tekstowych/głosowych ze strony www
@app.route('/create-channel', methods=['POST'])
def create_channel():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    name = request.form.get('channel_name', '').strip()
    c_type = request.form.get('channel_type', 'text')
    
    if name:
        asyncio.run_coroutine_threadsafe(create_channel_async(name, c_type), bot_instance.loop)
        return redirect('/?msg=Kanal+zostal+utworzony+na+Discordzie!')
    return redirect('/?msg=Nazwa+kanalu+nie+moze+byc+pusta.')

# [NOWOŚĆ] Przypisywanie ról użytkownikom przez stronę www
@app.route('/assign-role', methods=['POST'])
def assign_role():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    u_id = request.form.get('user_id', '').strip()
    r_name = request.form.get('role_name', '').strip()
    
    if u_id.isdigit() and r_name:
        asyncio.run_coroutine_threadsafe(assign_role_async(int(u_id), r_name), bot_instance.loop)
        return redirect('/?msg=Zlecenie+nadania+roli+wyslane!')
    return redirect('/?msg=Bledne+dane+uzytkownika+lub+roli.')

# ===============================
# ⛓️ ASYNCHRONICZNE POMOCNIKI BOTA
# ===============================

async def delete_channel_async(channel_id: int):
    channel = bot_instance.get_channel(channel_id)
    if channel:
        await channel.delete()

async def create_channel_async(name: str, channel_type: str):
    for guild in bot_instance.guilds:
        if channel_type == "text":
            await guild.create_text_channel(name=name)
        elif channel_type == "voice":
            await guild.create_voice_channel(name=name)
        break # Tworzy na pierwszym napotkanym serwerze bota

async def assign_role_async(user_id: int, role_name: str):
    for guild in bot_instance.guilds:
        member = guild.get_member(user_id) or await guild.fetch_member(user_id)
        role = utils.get(guild.roles, name=role_name)
        if member and role:
            await member.add_roles(role)
            break

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True 
    t.start()

# ===============================
# 🤖 URUCHOMIENIE BOTA
# ===============================

intents = Intents.default()
intents.message_content = True 
intents.members = True          

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def setup_hook():
    global bot_instance
    bot_instance = bot

@bot.event
async def on_ready():
    print(f'🤖 Bot online: {bot.user}')

if __name__ == "__main__":
    keep_alive() 
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN: bot.run(TOKEN)
