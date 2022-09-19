from nextcord import Interaction, SlashOption
from nextcord.ext import commands

TESTING_GUILD_ID = 995682058049425438  # Replace with your testing guild id
GLOBAL_GUILD_ID = 995681969478312066  # Replace with your global guild id
bot = commands.Bot()


# command will be global if guild_ids is not specified
@bot.slash_command(guild_ids=[GLOBAL_GUILD_ID], description="Ping command")
async def ping(interaction: Interaction):
    await interaction.response.send_message("Pong!")

# stop everyone except IT Gods from using this command


@bot.slash_command(guild_ids=[TESTING_GUILD_ID], description="Test command")
async def test(interaction: Interaction, user: SlashOption(str, description="User to test")):
    if interaction.author.id not in [123456789, 987654321]:
        await interaction.response.send_message("You are not allowed to use this command!", ephemeral=True)
        return
    await interaction.response.send_message(f"Testing {user}...")


@bot.slash_command(guild_ids=[GLOBAL_GUILD_ID], description="Choose a number")
async def enter_a_number(
    interaction: Interaction,
    number: int = SlashOption(description="Your number", required=False),
):
    if not number:
        await interaction.response.send_message("No number was specified!", ephemeral=True)
    else:
        await interaction.response.send_message(f"You chose {number}!")

bot.run("MTAwOTU0NzYyMzYzNzcxMjk3Nw.GV4Syx.8kkk8zemsg4VXJ-zV2bxDHoHjxbFtzvQgTewEg")
