import discord
from discord.ext import commands
from discord import Intents, utils
import os
from flask import Flask, render_template_string, request, redirect, session
from threading import Thread
import asyncio
import io
import random
import string
from datetime import datetime
from typing import List 
from PIL import Image, ImageDraw, ImageFont

# ===============================
# 🚨 KONFIGURACJA GLOBALNA I ZMIENNE ŚRODOWISKOWE 🚨
# ===============================

ADMIN_IDS: List[int] = [652507356105539585, 550959315700154368, 590215623259193371]
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PWD", "Kuba123!")

app = Flask('')
app.secret_key = os.environ.get("FLASK_SECRET", "super-tajny-klucz-kubusiowo")

bot_instance = None

# ===============================
# 🎨 NOWOCZESNE SZABLONY HTML/CSS (SIDEBAR + NEON GLOW)
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
    .btn-action:hover {
        box-shadow: 0 6px 20px rgba(46, 213, 115, 0.4);
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
        color: white;
    }
    
    .custom-input, .custom-textarea, .custom-select select {
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #fff !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
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

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
"""

# Usunięto prefiks 'f' przed potrójnym cudzysłowem, style wstrzykujemy znacznikiem Jinja {{ SHARED_STYLE }}
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
        <!-- BOCZNE MENU (SIDEBAR) -->
        <aside class="sidebar">
            <div>
                <div class="has-text-centered mb-6">
                    <h1 class="title is-4 glow-text mb-1">🎮 KUBUSIOWO</h1>
                    <p class="is-size-7 has-text-grey">v2.5 Professional</p>
                </div>
                <ul class="menu-list">
                    <li><a href="#" class="is-active" onclick="switchTab(event, 'status-tab')">⚙️ Status bota</a></li>
                    <li><a href="#" onclick="switchTab(event, 'commands-tab')">🛠️ Panele i Komendy</a></li>
                    <li><a href="#" onclick="switchTab(event, 'announcements-tab')">📢 Ogłoszenia</a></li>
                </ul>
            </div>
            <div>
                <a href="/logout" class="button btn-danger-glow is-fullwidth">Wyloguj się</a>
            </div>
        </aside>

        <!-- GŁÓWNA TREŚĆ -->
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

            <!-- ZAKŁADKA 2: PANALE I KOMENDY SERWEROWE -->
            <div id="commands-tab" class="tab-content">
                <div class="columns is-multiline">
                    <!-- Karta: Weryfikacja Captcha -->
                    <div class="column is-6">
                        <div class="box glass-box p-5" style="height: 100%;">
                            <h3 class="title is-4 has-text-white mb-2">🔐 System Weryfikacji Captcha</h3>
                            <p class="has-text-grey-light is-size-6 mb-4">Wysyła oficjalny panel weryfikacyjny z przyciskiem na dedykowany kanał tekstowy serwera.</p>
                            <form method="POST" action="/trigger-command">
                                <input type="hidden" name="command_type" value="verification">
                                <button type="submit" class="button btn-glow btn-action is-fullwidth">Wyślij Panel Weryfikacji</button>
                            </form>
                        </div>
                    </div>

                    <!-- Karta: System Ticketów -->
                    <div class="column is-6">
                        <div class="box glass-box p-5" style="height: 100%;">
                            <h3 class="title is-4 has-text-white mb-2">🎫 System Zgłoszeń (Tickety)</h3>
                            <p class="has-text-grey-light is-size-6 mb-4">Tworzy na wskazanym kanale widget umożliwiający użytkownikom otwieranie prywatnych spraw.</p>
                            <form method="POST" action="/trigger-command">
                                <input type="hidden" name="command_type" value="ticket">
                                <div class="field mb-3">
                                    <div class="control">
                                        <input class="input custom-input is-small" type="text" name="target_channel_id" placeholder="ID kanału (opcjonalnie, puste = obecny)">
                                    </div>
                                </div>
                                <button type="submit" class="button btn-glow btn-action is-fullwidth">Wyślij Panel Ticketów</button>
                            </form>
                        </div>
                    </div>

                    <!-- Karta: Kreator Ankiet -->
                    <div class="column is-6">
                        <div class="box glass-box p-5" style="height: 100%;">
                            <h3 class="title is-4 has-text-white mb-2">📊 Panel do Tworzenia Ankiet</h3>
                            <p class="has-text-grey-light is-size-6 mb-4">Wrzuca przycisk, który pozwala uprawnionym administratorom na błyskawiczne otwieranie ankiet.</p>
                            <form method="POST" action="/trigger-command">
                                <input type="hidden" name="command_type" value="poll">
                                <button type="submit" class="button btn-glow btn-action is-fullwidth">Wyślij Kreator Ankiet</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ZAKŁADKA 3: OGŁOSZENIA -->
            <div id="announcements-tab" class="tab-content">
                <div class="box glass-box p-6">
                    <h2 class="title is-3 has-text-white mb-2">📢 Nadaj Komunikat globalny</h2>
                    <p class="subtitle is-6 has-text-grey-light">Wyślij sformatowaną wiadomość na dowolny kanał tekstowy na serwerze.</p>
                    <hr style="background-color: rgba(255,255,255,0.05)">
                    <form method="POST" action="/send-announcement">
                        <div class="field mb-4">
                            <label class="label has-text-grey-light">ID Kanału tekstowego:</label>
                            <div class="control">
                                <input class="input custom-input" type="text" name="channel_id" required placeholder="Wklej ID kanału docelowego">
                            </div>
                        </div>
                        <div class="field mb-4">
                            <label class="label has-text-grey-light">Treść wiadomości:</label>
                            <div class="control">
                                <textarea class="textarea custom-textarea" name="msg_content" rows="5" required placeholder="Napisz coś... Możesz używać oznaczeń typu @everyone lub formatowania Markdown."></textarea>
                            </div>
                        </div>
                        <button type="submit" class="button btn-glow px-5">Wyślij Komunikat</button>
                    </form>
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
        }
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
# 🌐 TRASY FLASK (ZARZĄDZANIE)
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

@app.route('/send-announcement', methods=['POST'])
def send_announcement():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    channel_id = request.form.get('channel_id', '')
    msg_content = request.form.get('msg_content', '')
    
    try:
        ch_id = int(channel_id)
        asyncio.run_coroutine_threadsafe(send_dash_msg(ch_id, msg_content), bot_instance.loop)
        return redirect('/?msg=Komunikat+wyslany+pomyslnie!')
    except ValueError:
        return redirect('/?msg=Bledne+ID+kanalu!')

@app.route('/trigger-command', methods=['POST'])
def trigger_command():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    cmd_type = request.form.get('command_type')
    target_ch = request.form.get('target_channel_id', '').strip()

    asyncio.run_coroutine_threadsafe(execute_panel_deploy(cmd_type, target_ch), bot_instance.loop)
    return redirect(f'/?msg=Komenda+{cmd_type}+wykonana+na+serwerze!')

async def execute_panel_deploy(cmd_type: str, target_ch_id: str):
    for guild in bot_instance.guilds:
        channel = None
        if target_ch_id.isdigit():
            channel = bot_instance.get_channel(int(target_ch_id))
        
        if not channel:
            if cmd_type == "verification":
                channel = utils.get(guild.text_channels, name="│🔐│weryfikacja")
            elif cmd_type == "ticket":
                channel = utils.get(guild.text_channels, name="│🎫│tickety") or utils.get(guild.text_channels, name="general")
            elif cmd_type == "poll":
                channel = utils.get(guild.text_channels, name="│📊│ankiety") or utils.get(guild.text_channels, name="general")

        if channel:
            if cmd_type == "verification":
                embed = discord.Embed(
                    title="🔒 System Bezpieczeństwa & Weryfikacji",
                    description="Aby uzyskać pełny dostęp do pozostałych kanałów naszego serwera, musisz udowodnić, że nie jesteś botem.\n\n👉 **Kliknij zielony przycisk poniżej**, przepisz wygenerowany kod Captcha i ciesz się grą!",
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed, view=VerificationView())
            elif cmd_type == "ticket":
                embed = discord.Embed(title="🎫 System zgłoszeń", description="Masz problem? Chcesz o coś zapytać? Kliknij przycisk poniżej, aby otworzyć prywatne zgłoszenie do administracji serwera.", color=discord.Color.purple())
                await channel.send(embed=embed, view=TicketButton())
            elif cmd_type == "poll":
                embed = discord.Embed(title="📊 Panel tworzenia ankiet", description="Kliknij przycisk poniżej, aby otworzyć formularz ankiety (Dla Administracji).", color=discord.Color.gold())
                await channel.send(embed=embed, view=StartPollView())

async def send_dash_msg(channel_id: int, content: str):
    channel = bot_instance.get_channel(channel_id)
    if channel:
        await channel.send(content)

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True 
    t.start()


# ===============================
# 🔐 SYSTEM CAPTCHA (Weryfikacja)
# ===============================

def generate_captcha() -> tuple:
    text = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    img = Image.new('RGB', (200, 70), color=(25, 22, 43))
    d = ImageDraw.Draw(img)
    
    for _ in range(12):
        x1, y1 = random.randint(0, 200), random.randint(0, 70)
        x2, y2 = random.randint(0, 200), random.randint(0, 70)
        d.line([(x1, y1), (x2, y2)], fill=(88, 101, 242), width=1)
        
    d.text((60, 25), text, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return text, buf

class CaptchaModal(discord.ui.Modal, title="🔐 Przepisz Kod z Obrazka"):
    def __init__(self, correct_code: str):
        super().__init__(timeout=60.0)
        self.correct_code = correct_code
        
    user_input = discord.ui.TextInput(label="Wpisz kod widoczny na obrazku:", placeholder="Wielkość liter nie ma znaczenia", max_length=10, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        log_channel = utils.get(guild.text_channels, name="│📝│logi-weryfikacji")
        
        if self.user_input.value.strip().upper() == self.correct_code:
            role_verified = utils.get(guild.roles, name="ZWERYFIKOWANY")
            role_member = utils.get(guild.roles, name="Member")
            
            if role_verified: await member.add_roles(role_verified)
            if role_member: await member.remove_roles(role_member)
            
            await interaction.response.send_message("✅ Weryfikacja pomyślna! Witamy na serwerze!", ephemeral=True)
            if log_channel:
                await log_channel.send(f"🟢 Użytkownik {member.mention} zmienił status na zweryfikowany.")
        else:
            await interaction.response.send_message("❌ Niepoprawny kod! Spróbuj ponownie.", ephemeral=True)

class VerificationView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Zweryfikuj się 🔐", style=discord.ButtonStyle.success, custom_id="verify_user_btn")
    async def verify_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        if utils.get(interaction.user.roles, name="ZWERYFIKOWANY"):
            await interaction.response.send_message("Jesteś już pomyślnie zweryfikowany!", ephemeral=True)
            return
        correct_code, img_buf = generate_captcha()
        file = discord.File(img_buf, filename="captcha.png")
        await interaction.response.send_message(content="👇 Przepisz kod:", file=file, view=CaptchaTriggerView(correct_code), ephemeral=True)

class CaptchaTriggerView(discord.ui.View):
    def __init__(self, correct_code: str):
        super().__init__(timeout=60.0)
        self.correct_code = correct_code
    @discord.ui.button(label="Wpisz Kod 📝", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CaptchaModal(self.correct_code))


# ===============================
# 📊 ANKIETY I TICKETY 
# ===============================

class PollModal(discord.ui.Modal, title="📊 Nowa Ankieta"):
    pytanie = discord.ui.TextInput(label="Pytanie", max_length=256, required=True)
    opcja_a = discord.ui.TextInput(label="Opcja A", max_length=100, required=True)
    opcja_b = discord.ui.TextInput(label="Opcja B", max_length=100, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        view = PollVotesView(question=self.pytanie.value, opt_a=self.opcja_a.value, opt_b=self.opcja_b.value)
        await interaction.channel.send(embed=view.build_embed(), view=view)
        await interaction.response.send_message("✅ Ankieta wygenerowana!", ephemeral=True)

class PollVotesView(discord.ui.View):
    def __init__(self, question: str, opt_a: str, opt_b: str):
        super().__init__(timeout=None)
        self.question = question
        self.opt_a_text = opt_a
        self.opt_b_text = opt_b
        self.votes_a = set()
        self.votes_b = set()

    def build_embed(self):
        total = len(self.votes_a) + len(self.votes_b)
        pct_a = (len(self.votes_a) / total * 100) if total > 0 else 0
        pct_b = (len(self.votes_b) / total * 100) if total > 0 else 0
        embed = discord.Embed(title=f"📊 {self.question}", color=discord.Color.brand_green())
        embed.add_field(name=f"🅰️ {self.opt_a_text}", value=f"**{pct_a:.0f}%** ({len(self.votes_a)})", inline=False)
        embed.add_field(name=f"🅱️ {self.opt_b_text}", value=f"**{pct_b:.0f}%** ({len(self.votes_b)})", inline=False)
        return embed

    @discord.ui.button(label="🅰️", style=discord.ButtonStyle.primary, custom_id="vote_a_btn")
    async def vote_a(self, interaction, btn):
        self.votes_b.discard(interaction.user.id)
        self.votes_a.add(interaction.user.id)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="🅱️", style=discord.ButtonStyle.primary, custom_id="vote_b_btn")
    async def vote_b(self, interaction, btn):
        self.votes_a.discard(interaction.user.id)
        self.votes_b.add(interaction.user.id)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

class StartPollView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Stwórz Nową Ankietę 📊", style=discord.ButtonStyle.success, custom_id="start_poll_btn_persistent")
    async def start_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PollModal())

class TicketModal(discord.ui.Modal, title="🎫 Zgłoszenie"):
    temat = discord.ui.TextInput(label="Temat", max_length=100, required=True)
    opis = discord.ui.TextInput(label="Opis", style=discord.TextStyle.long, max_length=1000, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        channel_name = f"ticket-{member.name.lower()}"

        if utils.get(guild.text_channels, name=channel_name):
            await interaction.response.send_message("Masz już otwarty jeden ticket!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        embed = discord.Embed(title="🎫 Nowe Zgłoszenie", description=f"Witaj {member.mention}!", color=discord.Color.green())
        embed.add_field(name="📌 Temat:", value=self.temat.value, inline=False)
        embed.add_field(name="📝 Opis:", value=self.opis.value, inline=False)
        await ticket_channel.send(embed=embed, view=TicketControlView(self.temat.value, self.opis.value))
        await interaction.response.send_message(f"Stworzono ticket! {ticket_channel.mention}", ephemeral=True)

class TicketButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Stwórz Ticket ✉️", style=discord.ButtonStyle.primary, custom_id="create_ticket_btn")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())

class TicketControlView(discord.ui.View):
    def __init__(self, topic="Brak", desc="Brak"):
        super().__init__(timeout=None)
        self.claimed_by = None
        self.topic = topic
        self.desc = desc

    @discord.ui.button(label="Zajmij się zgłoszeniem ✋", style=discord.ButtonStyle.success, custom_id="claim_ticket_btn")
    async def claim_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in ADMIN_IDS: return
        self.claimed_by = interaction.user
        button.disabled = True
        button.label = f"Obsługuje: {interaction.user.name} 🛠️"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Zamknij Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_control_btn")
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.channel.send("⚠️ Usuwanie kanału za 5 sekund...")
        await asyncio.sleep(5)
        await interaction.channel.delete()


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
    bot.add_view(StartPollView())
    bot.add_view(TicketButton())
    bot.add_view(TicketControlView())
    bot.add_view(VerificationView())

@bot.event
async def on_ready():
    print(f'🤖 Bot online: {bot.user}')

if __name__ == "__main__":
    keep_alive() 
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN: bot.run(TOKEN)
