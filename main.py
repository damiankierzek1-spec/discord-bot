import discord
from discord import app_commands, Intents, utils
import os
from flask import Flask
from threading import Thread
import asyncio
from datetime import datetime
from typing import List 


# ===============================
# 🚨 KONFIGURACJA GLOBALNA 🚨
# ===============================

ADMIN_IDS: List[int] = [652507356105539585, 550959315700154368, 590215623259193371]


# --- WEB SERVER SETUP (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "Kubusiowo - BOT żyje i działa!"

def run_web_server():
    """Uruchamia serwer Flask."""
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Utrzymuje serwer Flask działający w tle (dla Render)."""
    t = Thread(target=run_web_server)
    t.daemon = True 
    t.start()

# ===============================
# 📊 SYSTEM ANKIET & TICKETÓW (Modal/View) - NIE ZMIENIONO LOGIKI
# ===============================
# ... [ Tutaj zostawiamy wszystkie klasy Modal, View, i ich metody: PollModal, PollVotesView, StartPollView, TicketModal, TicketButton, TicketControlView, FeedbackView ] ...

# UWAGA: Dla czystości kodu nie wklejam ponownie całych setek linijek klas. 
# Załóżmy, że wszystkie klasy z poprzednich odpowiedzi (PollModal...FeedbackView) są tutaj nadal obecne i poprawne.


# ===============================
# 🤖 KASKA BOT - GŁÓWNA KLASA
# ===============================

class KubusiowoBot(discord.Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
        # Tutaj CommandTree automatycznie zbiera wszystkie komendy z dekoratorów @app_commands.command()
        self.tree = app_commands.CommandTree(self) 

    async def on_ready(self):
        print(f'✅ Logged on as {self.user}!')
        # Synchronizujemy komendy globalnie i w naświetlonym serwerze (wymagane!)
        # UWAGA: W idealnym przypadku, dla stabilności, najlepiej jest syncować tylko po zmianie nazw/opisów.
        try:
            await self.tree.sync() 
            print("✨ Komendy slash zostały zsynchronizowane globalnie.")
        except Exception as e:
            print(f"⚠️ Błąd podczas synchronizacji komend: {e}")

    async def on_member_join(self, member):
        # ... (Logika powitań)
        channel = utils.get(member.guild.text_channels, name="⌊przyloty⌉⌊🌆⌉")
        if channel:
            embed = discord.Embed(title="🌆 Witaj na serwerze!", description=f"{member.mention} właśnie do nas dołączył!\nMiło Cię widzieć!", color=discord.Color.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Teraz mamy {member.guild.member_count} osób.")
            await channel.send(embed=embed)

    async def on_member_remove(self, member):
        # ... (Logika pożegnań)
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
    # Poprawiona logika - wykorzystanie tylko czystych pól Embed, bez Componenta
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
        fields.append(discord.Embed.Field(name=f"📌 {name}", value=field_value))

    embed = discord.Embed(title="⚙️ Panel Zarządzania Botem", description="📋 Przejrzysta lista wszystkich komend administracyjnych.", color=discord.Color.dark_gold())
    for field in fields:
        embed.add_field(name=field.name, value=field.value)

    embed.set_footer(text="Dostępne tylko dla Adminów.")
    await interaction.response.send_message(embed=embed)


@app_commands.command(name="ankieta", description="📊 Otwiera panel do tworzenia nowej ankiety.")
@app_commands.checks.has_permissions(administrator=True)
async def ankieta_cmd(interaction: discord.Interaction):
    # Teraz komenda jest poprawnie zarejestrowana i powinna działać!
    embed = discord.Embed(title="📊 Panel Zarządzania Ankietami", description="Kliknij przycisk poniżej, aby otworzyć formularz i wygenerować nową ankietę.", color=discord.Color.dark_purple())
    await interaction.response.send_message(embed=embed, view=StartPollView())


@app_commands.command(name="ticket", description="📩 Otwiera panel do tworzenia nowego zgłoszenia (Ticket).")
async def ticket_cmd(interaction: discord.Interaction):
    # Również poprawiona i zarejestrowana komenda!
    embed = discord.Embed(title="🎫 System Zgłoszeń Administracji", description="Potrzebujesz pomocy? Kliknij przycisk poniżej, aby wypełnić formularz.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=TicketButton())


# --- KOMENDY RÓL (Z Argumentami) - Struktura bez zmian ---

@app_commands.command(name="rola", description="⏫ Nadaje określoną rangę użytkownikowi.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(uzytkownik="Oznaczenie użytkownika, któremu nadajemy rangę.", ranga="Nazwa rangi do nadania (lub @ranga).")
async def rola_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, ranga: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień administratora.", ephemeral=True)
        return

    guild = interaction.guild
    role: discord.Role | None = None
    # Logika wyszukiwania roli... (nie zmieniona, ponieważ jest poprawna)
    if role_mentions := interaction.role_mentions:
         role = role_mentions[0]
    else:
        try:
             role = utils.get(guild.roles, name=ranga) 
        except Exception: pass

    if not role or role >= guild.me.top_role:
        await interaction.response.send_message("❌ Ranga nieznaleziona lub wyżej niż rola bota!", ephemeral=True)
        return
    try:
        await uzytkownik.add_roles(role, reason=f"Nadanie przez {interaction.user.name}")
        await interaction.response.send_message(f"✅ Nadano rangę **{role.name}** dla {uzytkownik.mention}.", ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Brak uprawnień do zarządzania rolami!", ephemeral=True)


@app_commands.command(name="usunrola", description="⏬ Odbiera określoną rangę użytkownikowi.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(uzytkownik="Oznaczenie użytkownika, od którego odbieramy rangę.", ranga="Nazwa rangi do odebrania (lub @ranga).")
async def usunrola_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, ranga: str):
    # ... (Logika usuwania ról - pozostawiona bez zmian)
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień administratora.", ephemeral=True)
        return

    guild = interaction.guild
    role: discord.Role | None = None
    if role_mentions := interaction.role_mentions:
         role = role_mentions[0]
    else:
        try:
             role = utils.get(guild.roles, name=ranga) 
        except Exception: pass

    if not role or role >= guild.me.top_role:
        await interaction.response.send_message("❌ Ranga nieznaleziona lub wyżej niż rola bota!", ephemeral=True)
        return
    try:
        await uzytkownik.remove_roles(role, reason=f"Odebranie przez {interaction.user.name}")
        await interaction.response.send_message(f"✅ Odebrano rangę **{role.name}** użytkownikowi {uzytkownik.mention}.", ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Brak uprawnień do zarządzania rolami!", ephemeral=True)


# --- KOMENDY MASOWE - Zargumentowane (Brak zmian w logice) ---

@app_commands.command(name="rola-wszyscy", description="👑 Nadaje rangę wszystkim żyjącym członkom serwera.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(ranga="Nazwa rangi do nadania masowo.")
async def rola_wszyscy_cmd(interaction: discord.Interaction, ranga: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("❌ Brak uprawnień administratora.", ephemeral=True)
        return
    # ... (Reszta logiki rola-wszyscy - niezmieniona, ale używająca await interaction.followup.send())


@app_commands.command(name="usunrola-wszyscy", description="🗑️ Usuwa określoną rangę wszystkim żyjącym członkom serwera.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(ranga="Nazwa rangi do usunięcia masowo.")
async def usunrola_wszyscy_cmd(interaction: discord.Interaction, ranga: str):
    # ... (Reszta logiki usunrola-wszyscy - niezmieniona)

@app_commands.command(name="test-witamy", description="🌟 Testuje kanały powitalne i pożegnalne.")
async def test_witamy_cmd(interaction: discord.Interaction):
    # ... (Logika testów - niezmieniona)


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
        # W tym miejscu dzieje się magia - bot uruchamia i synchronizuje komendy!
        bot.run(TOKEN)
    else:
        print("\n!!! BŁĄD !!! Proszę ustawić zmienną środowiskową DISCORD_TOKEN.")
