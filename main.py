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


# === FORMULARZ WYSKAKUJĄCY W OKIENKU (MODAL) ===
class TicketModal(discord.ui.Modal, title="🎫 Formularz Zgłoszeniowy"):
    # Pierwsze pole: Temat
    temat = discord.ui.TextInput(
        label="Podaj temat zgłoszenia",
        placeholder="np. Błąd na serwerze / Pytanie...",
        max_length=100,
        required=True,
        style=discord.TextStyle.short
    )
    
    # Drugie pole: Opis
    opis = discord.ui.TextInput(
        label="Opisz krótko swoją sprawę",
        placeholder="Napisz tutaj, w czym możemy Ci pomóc...",
        style=discord.TextStyle.long,
        max_length=1000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        
        channel_name = f"ticket-{member.name}"
        
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"Masz już otwarty jeden ticket! Przejdź do: {existing_channel.mention}", ephemeral=True)
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
        
        # Tworzymy embed powitalny w nowym kanale, pokazujący dane z formularza
        embed = discord.Embed(
            title="🎫 Nowe Zgłoszenie użytkownika",
            description=f"Witaj {member.mention}! Administracja została powiadomiona o Twoim zgłoszeniu. Odpowiemy tak szybko, jak to możliwe.\n\nAby zamknąć to zgłoszenie, kliknij przycisk poniżej.",
            color=discord.Color.green()
        )
        embed.add_field(name="📌 Temat:", value=f"```\n{self.temat.value}\n```", inline=False)
        embed.add_field(name="📝 Opis sprawy:", value=f"```\n{self.opis.value}\n```", inline=False)
        
        await ticket_channel.send(embed=embed, view=CloseTicketButton())
        await interaction.response.send_message(f"Pomyślnie stworzono ticket! Kliknij tutaj: {ticket_channel.mention}", ephemeral=True)


# === PRZYCISK URUCHAMIAJĄCY OKIENKO FORMULARZA ===
class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="Stwórz Ticket ✉️", style=discord.ButtonStyle.primary, custom_id="create_ticket_btn")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Wyświetlamy użytkownikowi wyskakujące okienko z formularzem
        await interaction.response.send_modal(TicketModal())


# === PRZYCISK ZAMYKANIA TICKETU ===
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
        if not new_name.startswith("zamkniety-"):
            new_name = f"zamkniety-{new_name}"
            
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

        ADMIN_IDS = [652507356105539585, 550959315700154368, 590215623259193371]

        # === KOMENDA !pomoc (LISTA KOMEND) ===
        if message.content == "!pomoc":
            if message.author.id not in ADMIN_IDS:
                return

            embed = discord.Embed(
                title="⚙️ Panel Zarządzania Botem",
                description="Ściąga komend do bota żeby nie zapomnieć XD.",
                color=discord.Color.dark_gold()
            )
            
            embed.add_field(
                name="📩 Tickety", 
                value="`!ticket` — dodaje panel ticket na kanał (otwiera formularz zgłoszeniowy w wyskakującym okienku).", 
                inline=False
            )
            embed.add_field(
                name="👤 Rangi ", 
                value="`!rola @osoba @ranga` — Daje rangę.\n`!usunrola @osoba @ranga` — Zabiera rangę.", 
                inline=False
            )
            embed.add_field(
                name="👥 Masowe zarządzanie rangami", 
                value="`!rola-wszyscy @ranga` — Daje rangę każdemu na serwerze.\n`!usunrola-wszyscy @ranga` — Zabiera rangę każdemu na serwerze.", 
                inline=False
            )
            
            embed.set_footer(text="Dostęp do tych komend ma tylko uprawniona administracja czyli @.zbyszek. , @kubus3368 , @steryd2378 .")
            
            await message.channel.send(embed=embed)
            await message.delete()

        # === KOMENDA DO TICKETÓW ===
        if message.content == "!ticket":
            if message.author.id not in ADMIN_IDS:
                return
                
            embed = discord.Embed(
                title="📩 ticket",
                description="Potrzebujesz pomocy administracji? Chcesz zgłosić błąd lub osobę?\n\nKliknij przycisk poniżej, aby wypełnić krótki formularz i otworzyć prywatny kanał z administracją serwera.",
                color=discord.Color.blue()
            )
            await message.channel.send(embed=embed, view=TicketButton())
            await message.delete() 

        # === KOMENDA DO NADAWANIA RANGI JEDNEJ OSOBIE ===
        if message.content.startswith("!rola "):
            if message.author.id not in ADMIN_IDS:
                return

            content_clean = message.content[6:].strip()
            if not message.mentions:
                await message.channel.send("❌ Musisz oznaczyć użytkownika! Przykład: `!rola @Kuba @Ranga`")
                return

            target_user = message.mentions[0]
            guild = message.guild

            role_part = content_clean.replace(target_user.mention, "").strip()
            role_part = role_part.replace(f"<@!{target_user.id}>", "").strip()
            role_part = role_part.replace(f"<@{target_user.id}>", "").strip()

            role = None
            if message.role_mentions:
                role = message.role_mentions[0]
            else:
                role = discord.utils.get(guild.roles, name=role_part)

            if not role:
                await message.channel.send(f"❌ Nie znalazłem rangi: `{role_part if role_part else 'Podaj nazwę'}`")
                return

            if role >= guild.me.top_role:
                await message.channel.send("❌ Ta ranga jest wyżej niż najwyższa rola bota!")
                return

            try:
                await target_user.add_roles(role)
                await message.channel.send(f"✅ Pomyślnie nadano rangę **{role.name}** użytkownikowi {target_user.mention}.")
            except discord.Forbidden:
                await message.channel.send("❌ Brak uprawnień do edycji tego użytkownika.")

        # === KOMENDA DO USUWANIA RANGI JEDNEJ OSOBIE ===
        if message.content.startswith("!usunrola "):
            if message.author.id not in ADMIN_IDS:
                return

            content_clean = message.content[10:].strip()
            if not message.mentions:
                await message.channel.send("❌ Musisz oznaczyć użytkownika! Przykład: `!usunrola @Kuba @Ranga`")
                return

            target_user = message.mentions[0]
            guild = message.guild

            role_part = content_clean.replace(target_user.mention, "").strip()
            role_part = role_part.replace(f"<@!{target_user.id}>", "").strip()
            role_part = role_part.replace(f"<@{target_user.id}>", "").strip()

            role = None
            if message.role_mentions:
                role = message.role_mentions[0]
            else:
                role = discord.utils.get(guild.roles, name=role_part)

            if not role:
                await message.channel.send(f"❌ Nie znalazłem rangi: `{role_part if role_part else 'Podaj nazwę'}`")
                return

            if role >= guild.me.top_role:
                await message.channel.send("❌ Ta ranga jest wyżej niż najwyższa rola bota!")
                return

            try:
                await target_user.remove_roles(role)
                await message.channel.send(f"✅ Pomyślnie odebrano rangę **{role.name}** użytkownikowi {target_user.mention}.")
            except discord.Forbidden:
                await message.channel.send("❌ Brak uprawnień do edycji tego użytkownika.")

        # === KOMENDA DO NADAWANIA RANGI WSZYSTKIM ===
        if message.content.startswith("!rola-wszyscy"):
            if message.author.id not in ADMIN_IDS:
                return

            args = message.content.split(" ", 1)
            if len(args) < 2:
                await message.channel.send("Musisz podać nazwę rangi! Przykład: `!rola-wszyscy @Ranga`")
                return

            role_query = args[1].strip()
            guild = message.guild
            role = None

            if message.role_mentions:
                role = message.role_mentions[0]
            else:
                role = discord.utils.get(guild.roles, name=role_query)

            if not role:
                await message.channel.send(f"❌ Nie znalazłem rangi o nazwie lub oznaczeniu: `{role_query}`")
                return

            if role >= guild.me.top_role:
                await message.channel.send("❌ Ta ranga jest wyżej w ustawieniach Discorda niż najwyższa rola bota! Przesuń bota wyżej.")
                return

            status_message = await message.channel.send(f"⏳ Rozpoczynam dodawanie rangi **{role.name}** wszystkim użytkownikom...")
            all_members = [m for m in guild.members if not m.bot]
            total_members = len(all_members)
            success_count = 0

            for i, member in enumerate(all_members):
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                        success_count += 1
                    except discord.Forbidden:
                        pass
                    except discord.HTTPException:
                        await asyncio.sleep(2)

                if i % 5 == 0 or i == total_members - 1:
                    await status_message.edit(content=f"Postęp: Sprawdzono {i + 1}/{total_members} użytkowników. Dodano rangę dla {success_count} osób...")
                    await asyncio.sleep(0.5)

            await status_message.edit(content=f"✨ Zakończono! Pomyślnie dodano rangę **{role.name}** dla {success_count} użytkowników.")

        # === KOMENDA DO USUWANIA RANGI WSZYSTKIM ===
        if message.content.startswith("!usunrola-wszyscy"):
            if message.author.id not in ADMIN_IDS:
                return

            args = message.content.split(" ", 1)
            if len(args) < 2:
                await message.channel.send("Musisz podać nazwę rangi! Przykład: `!usunrola-wszyscy @Ranga`")
                return

            role_query = args[1].strip()
            guild = message.guild
            role = None

            if message.role_mentions:
                role = message.role_mentions[0]
            else:
                role = discord.utils.get(guild.roles, name=role_query)

            if not role:
                await message.channel.send(f"❌ Nie znalazłem rangi o nazwie lub oznaczeniu: `{role_query}`")
                return

            if role >= guild.me.top_role:
                await message.channel.send("❌ Nie mogę zarządzać tą rangą, ponieważ jest ona wyżej na liście ról niż mój bot!")
                return

            status_message = await message.channel.send(f"⏳ Rozpoczynam usuwanie rangi **{role.name}** wszystkim użytkownikom...")
            all_members = [m for m in guild.members if not m.bot]
            total_members = len(all_members)
            success_count = 0

            for i, member in enumerate(all_members):
                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                        success_count += 1
                    except discord.Forbidden:
                        pass
                    except discord.HTTPException:
                        await asyncio.sleep(2)

                if i % 5 == 0 or i == total_members - 1:
                    await status_message.edit(content=f"Postęp: Sprawdzono {i + 1}/{total_members} użytkowników. Odebrano rangę {success_count} osobom...")
                    await asyncio.sleep(0.5)

            await status_message.edit(content=f"❌ Zakończono! Pomyślnie odebrano rangę **{role.name}** {success_count} użytkownikom.")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
client = MyBot(intents=intents)

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    client.run(TOKEN)
