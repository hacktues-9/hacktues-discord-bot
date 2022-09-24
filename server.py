from nextcord import Interaction, SlashOption
from nextcord.ext import commands
import os 

TOKEN = str(os.getenv('TOKEN'))
GLOBAL_GUILD_ID = 995681969478312066  # Replace with your global guild id
bot = commands.Bot()


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
