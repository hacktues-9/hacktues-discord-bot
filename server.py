from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import os 
from dotenv import load_dotenv

load_dotenv()
TOKEN = str(os.getenv('TOKEN'))
GLOBAL_GUILD_ID = int(os.getenv('GUILD_ID'))  # Replace with your global guild id
bot = commands.Bot()

@bot.event
async def on_ready():
    guild = bot.get_guild(GLOBAL_GUILD_ID)

    print(
        f"{bot.user} is connected to the following guild:\n"
        f"{guild.name}(id: {guild.id})\n"
        f"*** Bot is up-and-running ***"
    )

# command will be global if guild_ids is not specified
@bot.slash_command(guild_ids=[GLOBAL_GUILD_ID], description="Ping command")
async def ping(interaction: Interaction):
    await interaction.response.send_message("Pong!")


@bot.slash_command(guild_ids=[GLOBAL_GUILD_ID], description="Choose a number")
async def enter_a_number(
    interaction: Interaction,
    number: int = SlashOption(description="Your number", required=False),
):
    if not number:
        await interaction.response.send_message("No number was specified!", ephemeral=True)
    else:
        await interaction.response.send_message(f"You chose {number}!")

bot.run(TOKEN)
