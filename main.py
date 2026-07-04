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
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PWD", "Kuba123!") # Zmień hasło w zmiennych środowiskowych!

# --- WEB SERVER SETUP (Flask) - Dashboard i Uptime ---
app = Flask('')
app.secret_key = os.environ.get("FLASK_SECRET", "super-tajny-klucz-kubusiowo")

# Przechowujemy referencję do bota globalnie, aby Flask miał do niej dostęp
bot_instance = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
</head>
<body class="has-background-light" style="min-height: 100vh;">
    <section class="section">
        <div class="container">
            <div class="box has-text-centered">
                <h1 class="title is-2 text-primary">🤖 Panel Zarządzania - Kubusiowo Bot</h1>
                <p class="subtitle is-6">Zalogowany jako Administrator</p>
                <hr>
                {% if message %}
                    <div class="notification is-success">{{ message }}</div>
                {% endif %}
                
                <div class="columns">
                    <!-- Sekcja Statusu -->
                    <div class="column">
                        <div class="card">
                            <header class="card-header"><p class="card-header-title">⚙️ Ustawienia Bota</p></header>
                            <div class="card-content">
                                <form method="POST" action="/update-status">
                                    <div class="field">
                                        <label class="label">Status bota (Aktywność):</label>
                                        <div class="control">
                                            <input class="input" type="text" name="status_text" placeholder="np. Ogląda serwer..." value="{{ current_status }}">
                                        </div>
                                    </div>
                                    <button type="submit" class="button is-link is-fullwidth">Aktualizuj Status</button>
                                </form>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Sekcja Ogłoszeń -->
                    <div class="column">
                        <div class="card">
                            <header class="card-header"><p class="card-header-title">📢 Wyślij Ogłoszenie</p></header>
                            <div class="card-content">
                                <form method="POST" action="/send-announcement">
                                    <div class="field">
                                        <label class="label">ID Kanału tekstowego:</label>
                                        <div class="control">
                                            <input class="input" type="text" name="channel_id" placeholder="Wklej ID kanału">
                                        </div>
                                    </div>
                                    <div class="field">
                                        <label class="label">Treść wiadomości:</label>
                                        <div class="control">
                                            <textarea class="textarea" name="msg_content" placeholder="Napisz coś od bota..."></textarea>
                                        </div>
                                    </div>
                                    <button type="submit" class="button is-success is-fullwidth">Wyślij Wiadomość</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                
                <hr>
                <a href="/logout" class="button is-danger">Wyloguj się</a>
            </div>
        </div>
    </section>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Logowanie</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
</head>
<body class="has-background-dark style="height: 100vh; display: flex; align-items: center; justify-content: center;">
    <div class="box style="max-width: 400px; margin: 100px auto;">
        <h1 class="title is-4 has-text-centered">🔒 Dashboard Logowanie</h1>
        {% if error %}
            <div class="notification is-danger">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/login">
            <div class="field">
                <label class="label">Hasło administratora:</label>
                <div class="control">
                    <input class="input" type="password" name="password" required>
                </div>
            </div>
            <button type="submit" class="button is-primary is-fullwidth">Zaloguj</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string(LOGIN_TEMPLATE)
    
    current_status = ""
    if bot_instance and bot_instance.activity:
        current_status = bot_instance.activity.name

    return render_template_string(HTML_TEMPLATE, current_status=current_status, message=request.args.get('msg'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == DASHBOARD_PASSWORD:
        session['logged_in'] = True
        return redirect('/')
    return render_template_string(LOGIN_TEMPLATE, error="Nieprawidłowe hasło!")

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
    
    # Logowanie zmiany na serwerze
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
    # Generowanie losowego kodu tekstowego
    text = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    
    # Tworzenie obrazka tła (szerokość 200, wysokość 70, kolor jasno-szary)
    img = Image.new('RGB', (200, 70), color=(230, 230, 230))
    d = ImageDraw.Draw(img)
    
    # Rysowanie losowych linii zakłócających dla bezpieczeństwa
    for _ in range(8):
        x1 = random.randint(0, 200)
        y1 = random.randint(0, 70)
        x2 = random.randint(0, 200)
        y2 = random.randint(0, 70)
        d.line([(x1, y1), (x2, y2)], fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)), width=2)
        
    # Rysowanie tekstu (używamy domyślnego fontu bitmapowego, aby nie wymagać pliku ttf)
    # W razie potrzeby można wgrać plik czcionki za pomocą ImageFont.truetype()
    d.text((50, 25), text, fill=(40, 40, 40))
    
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
                await log_channel.send(f"🟢 Użytkownik {member.mention} (`{member.name}`) pomyślnie przeszedł weryfikację Captcha.")
        else:
            await interaction.response.send_message("❌ Niepoprawny kod! Spróbuj ponownie klikając przycisk.", ephemeral=True)
            if log_channel:
                await log_channel.send(f"🔴 Użytkownik {member.mention} wpisał błędny kod Captcha (Wpisał: `{self.user_input.value}`, Oczekiwano: `{self.correct_code}`).")

class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zweryfikuj się 🔐", style=discord.ButtonStyle.success, custom_id="verify_user_btn")
    async def verify_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Sprawdzamy, czy użytkownik nie jest już zweryfikowany
        if utils.get(interaction.user.roles, name="ZWERYFIKOWANY"):
            await interaction.response.send_message("Jesteś już pomyślnie zweryfikowany!", ephemeral=True)
            return
            
        correct_code, img_buf = generate_captcha()
        file = discord.File(img_buf, filename="captcha.png")
        
        # Wysyłamy obrazek jako wiadomość ukrytą (ephemeral)
        await interaction.response.send_message(
            content="👇 Przepisz poniższy kod w okienku formularza, które pojawi się po kliknięciu drugiego przycisku!", 
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
# 📊 WIDOKI UI DLA TICKETÓW I ANKIET (Bez zmian)
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
        
        # Generowanie transkrypcji z poprawką io.BytesIO
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
# 🤖 BOT KONFIGURACJA SEKCJA GŁÓWNA
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
    bot.add_view(VerificationView()) # <-- Dodajemy widok weryfikacji na przycisk jako stały
    print("✨ Rejestracja widoków powiodła się.")

@bot.event
async def on_ready():
    print(f'🤖 Bot uruchomiony jako: {bot.user}')

@bot.event
async def on_member_join(member):
    # Automatyczne nadawanie roli Member nowemu użytkownikowi
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
        await channel.send(f"🌇 Użytkownik **{member.name}** opuścił nas serwer.")


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
