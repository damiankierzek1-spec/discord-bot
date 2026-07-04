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
# 🎨 NOWOCZESNE SZABLONY HTML/CSS (DARK MODE + ANIMACJE)
# ===============================

SHARED_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    body {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #0f0c20 0%, #15102a 50%, #06040a 100%);
        color: #e2e8f0;
        min-height: 100vh;
        overflow-x: hidden;
    }
    
    .glass-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(114, 137, 218, 0.2);
        border-color: rgba(114, 137, 218, 0.3);
    }
    
    .glow-text {
        color: #fff;
        text-shadow: 0 0 10px rgba(114, 137, 218, 0.6), 0 0 20px rgba(114, 137, 218, 0.4);
        animation: pulseText 3s infinite alternate;
    }
    
    .btn-glow {
        background: linear-gradient(45deg, #7289da, #5865f2);
        color: white;
        border: none;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(88, 101, 242, 0.4);
    }
    
    .btn-glow:hover {
        background: linear-gradient(45deg, #5865f2, #4752c4);
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(88, 101, 242, 0.6);
        color: white;
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
        box-shadow: 0 6px 20px rgba(238, 82, 83, 0.5);
        color: white;
    }
    
    .custom-input, .custom-textarea {
        background: rgba(0, 0, 0, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #fff !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .custom-input:focus, .custom-textarea:focus {
        border-color: #7289da !important;
        box-shadow: 0 0 0 3px rgba(114, 137, 218, 0.25) !important;
    }
    
    .notification {
        background: rgba(46, 213, 115, 0.15) !important;
        border: 1px solid #2ed573 !important;
        color: #2ed573 !important;
        animation: fadeIn 0.5s ease;
    }
    
    .notification.is-danger {
        background: rgba(255, 71, 87, 0.15) !important;
        border: 1px solid #ff4757 !important;
        color: #ff4757 !important;
    }

    @keyframes pulseText {
        0% { text-shadow: 0 0 10px rgba(114, 137, 218, 0.5); }
        100% { text-shadow: 0 0 20px rgba(114, 137, 218, 0.8), 0 0 30px rgba(88, 101, 242, 0.6); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
"""

HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {SHARED_STYLE}
</head>
<body>
    <section class="section">
        <div class="container" style="max-width: 900px;">
            <div class="box glass-box has-text-centered mb-6 p-6">
                <h1 class="title is-1 glow-text mb-2">🤖 KUBUSIOWO PANEL</h1>
                <p class="subtitle is-6 has-text-grey-light">Centrum Dowodzenia Twoim Botem Discord</p>
                
                {% if message %}
                    <div class="notification p-3 mt-4">{{ message }}</div>
                {% endif %}
            </div>
            
            <div class="columns is-desktop">
                <!-- LEWA KOLUMNA: USTAWIENIA STATUSU -->
                <div class="column">
                    <div class="box glass-box p-5">
                        <h3 class="title is-4 has-text-white mb-4">⚙️ Status Aplikacji</h3>
                        <form method="POST" action="/update-status">
                            <div class="field mb-4">
                                <label class="label has-text-grey-light">Tekst aktywności bota:</label>
                                <div class="control">
                                    <input class="input custom-input" type="text" name="status_text" placeholder="np. Pilnuje porządku..." value="{{ current_status }}">
                                </div>
                            </div>
                            <button type="submit" class="button btn-glow is-fullwidth">Zaktualizuj Status</button>
                        </form>
                    </div>
                </div>
                
                <!-- PRAWA KOLUMNA: OGŁOSZENIA -->
                <div class="column">
                    <div class="box glass-box p-5">
                        <h3 class="title is-4 has-text-white mb-4">📢 Nadaj Komunikat</h3>
                        <form method="POST" action="/send-announcement">
                            <div class="field mb-3">
                                <label class="label has-text-grey-light">ID Kanału tekstowego:</label>
                                <div class="control">
                                    <input class="input custom-input" type="text" name="channel_id" placeholder="Wklej ID kanału docelowego">
                                </div>
                            </div>
                            <div class="field mb-4">
                                <label class="label has-text-grey-light">Treść wiadomości:</label>
                                <div class="control">
                                    <textarea class="textarea custom-textarea" name="msg_content" rows="3" placeholder="Wpisz treść, którą bot ma wysłać..."></textarea>
                                </div>
                            </div>
                            <button type="submit" class="button btn-glow is-fullwidth">Wyślij do Discord</button>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="has-text-centered mt-5">
                <a href="/logout" class="button btn-danger-glow px-5">Wyloguj Panel</a>
            </div>
        </div>
    </section>
</body>
</html>
"""

LOGIN_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Logowanie</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {SHARED_STYLE}
</head>
<body style="display: flex; align-items: center; min-height: 100vh;">
    <div class="container">
        <div class="box glass-box p-6 style="max-width: 420px; margin: 0 auto;">
            <h1 class="title is-3 glow-text has-text-centered mb-5">🔒 Dostęp Admina</h1>
            
            {% if error %}
                <div class="notification is-danger p-3 mb-4">{{ error }}</div>
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
# 🌐 TRASY FLASK (Poprawione methods)
# ===============================

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string(LOGIN_TEMPLATE)
    
    current_status = ""
    if bot_instance and bot_instance.activity:
        current_status = bot_instance.activity.name

    return render_template_string(HTML_TEMPLATE, current_status=current_status, message=request.args.get('msg'))

@app.route('/login', methods=['POST'])  # <-- NAPRAWIONE Z 'models' NA 'methods'
def login():
    if request.form.get('password') == DASHBOARD_PASSWORD:
        session['logged_in'] = True
        return redirect('/')
    return render_template_string(LOGIN_TEMPLATE, error="Błędne hasło administratora!")

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
    
    asyncio.run_coroutine_threadsafe(
        log_to_dashboard_channel(f"⚙️ **Dashboard**: Zmieniono status bota na: `{status_text}`"),
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
        return redirect('/?msg=Wiadomosc+wyslana!')
    except ValueError:
        return redirect('/?msg=Bledne+ID+kanalu!')

async def send_dash_msg(channel_id: int, content: str):
    channel = bot_instance.get_channel(channel_id)
    if channel:
        await channel.send(content)
        await log_to_dashboard_channel(f"📢 **Dashboard**: Wysłano wiadomość na kanał {channel.mention}:\n```\n{content}\n```")

async def log_to_dashboard_channel(text: str):
    for guild in bot_instance.guilds:
        log_ch = utils.get(guild.text_channels, name="│⚙️│logi-dashboard")
        if log_ch:
            await log_ch.send(text)

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
    img = Image.new('RGB', (200, 70), color=(25, 22, 43)) # Ciemne tło dopasowane do motywu
    d = ImageDraw.Draw(img)
    
    for _ in range(12):
        x1 = random.randint(0, 200)
        y1 = random.randint(0, 70)
        x2 = random.randint(0, 200)
        y2 = random.randint(0, 70)
        d.line([(x1, y1), (x2, y2)], fill=(random.randint(88, 114), random.randint(101, 137), 242), width=1)
        
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
                await log_channel.send(f"🟢 Użytkownik {member.mention} (`{member.name}`) przeszedł weryfikację Captcha.")
        else:
            await interaction.response.send_message("❌ Niepoprawny kod! Spróbuj ponownie klikając przycisk.", ephemeral=True)
            if log_channel:
                await log_channel.send(f"🔴 Użytkownik {member.mention} wpisał błędny kod.")

class VerificationView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="Zweryfikuj się 🔐", style=discord.ButtonStyle.success, custom_id="verify_user_btn")
    async def verify_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        if utils.get(interaction.user.roles, name="ZWERYFIKOWANY"):
            await interaction.response.send_message("Jesteś już pomyślnie zweryfikowany!", ephemeral=True)
            return
            
        correct_code, img_buf = generate_captcha()
        file = discord.File(img_buf, filename="captcha.png")
        
        await interaction.response.send_message(
            content="👇 Przepisz poniższy kod w okienku formularza!", 
            file=file, 
            view=CaptchaTriggerView(correct_code), 
            ephemeral=True
        )

class CaptchaTriggerView(discord.ui.View):
    def __init__(self, correct_code: str):
        super().__init__(timeout=60.0)
        self.correct_code = correct_code

    @discord.ui.button(label="Wpisz Kod 📝", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CaptchaModal(self.correct_code))


# ===============================
# 📊 SYSTEM TICKETÓW I ANKIET 
# ===============================

class PollModal(discord.ui.Modal, title="📊 Tworzenie nowej ankiety"):
    pytanie = discord.ui.TextInput(label="Wpisz pytanie ankiety", placeholder="np. Gramy dzisiaj w turniej?", max_length=256, required=True)
    opcja_a = discord.ui.TextInput(label="Opcja A", placeholder="np. Tak, jasne! 🔥", max_length=100, required=True)
    opcja_b = discord.ui.TextInput(label="Opcja B", placeholder="np. Nie, brak czasu ❌", max_length=100, required=True)

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

    def get_progress_bar(self, percentage: float) -> str:
        filled = max(0, min(10, int(round(percentage / 10))))
        return "█" * filled + "░" * (10 - filled)

    def build_embed(self):
        total = len(self.votes_a) + len(self.votes_b)
        pct_a = (len(self.votes_a) / total * 100) if total > 0 else 0
        pct_b = (len(self.votes_b) / total * 100) if total > 0 else 0
        embed = discord.Embed(title=f"📊 {self.question}", color=discord.Color.brand_green())
        embed.add_field(name=f"🅰️ {self.opt_a_text}", value=f"`{self.get_progress_bar(pct_a)}` **{pct_a:.0f}%** ({len(self.votes_a)})", inline=False)
        embed.add_field(name=f"🅱️ {self.opt_b_text}", value=f"`{self.get_progress_bar(pct_b)}` **{pct_b:.0f}%** ({len(self.votes_b)})", inline=False)
        return embed

    @discord.ui.button(label="🅰️ Opcja A", style=discord.ButtonStyle.primary, custom_id="vote_a_btn")
    async def vote_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes_b.discard(interaction.user.id)
        self.votes_a.add(interaction.user.id)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="🅱️ Opcja B", style=discord.ButtonStyle.primary, custom_id="vote_b_btn")
    async def vote_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes_a.discard(interaction.user.id)
        self.votes_b.add(interaction.user.id)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

class StartPollView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Stwórz Nową Ankietę 📊", style=discord.ButtonStyle.success, custom_id="start_poll_btn_persistent")
    async def start_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in ADMIN_IDS: return
        await interaction.response.send_modal(PollModal())

class TicketModal(discord.ui.Modal, title="🎫 Formularz Zgłoszeniowy"):
    temat = discord.ui.TextInput(label="Podaj temat zgłoszenia", placeholder="np. Błąd na serwerze...", max_length=100, required=True)
    opis = discord.ui.TextInput(label="Opisz krótko swoją sprawę", style=discord.TextStyle.long, max_length=1000, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        channel_name = f"ticket-{member.name.lower()}"

        if utils.get(guild.text_channels, name=channel_name):
            await interaction.response.send_message("Masz już otwarty jeden ticket!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        admin_role = utils.get(guild.roles, name="Admin") 
        if admin_role: overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        embed = discord.Embed(title="🎫 Nowe Zgłoszenie", description=f"Witaj {member.mention}! Administracja zajmie się Twoją sprawą.", color=discord.Color.green())
        embed.add_field(name="📌 Temat:", value=f"```\n{self.temat.value}\n```", inline=False)
        embed.add_field(name="📝 Opis:", value=f"```\n{self.opis.value}\n```", inline=False)

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
        button.label = f"Obsługiwane przez: {interaction.user.name} 🛠️"
        button.style = discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"➡️ {interaction.user.mention} przejął zgłoszenie.")

    @discord.ui.button(label="Zamknij Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_control_btn")
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(view=self)
        embed = discord.Embed(title="⭐ Oceń pomoc", description="Wybierz ocenę gwiazdkową.", color=discord.Color.gold())
        await interaction.channel.send(embed=embed, view=FeedbackView(self.claimed_by, interaction.user, self.topic, self.desc))

class FeedbackView(discord.ui.View):
    def __init__(self, claimed_by, closer, topic, desc):
        super().__init__(timeout=60.0)
        self.claimed_by = claimed_by
        self.closer = closer
        self.topic = topic
        self.desc = desc
        self.rating = "Brak"

    async def handle_rating(self, interaction: discord.Interaction, stars: str):
        self.rating = stars
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(view=self)
        
        log_content = f"TRANSKRYPCJA: {interaction.channel.name}\nOcena: {self.rating}\nTemat: {self.topic}\nOpis: {self.desc}\n\n"
        async for msg in interaction.channel.history(limit=None, oldest_first=True):
            log_content += f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author.name}: {msg.content}\n"
            
        file_data = io.BytesIO(log_content.encode('utf-8'))
        log_file = discord.File(file_data, filename=f"log-{interaction.channel.name}.txt")
        
        log_channel = utils.get(interaction.guild.text_channels, name="logi-ticketow")
        if log_channel:
            await log_channel.send(content=f"🔒 Ticket **{interaction.channel.name}** zamknięty przez {self.closer.name}. Ocena: {self.rating}", file=log_file)
            
        await interaction.channel.send("⚠️ Kanał zostanie usunięty za 5 sekund...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="⭐", style=discord.ButtonStyle.primary)
    async def s1(self, interaction, btn): await self.handle_rating(interaction, "1/5")
    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def s3(self, interaction, btn): await self.handle_rating(interaction, "3/5")
    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def s5(self, interaction, btn): await self.handle_rating(interaction, "5/5")


# ===============================
# 🤖 BOT SEKCJA GŁÓWNA
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
    print("✨ Rejestracja widoków powiodła się.")

@bot.event
async def on_ready():
    print(f'🤖 Bot uruchomiony jako: {bot.user}')

@bot.event
async def on_member_join(member):
    role_member = utils.get(member.guild.roles, name="Member")
    if role_member:
        await member.add_roles(role_member)
        
    channel = utils.get(member.guild.text_channels, name="⌊przyloty⌉⌊🌆⌉")
    if channel:
        embed = discord.Embed(title="🌆 Nowy użytkownik!", description=f"{member.mention} dołączył. Przejdź na kanał weryfikacyjny, aby uzyskać dostęp!", color=discord.Color.green())
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = utils.get(member.guild.text_channels, name="⌊odloty⌉⌊🌇⌉")
    if channel:
        await channel.send(f"🌇 Użytkownik **{member.name}** opuścił nasz serwer.")


# ===============================
# 🚀 KOMENDY ADMINISTRACYJNE
# ===============================

@bot.command(name="setup-weryfikacja")
@commands.has_permissions(administrator=True)
async def setup_weryfikacja_cmd(ctx):
    ch_verify = utils.get(ctx.guild.text_channels, name="│🔐│weryfikacja")
    if not ch_verify:
        await ctx.send("❌ Nie znalazłem kanału o nazwie `│🔐│weryfikacja`!")
        return
        
    embed = discord.Embed(
        title="🔒 System Bezpieczeństwa & Weryfikacji",
        description="Aby uzyskać pełny dostęp do pozostałych kanałów naszego serwera, musisz udowodnić, że nie jesteś botem.\n\n👉 **Kliknij zielony przycisk poniżej**, przepisz wygenerowany kod Captcha i ciesz się grą!",
        color=discord.Color.blue()
    )
    await ch_verify.send(embed=embed, view=VerificationView())
    await ctx.send("✅ Panel weryfikacyjny został wysłany na odpowiedni kanał!")

@bot.command(name="pomoc")
@commands.has_permissions(administrator=True)
async def pomoc_cmd(ctx):
    embed = discord.Embed(title="⚙️ Lista Komend Kubusiowo", color=discord.Color.gold())
    embed.add_field(name="🔒 !setup-weryfikacja", value="Generuje panel z przyciskiem do Captcha na kanale weryfikacyjnym.", inline=False)
    embed.add_field(name="📩 !ticket", value="Wysyła panel otwierania spraw.", inline=False)
    embed.add_field(name="📊 !ankieta", value="Otwiera panel tworzenia ankiet.", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="ankieta")
@commands.has_permissions(administrator=True)
async def ankieta_cmd(ctx):
    await ctx.send(embed=discord.Embed(title="📊 Tworzenie ankiety", description="Kliknij przycisk:"), view=StartPollView())

@bot.command(name="ticket")
async def ticket_cmd(ctx):
    await ctx.send(embed=discord.Embed(title="🎫 System zgłoszeń", description="Kliknij przycisk aby otworzyć ticket:"), view=TicketButton())

if __name__ == "__main__":
    keep_alive() 
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN: bot.run(TOKEN)
