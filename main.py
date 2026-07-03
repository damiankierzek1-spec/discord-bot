import discord
import os
from flask import Flask
from threading import Thread
import asyncio

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

        TWOJE_ID_DISCORD = 652507356105539585 

        # === KOMENDA DO TICKETÓW ===
        if message.content == "!ticket":
            if message.author.id != TWOJE_ID_DISCORD:
                return
                
            embed = discord.Embed(
                title="📩 ticket",
                description="Potrzebujesz pomocy administracji? Chcesz zgłosić błąd lub osobe?\n\nKliknij przycisk poniżej, aby otworzyć prywatny kanał z adminsitracją serwera.",
                color=discord.Color.blue()
            )
            await message.channel.send(embed=embed, view=TicketButton())
            await message.delete() 

        # === KOMENDA DO NADAWANIA RANGI WSZYSTKIM ===
        if message.content.startswith("!rola-wszyscy"):
            if message.author.id != TWOJE_ID_DISCORD:
                return

            # Pobieramy nazwę roli lub wzmiankę z wiadomości
            args = message.content.split(" ", 1)
            if len(args) < 2:
                await message.channel.send("Musisz podać nazwę rangi lub ją oznaczyć! Przykład: `!rola-wszyscy @Gracz`")
                return

            role_query = args[1].strip()
            guild = message.guild
            role = None

            # Sprawdzamy czy rola została oznaczona, czy wpisana tekstowo
            if message.role_mentions:
                role = message.role_mentions[0]
            else:
                role = discord.utils.get(guild.roles, name=role_query)

            if not role:
                await message.channel.send(f"Nie znalazłem rangi o nazwie: `{role_query}`")
                return

            # Sprawdzamy czy bot ma wystarczająco wysokie uprawnienia do nadania tej roli
            if role >= guild.me.top_role:
                await message.channel.send("Ta ranga jest wyżej niż najwyższa rola bota! Przesuń rolę bota wyżej w ustawieniach serwera.")
                return

            status_message = await message.channel.send("Rozpoczynam nadawanie rangi wszystkim użytkownikom. Pobieram listę osób...")
            
            # Pobieramy wszystkich członków serwera (wymaga włączonego Server Members Intent)
            all_members = [m for m in guild.members if not m.bot]
            total_members = len(all_members)
            success_count = 0

            for i, member in enumerate(all_members):
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                        success_count += 1
                    except discord.Forbidden:
                        pass # Brak uprawnień do edycji tego konkretnego użytkownika (np. właściciel)
                    except discord.HTTPException:
                        await asyncio.sleep(2) # Jeśli Discord nas blokuje, czekamy chwilę

                # Aktualizujemy status na czacie co 5 osób, żeby nie spamować API
                if i % 5 == 0 or i == total_members - 1:
                    await status_message.edit(content=f"Postęp: Sprawdzono {i + 1}/{total_members} użytkowników. Nadano rangę dla {success_count} osób...")
                    await asyncio.sleep(0.5)

            await status_message.edit(content=f"✨ Zakończono! Pomyślnie dodano rangę **{role.name}** dla {success_count} użytkowników.")


# Włączamy pobieranie członków serwera w konfiguracji bota
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Ta linijka pozwala botowi widzieć listę użytkowników
client = MyBot(intents=intents)

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    client.run(TOKEN)
