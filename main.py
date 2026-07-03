import discord
import os
from flask import Flask
from threading import Thread

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

# === KLASA PRZYCISKU DO OTWIERANIA TICKETÓW ===
class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Przycisk działa na stałe, nawet po restarcie bota

    @discord.ui.button(label="Stwórz Ticket ✉️", style=discord.ButtonStyle.primary, custom_id="create_ticket_btn")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        
        # Nazwa nowego kanału ticketu
        channel_name = f"ticket-{member.name}"
        
        # Sprawdzamy, czy taki kanał już przypadkiem nie istnieje
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"Masz już otwarty ticket! Idź do: {existing_channel.mention}", ephemeral=True)
            return

        # Uprawnienia: nikt nie widzi kanału oprócz administracji i osoby otwierającej ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # Jeśli masz specjalną rolę dla adminów (np. "Admin" lub "Moderator"), bot automatycznie da im dostęp
        # Możesz podmienić nazwę roli poniżej, jeśli masz inną na serwerze:
        admin_role = discord.utils.get(guild.roles, name="Admin")
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Tworzenie kanału
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        
        # Wiadomość powitalna w nowym tickecie z przyciskiem do zamykania go
        embed = discord.Embed(
            title="🎫 Nowe Zgłoszenie",
            description=f"Witaj {member.mention}! Opisz tutaj swój problem, a administracja odpowie tak szybko, jak to możliwe.\n\nAby zamknąć to zgłoszenie, kliknij przycisk poniżej.",
            color=discord.Color.green()
        )
        
        await ticket_channel.send(embed=embed, view=CloseTicketButton())
        await interaction.response.send_message(f"Pomyślnie stworzono ticket! Kliknij tutaj: {ticket_channel.mention}", ephemeral=True)

# === KLASA PRZYCISKU DO ZAMYKANIA TICKETÓW ===
class CloseTicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zamknij Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ten kanał zostanie usunięty za 5 sekund...")
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()

# === GŁÓWNA KLASA BOTA ===
class MyBot(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        # Rejestrujemy przyciski, żeby bot pamiętał o nich po restartach hostingu
        self.add_view(TicketButton())
        self.add_view(CloseTicketButton())

    async def on_message(self, message):
        # Ignoruj wiadomości bota
        if message.author == self.user:
            return

        # Komenda do wysłania panelu ticketów (tylko dla osób z uprawnieniami administratora)
        if message.content == "!setup-tickety":
            if not message.author.guild_permissions.administrator:
                await message.channel.send("Nie masz uprawnień administratora, aby to zrobić!")
                return
                
            embed = discord.Embed(
                title="📩 Centrum Zgłoszeń (Tickets)",
                description="Potrzebujesz pomocy administracji? Chcesz zgłosić błąd lub gracza?\n\nKliknij przycisk poniżej, aby otworzyć prywatny kanał dyskusyjny z załogą serwera.",
                color=discord.Color.blue()
            )
            await message.channel.send(embed=embed, view=TicketButton())
            await message.delete() # Usuwa komendę użytkownika, żeby był porządek

intents = discord.Intents.default()
intents.message_content = True
client = MyBot(intents=intents)

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    client.run(TOKEN)
