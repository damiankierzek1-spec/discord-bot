from flask import Flask
from threading import Thread
import os
import discord

# =============================
#         FLASK KEEP ALIVE
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
#     PRZYCISK WERYFIKACJI
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
                "❌ Nie znaleziono roli 'Zweryfikowany'!", ephemeral=True
            )
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            "✅ Otrzymałeś rangę Zweryfikowany!", ephemeral=True
        )


# =============================
#         BOT READY
# =============================
@client.event
async def on_ready():
    print(f"Zalogowano jako {client.user}")
    client.add_view(VerifyButton())


# =============================
#         WIADOMOŚCI
# =============================
@client.event
async def on_message(message):

    if message.author.bot:
        return

    if message.content == "!ping":
        await message.channel.send("🏓 Pong!")

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
            color=discord.Color.gold(),
        )

        embed.set_footer(
            text="Kanał: #regulamin • Przestrzeganie zasad jest obowiązkowe"
        )

        await message.channel.send(embed=embed, view=VerifyButton())

    if message.content.startswith("!clear"):
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("❌ Nie masz uprawnień!")
            return
        try:
            amount = int(message.content.split()[1])
            await message.channel.purge(limit=amount + 1)
        except:
            await message.channel.send("❗ Użycie: !clear <ilość>")

    if message.content.startswith("!kick"):
        if message.author.guild_permissions.kick_members and message.mentions:
            user = message.mentions[0]
            await user.kick(reason="Kick admina")
            await message.channel.send(f"👢 {user} został wyrzucony")

    if message.content.startswith("!ban"):
        if message.author.guild_permissions.ban_members and message.mentions:
            user = message.mentions[0]
            await user.ban(reason="Ban admina")
            await message.channel.send(f"🔨 {user} został zbanowany")

    if message.content.startswith("!say"):
        if message.author.guild_permissions.administrator:
            text = message.content[5:]
            if text:
                embed = discord.Embed(description=text, color=discord.Color.orange())
                await message.channel.send(embed=embed)
                await message.delete()

    if "ticket" in message.content.lower():
        await message.channel.send(
            "Czy ja usłyszałem ticket czy ktoś chce się na kogoś rozjebać?!"
        )


# =============================
#       URUCHOMIENIE BOTA
# =============================
keep_alive()

TOKEN = os.getenv("TOKEN")
client.run(TOKEN)
