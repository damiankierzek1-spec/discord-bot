import discord
from discord import app_commands
from discord.ext import commands
import os

# --- KONFIGURACJA ---
# Wstaw tutaj ID użytkowników, którzy mają mieć dostęp do komend
ADMIN_IDS = [652507356105539585, 550959315700154368, 590215623259193371] 

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        # Pamiętaj, aby dodać tutaj swoje View: self.add_view(TicketButton()), self.add_view(StartPollView()) itp.
        await self.tree.sync()
        print("Komendy slash (/) zsynchronizowane!")

bot = MyBot()

# --- FUNKCJA SPRAWDZAJĄCA DOSTĘP ---
def is_admin(interaction: discord.Interaction):
    return interaction.user.id in ADMIN_IDS

# --- KOMENDY SLASH ---

@bot.tree.command(name="ticket", description="Wysyła panel tworzenia ticketów")
@app_commands.check(is_admin)
async def slash_ticket(interaction: discord.Interaction):
    await interaction.response.send_message("Kliknij przycisk poniżej, aby otworzyć ticket:", view=TicketButton(), ephemeral=True)

@bot.tree.command(name="ankieta", description="Wysyła panel tworzenia ankiet")
@app_commands.check(is_admin)
async def slash_ankieta(interaction: discord.Interaction):
    await interaction.response.send_message("Kliknij przycisk poniżej, aby stworzyć ankietę:", view=StartPollView(), ephemeral=True)

@bot.tree.command(name="rola", description="Nadaje rangę użytkownikowi")
@app_commands.check(is_admin)
async def slash_rola(interaction: discord.Interaction, osoba: discord.Member, ranga: discord.Role):
    await osoba.add_roles(ranga)
    await interaction.response.send_message(f"✅ Nadano rangę {ranga.mention} użytkownikowi {osoba.mention}", ephemeral=True)

@bot.tree.command(name="usunrola", description="Odbiera rangę użytkownikowi")
@app_commands.check(is_admin)
async def slash_usunrola(interaction: discord.Interaction, osoba: discord.Member, ranga: discord.Role):
    await osoba.remove_roles(ranga)
    await interaction.response.send_message(f"❌ Odebrano rangę {ranga.mention} użytkownikowi {osoba.mention}", ephemeral=True)

@bot.tree.command(name="rola-wszyscy", description="Nadaje rangę wszystkim użytkownikom")
@app_commands.check(is_admin)
async def slash_rola_wszyscy(interaction: discord.Interaction, ranga: discord.Role):
    await interaction.response.send_message(f"⏳ Nadawanie roli {ranga.name} wszystkim...", ephemeral=True)
    for member in interaction.guild.members:
        if not member.bot: await member.add_roles(ranga)

@bot.tree.command(name="usunrola-wszyscy", description="Odbiera rangę wszystkim użytkownikom")
@app_commands.check(is_admin)
async def slash_usunrola_wszyscy(interaction: discord.Interaction, ranga: discord.Role):
    await interaction.response.send_message(f"⏳ Odbieranie roli {ranga.name} wszystkim...", ephemeral=True)
    for member in interaction.guild.members:
        if not member.bot: await member.remove_roles(ranga)

# --- EVENTY POWITAŃ/POŻEGNAŃ ---
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="⌊przyloty⌉⌊🌆⌉")
    if channel: await channel.send(f"Witaj na serwerze, {member.mention}!")

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name="⌊odloty⌉⌊🌇⌉")
    if channel: await channel.send(f"Żegnaj, {member.name} opuścił nas.")

bot.run(os.environ.get("DISCORD_TOKEN"))
