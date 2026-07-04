import discord
from discord import app_commands, Intents, utils
import os
from flask import Flask
from threading import Thread
import asyncio
from datetime import datetime
from typing import List # Import dla lepszej obsługi typów danych

# ===============================
# 🚨 KONFIGURACJA GLOBALNA 🚨
# ===============================

# Lista ID administratorów. KLUCZOWE: Upewnij się, że są aktualne!
ADMIN_IDS: List[int] = [652507356105539585, 550959315700154368, 590215623259193371]

# --- WEB SERVER SETUP (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "Kubusiowo - BOT żyje i działa!"

def run_web_server():
    """Uruchamia serwer Flask na portu określonym w zmiennych środowiskowych."""
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Utrzymuje serwer Flask działający w tle (dla Render)."""
    t = Thread(target=run_web_server)
    t.daemon = True 
    t.start()

# ===============================
# 📊 SYSTEM ANKIET (Polls)
# ===============================

class PollModal(discord.ui.Modal, title="📊 Tworzenie nowej ankiety"):
    pytanie = discord.ui.TextInput(label="Wpisz pytanie ankiety", placeholder="np. Gramy dzisiaj w turniej?", max_length=256, required=True, style=discord.TextStyle.short)
    opcja_a = discord.ui.TextInput(label="Opcja A", placeholder="np. Tak, jasne! 🔥", max_length=100, required=True, style=discord.TextStyle.short)
    opcja_b = discord.ui.TextInput(label="Opcja B", placeholder="np. Nie, brak czasu ❌", max_length=100, required=True, style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        view = PollVotesView(question=self.pytanie.value, opt_a=self.opcja_a.value, opt_b=self.opcja_b.value)
        await interaction.channel.send(embed=view.build_embed(), view=view)
        await interaction.response.send_message("✅ Ankieta została pomyślnie wygenerowana na kanale!", ephemeral=True)

class PollVotesView(discord.ui.View):
    def __init__(self, question: str, opt_a: str, opt_b: str):
        super().__init__(timeout=None)
        self.question = question
        self.opt_a_text = opt_a
        self.opt_b_text = opt_b
        self.votes_a = set()
        self.votes_b = set()

    def get_progress_bar(self, percentage: float) -> str:
        filled = int(round(percentage / 10))
        filled = max(0, min(10, filled))
        empty = 10 - filled
        return "█" * filled + "░" * empty

    def build_embed(self):
        total_votes = len(self.votes_a) + len(self.votes_b)
        pct_a = (len(self.votes_a) / total_votes * 100) if total_votes > 0 else 0
        pct_b = (len(self.votes_b) / total_votes * 100) if total_votes > 0 else 0
        bar_a = self.get_progress_bar(pct_a)
        bar_b = self.get_progress_bar(pct_b)

        embed = discord.Embed(
            title=f"📊 {self.question}",
            description="Oddaj swój głos klikając w odpowiedni przycisk poniżej!\nMożesz też zmienić zdanie w dowolnym momencie.",
            color=discord.Color.brand_green()
        )
        embed.add_field(name=f"🅰️ {self.opt_a_text}", value=f"`{bar_a}` **{pct_a:.0f}%** ({len(self.votes_a)} głosów)", inline=False)
        embed.add_field(name=f"🅱️ {self.opt_b_text}", value=f"`{bar_b}` **{pct_b:.0f}%** ({len(self.votes_b)} głosów)", inline=False)
        embed.add_field(name="👥 Suma oddanych głosów", value=f"**{total_votes}**", inline=False)
        embed.set_footer(text="Ankieta działa na przyciskach.")
        return embed

    async def update_poll(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Opcja A 🅰️", style=discord.ButtonStyle.primary, custom_id="poll_btn_a")
    async def button_a_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.votes_a:
            self.votes_a.remove(user_id)
        else:
            self.votes_a.add(user_id)
            self.votes_b.discard(user_id)
        await self.update_poll(interaction)

    @discord.ui.button(label="Opcja B 🅱️", style=discord.ButtonStyle.secondary, custom_id="poll_btn_b")
    async def button_b_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.votes_b:
            self.votes_b.remove(user_id)
        else:
            self.votes_b.add(user_id)
            self.votes_a.discard(user_id)
        await self.update_poll(interaction)

class StartPollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Stwórz Nową Ankietę 📊", style=discord.ButtonStyle.success, custom_id="start_poll_btn_persistent")
    async def start_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("❌ Brak uprawnień do tworzenia ankiet.", ephemeral=True)
            return
        await interaction.response.send_modal(PollModal())


# ===============================
# 🎫 SYSTEM TICKETÓW (Tickets)
# ===============================

class TicketModal(discord.ui.Modal, title="🎫 Formularz Zgłoszeniowy"):
    temat = discord.ui.TextInput(label="Podaj temat zgłoszenia", placeholder="np. Błąd na serwerze / Pytanie...", max_length=100, required=True, style=discord.TextStyle.short)
    opis = discord.ui.TextInput(label="Opisz krótko swoją sprawę", placeholder="Napisz tutaj, w czym możemy Ci pomóc...", style=discord.TextStyle.long, max_length=1000, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        channel_name = f"ticket-{member.name}"

        existing_channel = utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"Masz już otwarty jeden ticket! Przejdź do: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        admin_role = utils.get(guild.roles, name="Admin") 
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)

        embed = discord.Embed(
            title="🎫 Nowe Zgłoszenie użytkownika",
            description=f"Witaj {member.mention}! Administracja została powiadomiona o Twoim zgłoszeniu.\n\n👉 **Kliknij przycisk poniżej, aby przejąć to zgłoszenie!**",
            color=discord.Color.green()
        )
        embed.add_field(name="📌 Temat:", value=f"```\n{self.temat.value}\n```", inline=False)
        embed.add_field(name="📝 Opis sprawy:", value=f"```\n{self.opis.value}\n```", inline=False)

        view = TicketControlView(ticket_topic=self.temat.value, ticket_desc=self.opis.value)
        await ticket_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Pomyślnie stworzono ticket! Kliknij tutaj: {ticket_channel.mention}", ephemeral=True)

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Stwórz Ticket ✉️", style=discord.ButtonStyle.primary, custom_id="create_ticket_btn")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())

class TicketControlView(discord.ui.View):
    def __init__(self, ticket_topic="Brak", ticket_desc="Brak"):
        super().__init__(timeout=None)
        self.claimed_by = None
        self.ticket_topic = ticket_topic
        self.ticket_desc = ticket_desc

    @discord.ui.button(label="Zajmij się zgłoszeniem ✋", style=discord.ButtonStyle.success, custom_id="claim_ticket_btn")
    async def claim_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("❌ Tylko administracja może przejąć ten ticket!", ephemeral=True)
            return

        self.claimed_by = interaction.user
        button.disabled = True
        button.label = f"Obsługiwane przez: {interaction.user.name} 🛠️"
        button.style = discord.ButtonStyle.secondary

        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"➡️ {interaction.user.mention} **przejął to zgłoszenie i udzieli pomocy!**")

    @discord.ui.button(label="Zamknij Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_control_btn")
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        feedback_view = FeedbackView(claimed_by=self.claimed_by, closer=interaction.user, ticket_topic=self.ticket_topic, ticket_desc=self.ticket_desc)

        embed = discord.Embed(title="⭐ Oceń pomoc administracji", description="Dziękujemy za skorzystanie z systemu zgłoszeń! Prosimy o wybranie oceny.", color=discord.Color.gold())
        await interaction.channel.send(embed=embed, view=feedback_view)


# ===============================
# ⭐ SYSTEM OCEN (Feedback View)
# ===============================

class FeedbackView(discord.ui.View):
    def __init__(self, claimed_by: discord.Member | None, closer: discord.Member, ticket_topic: str, ticket_desc: str):
        super().__init__(timeout=60.0)
        self.claimed_by = claimed_by
        self.closer = closer
        self.ticket_topic = ticket_topic
        self.ticket_desc = ticket_desc
        self.rating = "Brak oceny"

    async def process_close(self, channel: discord.TextChannel, guild: discord.Guild):
        log_content = f"--- TRANSKRYPCJA TICKETU: {channel.name} ---\n"
        log_content += f"Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_content += f"Obsługujący (Claim): {self.claimed_by.name if self.claimed_by else 'Brak'}\n"
        log_content += f"Zamknięty przez: {self.closer.name}\n"
        log_content += f"Ocena użytkownika: {self.rating}\n"
        log_content += f"Temat zgłoszenia: {self.ticket_topic}\n"
        log_content += f"Opis zgłoszenia: {self.ticket_desc}\n"
        log_content += "-----------------------------------------\n\n"

        # Pętla przechodząca przez historię wiadomości (Logika niezmieniona)
        async for msg in channel.history(limit=None, oldest_first=True):
            time_str = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            log_content += f"[{time_str}] {msg.author.name}: {msg.content}\n"
            if msg.attachments:
                for att in msg.attachments:
                    log_content += f" -> [Załącznik]: {att.url}\n"

        log_content += "\n--- KONIEC TRANSKRYPCJI ---"

        # Tworzenie pliku z logiem
        file_data = log_content.encode('utf-8') 
        log_file = discord.File(file_data, filename=f"log-{channel.name}.txt")
        log_channel = utils.get(guild.text_channels, name="logi-ticketow")

        if log_channel:
            log_embed = discord.Embed(title="🔒 Archiwum Zgłoszenia", description=f"Kanał **{channel.name}** został pomyślnie zamknięty.", color=discord.Color.red(), timestamp=discord.utils.utcnow())
            log_embed.add_field(name="🛠️ Obsługujący admin:", value=self.claimed_by.mention if self.claimed_by else "`Nikt`", inline=True)
            log_embed.add_field(name="🔒 Zamknął:", value=self.closer.mention, inline=True)
            log_embed.add_field(name="⭐ Ocena pracy:", value=f"**{self.rating}**", inline=True)
            log_embed.add_field(name="📌 Wpisany Temat:", value=f"```\n{self.ticket_topic}\n```", inline=False)
            log_embed.add_field(name="📝 Wpisany Opis:", value=f"```\n{self.ticket_desc}\n```", inline=False)

            await log_channel.send(embed=log_embed, file=log_file)

        await channel.send("⚠️ Transkrypcja zapisana. Kanał zostanie usunięty za 5 sekund...")
        await asyncio.sleep(5)
        await channel.delete()

    async def handle_rating(self, interaction: discord.Interaction, stars: str):
        self.rating = stars
        for child in self.children:
            child.disabled = True
        # Edytujemy message, aby wyłączyć przyciski po wybraniu oceny
        await interaction.response.edit_message(view=self) 
        await interaction.channel.send(f"✅ Dziękujemy za ocenę: **{stars}**!")
        self.stop()
        # Proces końcowy, uruchamiany w bloku try/except dla bezpieczeństwa!
        try:
            await self.process_close(interaction.channel, interaction.guild)
        except Exception as e:
             print(f"BŁĄD podczas procesu zamykania ticketu: {e}")


    @discord.ui.button(label="⭐", style=discord.ButtonStyle.primary, custom_id="star_1")
    async def star1(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, "⭐ (1/5)")

    @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.primary, custom_id="star_2")
    async def star2(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, "⭐⭐ (2/5)")

    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.primary, custom_id="star_3")
    async def star3(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, "⭐⭐⭐ (3/5)")

    @discord.ui.button(label="⭐⭐⭐⭐", style=discord.ButtonStyle.primary, custom_id="star_4")
    async def star4(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, "⭐⭐⭐⭐ (4/5)")

    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.primary, custom_id="star_5")
    async def star5(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_rating(interaction, "⭐⭐⭐⭐⭐ (5/5)")


# ===============================
# 🤖 KASKA BOT - GŁÓWNA KLASA
# ===============================

class KubusiowoBot(discord.Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
        # Inicjalizacja Command Tree jest kluczowa dla Slash Commands
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'✅ Logged on as {self.user}!')
        # Synchronizacja globalnych komend (wymagane po restarcie bota!)
        await self.tree.sync() 
        print("✨ Komendy slash zostały zsynchronizowane pomyślnie.")

    async def on_member_join(self, member):
        channel = utils.get(member.guild.text_channels, name="⌊przyloty⌉⌊🌆⌉")
        if channel:
            embed = discord.Embed(title="🌆 Witaj na serwerze!", description=f"{member.mention} właśnie do nas dołączył!\nMiło Cię widzieć!", color=discord.Color.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Teraz mamy {member.guild.member_count} osób.")
            await channel.send(embed=embed)

    async def on_member_remove(self, member):
        channel = utils.get(member.guild.text_channels, name="⌊odloty⌉⌊🌇⌉")
        if channel:
            embed = discord.Embed(title="🌇 Ktoś odleciał...", description=f"**{member.name}** opuścił serwer.", color=discord.Color.red())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Teraz mamy {member.guild.member_count} osób.")
            await channel.send(embed=embed)


# ===============================
# 🚀 DEFINICJA KOMEND SLASH (Slash Commands)
# ===============================

@app_commands.command(name="pomoc", description="📋 Wyświetla listę wszystkich komend administracyjnych i ich użycie.")
@app_commands.checks.has_permissions(administrator=True)
async def pomoc_cmd(interaction: discord.Interaction):
    # Uporządkowane bloki pomocy, aby uniknąć błędów składniowych z znakami specjalnymi
    help_data = [
        ("📩 Tickety", "Wyświetla panel do tworzenia ticketów.", "/ticket"),
        ("📊 Ankiety", "Wyświetla panel do tworzenia ankiet.", "/ankieta"),
        ("👤 Rangi (Nadaj)", "Nadaje rangę użytkownikowi. Użycie: /rola @użytkownik @ranga", "/rola"),
        ("👤 Rangi (Usuń)", "Odbiera rangę użytkownikowi. Użycie: /usunrola @użytkownik @ranga", "/usunrola"),
        ("👥 Masowe rangi", "Nadaje/usuwa rangę masowo. Użycie: /rola-wszyscy @ranga", "/rola-wszyscy"),
        ("🌆 Powitania/Pożegnania", "Testuje kanały powitalne i pożegnalne.", "/test-witamy")
    ]

    fields = []
    for name, desc_text, usage in help_data:
        field_value = f"{desc_text}\n\n**Użycie:** `{usage}`"
        fields.append(discord.ui.Component(name=f"{name}", value=field_value, inline=False))

    embed = discord.Embed(title="⚙️ Panel Zarządzania Botem", description="📋 Przejrzysta lista komend administracyjnych dostępnych na serwerze.", color=discord.Color.dark_gold())
    for field in fields:
        # Tworzenie pól z dynamicznie wygenerowanymi opisami
        embed.add_field(name=field.name, value=field.value, inline=False)

    embed.set_footer(text="Dostępne tylko dla Adminów.")
    await interaction.response.send_message(embed=embed)


@app_commands.command(name="ankieta", description="📊 Otwiera panel do tworzenia nowej ankiety.")
@app_commands.checks.has_permissions(administrator=True)
async def ankieta_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📊 Panel Zarządzania Ankietami", description="Kliknij przycisk poniżej, aby otworzyć formularz i wygenerować nową ankietę.", color=discord.Color.dark_purple())
    await interaction.response.send_message(embed=embed, view=StartPollView())

@app_commands.command(name="ticket", description="📩 Otwiera panel do tworzenia nowego zgłoszenia (Ticket).")
async def ticket_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 System Zgłoszeń Administracji", description="Potrzebujesz pomocy? Kliknij przycisk poniżej, aby wypełnić formularz.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=TicketButton())


# --- KOMENDY ROL (Z Argumentami) ---

@app_commands.command(name="rola", description="⏫ Nadaje określoną rangę użytkownikowi.")
@app_commands.describe(uzytkownik="Oznaczenie użytkownika, któremu nadajemy rangę.", ranga="Nazwa rangi do nadania (lub @ranga).")
async def rola_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, ranga: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień administratora.", ephemeral=True)
        return

    guild = interaction.guild
    role: discord.Role | None = None

    # Lokalizacja roli - priorytet dla oznaczenia, potem nazwa tekstu
    if role_mentions := interaction.role_mentions:
         role = role_mentions[0]
    else:
        try:
             role = utils.get(guild.roles, name=ranga) # Użycie funkcji z biblioteki discord.utils
        except Exception:
            pass 

    if not role or role >= guild.me.top_role:
        await interaction.response.send_message("❌ Ranga nieznaleziona lub wyżej niż rola bota!", ephemeral=True)
        return

    try:
        await uzytkownik.add_roles(role, reason=f"Nadanie przez {interaction.user.name}")
        await interaction.response.send_message(f"✅ Nadano rangę **{role.name}** dla {uzytkownik.mention}.", ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Brak uprawnień do zarządzania rolami!", ephemeral=True)

@app_commands.command(name="usunrola", description="⏬ Odbiera określoną rangę użytkownikowi.")
@app_commands.describe(uzytkownik="Oznaczenie użytkownika, od którego odbieramy rangę.", ranga="Nazwa rangi do odebrania (lub @ranga).")
async def usunrola_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, ranga: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień administratora.", ephemeral=True)
        return

    guild = interaction.guild
    role: discord.Role | None = None

    # Lokalizacja roli (analogicznie jak w rola_cmd)
    if role_mentions := interaction.role_mentions:
         role = role_mentions[0]
    else:
        try:
             role = utils.get(guild.roles, name=ranga)
        except Exception:
            pass

    if not role or role >= guild.me.top_role:
        await interaction.response.send_message("❌ Ranga nieznaleziona lub wyżej niż rola bota!", ephemeral=True)
        return

    try:
        await uzytkownik.remove_roles(role, reason=f"Odebranie przez {interaction.user.name}")
        await interaction.response.send_message(f"✅ Odebrano rangę **{role.name}** użytkownikowi {uzytkownik.mention}.", ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Brak uprawnień do zarządzania rolami!", ephemeral=True)

# --- KOMENDY MASOWE (Z Argumentami) ---
@app_commands.command(name="rola-wszyscy", description="👑 Nadaje rangę wszystkim żyjącym członkom serwera.")
@app_commands.describe(ranga="Nazwa rangi do nadania masowo.")
async def rola_wszyscy_cmd(interaction: discord.Interaction, ranga: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień administratora.", ephemeral=True)
        return

    guild = interaction.guild
    role: discord.Role | None = None
    try:
         role = utils.get(guild.roles, name=ranga)
    except Exception:
        pass

    if not role or role >= guild.me.top_role:
        await interaction.response.send_message("❌ Ranga nieznaleziona lub wyżej niż rola bota!", ephemeral=True)
        return

    # Proces masowego dodawania ról (długa logika pozostaje ta sama, ale używa followup)
    status_message = await interaction.followup.send(f"⏳ Dodawanie rangi **{role.name}** wszystkim...")
    all_members = [m for m in guild.members if not m.bot]
    total_members = len(all_members)
    success_count = 0

    for i, member in enumerate(all_members):
        if role not in member.roles:
            try:
                await member.add_roles(role)
                success_count += 1
            except discord.Forbidden: pass
            except discord.HTTPException: await asyncio.sleep(2)

        if i % 5 == 0 or i == total_members - 1:
            await status_message.edit(content=f"Postęp: {i + 1}/{total_members}... Dodano dla {success_count} osób.")
            await asyncio.sleep(0.5)

    await status_message.edit(content=f"✨ Zakończono! Dodano rangę **{role.name}** dla {success_count} osób.")


@app_commands.command(name="usunrola-wszyscy", description="🗑️ Usuwa określoną rangę wszystkim żyjącym członkom serwera.")
@app_commands.describe(ranga="Nazwa rangi do usunięcia masowo.")
async def usunrola_wszyscy_cmd(interaction: discord.Interaction, ranga: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień administratora.", ephemeral=True)
        return

    guild = interaction.guild
    role: discord.Role | None = None
    try:
         role = utils.get(guild.roles, name=ranga)
    except Exception:
        pass

    if not role or role >= guild.me.top_role:
        await interaction.response.send_message("❌ Ranga nieznaleziona lub wyżej niż rola bota!", ephemeral=True)
        return

    # Proces masowego usuwania ról
    status_message = await interaction.followup.send(f"⏳ Usuwanie rangi **{role.name}** wszystkim...")
    all_members = [m for m in guild.members if not m.bot]
    total_members = len(all_members)
    success_count = 0

    for i, member in enumerate(all_members):
        if role in member.roles:
            try:
                await member.remove_roles(role)
                success_count += 1
            except discord.Forbidden: pass
            except discord.HTTPException: await asyncio.sleep(2)

        if i % 5 == 0 or i == total_members - 1:
            await status_message.edit(content=f"Postęp: {i + 1}/{total_members}... Odebrano od {success_count} osób.")
            await asyncio.sleep(0.5)

    await status_message.edit(content=f"❌ Zakończono! Odebrano rangę **{role.name}** {success_count} użytkownikom.")


@app_commands.command(name="test-witamy", description="🌟 Testuje kanały powitalne i pożegnalne, wysyłając testowe komunikaty.")
async def test_witamy_cmd(interaction: discord.Interaction):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
        return

    ch1 = utils.get(interaction.guild.text_channels, name="⌊przyloty⌉⌊🌆⌉")
    ch2 = utils.get(interaction.guild.text_channels, name="⌊odloty⌉⌊🌇⌉")

    if ch1:
        e1 = discord.Embed(title="🌆 TEST PRZYLOTÓW", description="Test powitalny.", color=discord.Color.green())
        await ch1.send(embed=e1)
    else:
        await interaction.followup.send("⚠️ Nie znaleziono kanału przylotów.")

    if ch2:
        e2 = discord.Embed(title="🌇 TEST ODLOTÓW", description="Test pożegnalny.", color=discord.Color.red())
        await ch2.send(embed=e2)
    else:
        # Wysłanie tylko, jeśli było coś do wysłania w poprzednim komunikacie
        pass 

    await interaction.followup.send("✅ Testy zakończone (sprawdź kanały!).")


# ===============================
# 🚀 STARTUP I HOOKI NA WYDARZENIA
# ===============================

intents = Intents.default()
intents.message_content = True 
intents.members = True          

bot = KubusiowoBot(intents=intents)


if __name__ == "__main__":
    print("--- STARTING KUBUSIOWO BOT ---")
    keep_alive() # Uruchamia serwer webowy w tle
    TOKEN = os.environ.get("DISCORD_TOKEN")

    if TOKEN:
        bot.run(TOKEN)
    else:
        print("\n!!! BŁĄD !!! Proszę ustawić zmienną środowiskową DISCORD_TOKEN.")

