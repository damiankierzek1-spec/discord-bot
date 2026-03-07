import discord

# =============================
#         INTENTY
# =============================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

# =============================
#     PRZYCISK WERYFIKACJI
# =============================
class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Zweryfikuj się", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name="Zweryfikowany")

        if role is None:
            await interaction.response.send_message("❌ Nie znaleziono roli 'Zweryfikowany'!", ephemeral=True)
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ Otrzymałeś rangę Zweryfikowany!", ephemeral=True)

# =============================
#         BOT READY
# =============================
@client.event
async def on_ready():
    print(f'Zalogowano jako {client.user}')

# =============================
#         WIADOMOŚCI
# =============================
@client.event
async def on_message(message):

    if message.author.bot:
        return

    # PING
    if message.content == "!ping":
        await message.channel.send("🏓 Pong!")

    # =============================
    #          REGULAMIN
    # =============================
    if message.content == "!regulamin":

        text = (
"🐶 ASIOR – 𝙎𝙆𝙔𝙂𝙀𝙉\n\n"
"╔═══════ ✦ 𝐀𝐊𝐓𝐘𝐖𝐍𝐎𝐒́𝐂 ✦ ═══════╗\n"
"➤ Aktywność minimum co 2–3 dni.\n"
"➤ Dłuższa nieobecność musi być zgłoszona.\n"
"➤ Brak aktywności bez informacji = możliwe usunięcie.\n"
"➤ Każdy rozwija generator i wspiera klan.\n"
"╚════════════════════════════╝\n\n"
"╔═══════ ✦ 𝐙𝐀𝐂𝐇𝐎𝐖𝐀𝐍𝐈𝐄 ✦ ═══════╗\n"
"➤ Kultura i szacunek wobec wszystkich.\n"
"➤ Zakaz wyzywania, prowokacji i dram.\n"
"➤ Zakaz wynoszenia informacji o klanie.\n"
"➤ Reprezentujemy klan z klasą.\n"
"╚════════════════════════════╝\n\n"
"╔════════ ✦ 𝐊𝐀𝐑𝐘 ✦ ════════╗\n"
"➤ ① Ostrzeżenie\n"
"➤ ② Degradacja\n"
"➤ ③ Wyrzucenie z klanu\n"
"➤ Poważne przewinienia = natychmiastowe usunięcie.\n"
"╚════════════════════════════╝"
        )

        embed = discord.Embed(
            title="📜 Regulamin – Zasady Gita",
            description=text,
            color=discord.Color.gold()
        )

        embed.set_footer(text="Kanał: #regulamin • Przestrzeganie zasad jest obowiązkowe")

        await message.channel.send(embed=embed, view=VerifyButton())

    # =============================
    #         CLEAR
    # =============================
    if message.content.startswith("!clear"):
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("❌ Nie masz uprawnień!")
            return
        try:
            amount = int(message.content.split()[1])
            await message.channel.purge(limit=amount + 1)
        except:
            await message.channel.send("❗ Użycie: !clear <ilość>")

    # =============================
    #         KICK
    # =============================
    if message.content.startswith("!kick"):
        if message.author.guild_permissions.kick_members and message.mentions:
            user = message.mentions[0]
            await user.kick(reason="Kick admina")
            await message.channel.send(f"👢 {user} został wyrzucony")

    # =============================
    #         BAN
    # =============================
    if message.content.startswith("!ban"):
        if message.author.guild_permissions.ban_members and message.mentions:
            user = message.mentions[0]
            await user.ban(reason="Ban admina")
            await message.channel.send(f"🔨 {user} został zbanowany")

    # =============================
    #         SAY
    # =============================
    if message.content.startswith("!say"):
        if message.author.guild_permissions.administrator:
            text = message.content[5:]
            if text:
                embed = discord.Embed(description=text, color=discord.Color.orange())
                await message.channel.send(embed=embed)
                await message.delete()

    # =============================
    #         TICKET JOKE
    # =============================
    if "ticket" in message.content.lower():
        await message.channel.send("Czy ja usłyszałem ticket czy ktoś chce się na kogoś rozjebać?!")

    # =============================
    #         FOTO
    # =============================
    if message.content == "!foto":
        try:
            await message.channel.send(file=discord.File("chatgpt.png"))
        except FileNotFoundError:
            await message.channel.send("❌ Nie znalazłem pliku chatgpt.png na dysku!")

# =============================
#       URUCHOMIENIE BOTA
# =============================
client.run("MTQ3OTg3ODA5MzA0Mzc5ODA4OA.GF9S4w.AdIPiXzGe1Cr2quTO0RceNQX8ideg9Stmbvmv8")