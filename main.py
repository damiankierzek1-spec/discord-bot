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


class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="Stwórz Ticket ✉️", style=discord.ButtonStyle.primary, custom_id="create_ticket_btn")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        
        channel_name = f"ticket-{member.name}"
        
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"Ticket został utworzony! Przejdź do: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        admin_role = discord.utils.get(guild.roles, name="Admin")
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        
        embed = discord.Embed(
            title="🎫 Nowe Zgłoszenie",
            description=f"Witaj {member.mention}! Opisz tutaj swój problem, a administracja odpowie tak szybko, jak to możliwe.\n\nAby zamknąć to zgłoszenie, kliknij przycisk poniżej.",
            color=discord.Color.green()
        )
        
        await ticket_channel.send(embed=embed, view=CloseTicketButton())
        await interaction.response.send_message(f"Pomyślnie stworzono ticket! Kliknij tutaj: {ticket_channel.mention}", ephemeral=True)


class CloseTicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zamknij Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = interaction.channel
        
        TWOJE_ID_DISCORD = 652507356105539585 
        
        await interaction.response.send_message("Archiwizowanie i zamykanie ticketu...", ephemeral=False)
        
        owner = guild.get_member(TWOJE_ID_DISCORD)
        
        new_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        if owner:
            new_overwrites[owner] = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)
            
        await channel.edit(overwrites=new_overwrites)
        
        new_name = channel.name.replace("ticket-", "zamkniety-")
        await channel.edit(name=new_name)
        
        closed_embed = discord.Embed(
            title="🔒 Ticket Zamknięty",
            description=f"Ten ticket został zamknięty przez {interaction.user.mention} i przeniesiony do Twojego archiwum. Tylko Ty go teraz widzisz.",
            color=discord.Color.red()
        )
        await channel.send(embed=closed_embed)


class MyBot(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.add_view(TicketButton())
        self.add_view(CloseTicketButton())

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content == "!ticket":
            TWOJE_ID_DISCORD = 652507356105539585 
            
            if message.author.id != TWOJE_ID_DISCORD:
                return
                
            embed = discord.Embed(
                title="📩 ticket",
                description="Potrzebujesz pomocy administracji? Chcesz zgłosić błąd lub osobe?\n\nKliknij przycisk poniżej, aby otworzyć prywatny kanał z adminsitracją serwera.",
                color=discord.Color.blue()
            )
            await message.channel.send(embed=embed, view=TicketButton())
            await message.delete() 

intents = discord.Intents.default()
intents.message_content = True
client = MyBot(intents=intents)

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    client.run(TOKEN)
