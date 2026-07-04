import discord
import os
from flask import Flask
from threading import Thread
import asyncio
from io import BytesIO
from datetime import datetime
from discord import app_commands

app = Flask('')
@app.route('/')
def home():
    return "Kubusiowo - BOT żyje i działa!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# ---------------------
# ANKIETY (bez zmian)
# ---------------------
class PollModal(discord.ui.Modal, title="📊 Tworzenie nowej ankiety"):
    pytanie = discord.ui.TextInput(label="Wpisz pytanie ankiety", placeholder="np. Gramy dzisiaj w turniej?", max_length=256, required=True, style=discord.TextStyle.short)
    opcja_a = discord.ui.TextInput(label="Opcja A", placeholder="np. Tak, jasne! 🔥", max_length=100, required=True, style=discord.TextStyle.short)
    opcja_b = discord.ui.TextInput(label="Opcja B", placeholder="np. Nie, brak czasu ❌", max_length=100, required=True, style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        view = PollVotesView(question=self.pytanie.value, opt_a=self.opcja_a.value, opt_b=self.opcja_b.value)
        await interaction.channel.send(embed=view.build_embed(), view=view)
        await interaction.response.send_message("✅ Ankieta została pomyślnie wygenerowana na kanale!", ephemeral=True)

# ... (cała reszta klas ankiet, ticketów i widoków bez zmian - zostawiłem je tak jak były)

class StartPollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Stwórz Nową Ankietę 📊", style=discord.ButtonStyle.success, custom_id="start_poll_btn_persistent")
    async def start_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        ADMIN_IDS = [652507356105539585, 550959315700154368, 590215623259193371]
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("❌ Brak uprawnień do tworzenia ankiet.", ephemeral=True)
            return
        await interaction.response.send_modal(PollModal())

# ---------------------
# TICKET SYSTEM (bez zmian)
# ---------------------
# (wszystkie klasy TicketModal, TicketButton itd. zostają dokładnie tak samo)

# ---------------------
# BOT
# ---------------------
class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Rejestracja persistent views
        self.add_view(TicketButton())
        self.add_view(TicketControlView())
        self.add_view(StartPollView())

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash command(s)")
        except Exception as e:
            print(f"Sync error: {e}")

    # ==================== SLASH COMMANDS ====================

    @app_commands.command(name="pomoc", description="Pokazuje panel pomocy administracyjnej")
    async def pomoc(self, interaction: discord.Interaction):
        ADMIN_IDS = [652507356105539585, 550959315700154368, 590215623259193371]
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("❌ Brak uprawnień.", ephemeral=True)
            return

        embed = discord.Embed(title="⚙️ Panel Zarządzania Botem", description="Przejrzysta lista komend administracyjnych.", color=discord.Color.dark_gold())
        embed.add_field(name="📩 Tickety", value="`/ticket` — wysyła panel ticketów", inline=False)
        embed.add_field(name="📊 Ankiety", value="`/ankieta` — wysyła panel ankiet", inline=False)
        embed.add_field(name="👤 Rangi", value="`/rola @osoba @ranga`\n`/usunrola @osoba @ranga`", inline=False)
        embed.add_field(name="👥 Masowe rangi", value="`/rola-wszyscy @ranga`\n`/usunrola-wszyscy @ranga`", inline=False)
        embed.set_footer(text="Dostęp tylko dla administracji")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ankieta", description="Wysyła panel do tworzenia ankiet")
    async def ankieta(self, interaction: discord.Interaction):
        ADMIN_IDS = [652507356105539585, 550959315700154368, 590215623259193371]
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("❌ Brak uprawnień.", ephemeral=True)
            return
        embed = discord.Embed(title="📊 Panel Zarządzania Ankietami", description="Kliknij przycisk poniżej, aby utworzyć ankietę.", color=discord.Color.dark_purple())
        await interaction.response.send_message(embed=embed, view=StartPollView())

    @app_commands.command(name="ticket", description="Wysyła panel do tworzenia ticketów")
    async def ticket(self, interaction: discord.Interaction):
        ADMIN_IDS = [652507356105539585, 550959315700154368, 590215623259193371]
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("❌ Brak uprawnień.", ephemeral=True)
            return
        embed = discord.Embed(title="📩 System Ticketów", description="Potrzebujesz pomocy? Kliknij przycisk poniżej.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=TicketButton())

    # Możesz dodać więcej slash commands później...

    # Pozostałe metody (on_member_join, on_member_remove) bez zmian
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name="⌊przyloty⌉⌊🌆⌉")
        if channel:
            embed = discord.Embed(title="🌆 Witaj na serwerze!", description=f"{member.mention} właśnie do nas dołączył!\nMiło Cię widzieć!", color=discord.Color.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Teraz mamy {member.guild.member_count} osób.")
            await channel.send(embed=embed)

    async def on_member_remove(self, member):
        channel = discord.utils.get(member.guild.text_channels, name="⌊odloty⌉⌊🌇⌉")
        if channel:
            embed = discord.Embed(title="🌇 Ktoś odleciał...", description=f"**{member.name}** opuścił serwer.", color=discord.Color.red())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Teraz mamy {member.guild.member_count} osób.")
            await channel.send(embed=embed)

# --- START BOTA ---
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    client = MyBot()
    client.run(TOKEN)
