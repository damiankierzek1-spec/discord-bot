import discord
import os
import asyncio
from flask import Flask
from threading import Thread

# =============================
#         FLASK 24/7
# =============================

app = Flask("")

@app.route("/")
def home():
    return "Bot działa 24/7"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =============================
#         INTENTY
# =============================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

# =============================
#       WERYFIKACJA
# =============================

class VerifyButton(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ Zweryfikuj się",
        style=discord.ButtonStyle.green,
        custom_id="verify_button"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name="Zweryfikowany")

        if role is None:
            await interaction.response.send_message(
                "❌ Nie znaleziono roli Zweryfikowany", ephemeral=True)
            return

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            "✅ Otrzymałeś rangę!", ephemeral=True)

# =============================
#       ZAMYKANIE TICKETA
# =============================

class CloseTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Zamknij ticket",
        style=discord.ButtonStyle.red,
        custom_id="close_ticket"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        channel = interaction.channel
        guild = interaction.guild

        queen_role = discord.utils.get(guild.roles, name="Królowa")
        los_role = discord.utils.get(guild.roles, name="Człowiek Łoś")

        await channel.set_permissions(guild.default_role, read_messages=False)

        if queen_role:
            await channel.set_permissions(queen_role, read_messages=True)

        if los_role:
            await channel.set_permissions(los_role, read_messages=True)

        embed = discord.Embed(
            title="🔒 Ticket zamknięty",
            description="Ticket został zamknięty.\nDostęp ma tylko administracja.",
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed)

# =============================
#       OTWIERANIE TICKETA
# =============================

class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎫 Otwórz ticket",
        style=discord.ButtonStyle.green,
        custom_id="open_ticket"
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        # sprawdzenie czy ticket już istnieje
        for channel in guild.text_channels:
            if channel.name == f"ticket-{user.name}":
                await interaction.response.send_message(
                    f"❌ Masz już otwarty ticket: {channel.mention}",
                    ephemeral=True
                )
                return

        category = discord.utils.get(guild.categories, name="TICKETY")

        if category is None:
            category = await guild.create_category("TICKETY")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        queen_role = discord.utils.get(guild.roles, name="Królowa")
        los_role = discord.utils.get(guild.roles, name="Człowiek Łoś")

        embed = discord.Embed(
            title="🎫 Nowy Ticket",
            description=f"{user.mention} opisz swój problem.\nAdministracja wkrótce pomoże.",
            color=discord.Color.green()
        )

        embed.set_footer(text="Kliknij przycisk poniżej aby zamknąć ticket.")

        await channel.send(
            f"{queen_role.mention if queen_role else ''} {los_role.mention if los_role else ''}",
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"Ticket utworzony: {channel.mention}",
            ephemeral=True
        )

# =============================
#        BOT READY
# =============================

@client.event
async def on_ready():
    print(f"Zalogowano jako {client.user}")
    client.add_view(VerifyButton())
    client.add_view(TicketView())
    client.add_view(CloseTicketView())

# =============================
#        KOMENDY
# =============================

@client.event
async def on_message(message):

    if message.author.bot:
        return

    if message.content == "!ping":
        await message.channel.send("🏓 Pong!")

    if message.content == "!regulamin":

        embed = discord.Embed(
            title="📜 Regulamin",
            description="Kliknij przycisk aby się zweryfikować.",
            color=discord.Color.gold()
        )

        await message.channel.send(embed=embed, view=VerifyButton())

    if message.content == "!tickety":

        embed = discord.Embed(
            title="🎫 Ticket",
            description="Kliknij przycisk aby otworzyć ticket.",
            color=discord.Color.green()
        )

        embed.set_footer(text="Administracja odpowie najszybciej jak to możliwe.")

        await message.channel.send(embed=embed, view=TicketView())

# =============================
#       START BOTA
# =============================

keep_alive()

TOKEN = os.getenv("TOKEN")

client.run(TOKEN)
