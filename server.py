from nextcord import Interaction, SlashOption, Intents
from nextcord.ext import commands
import os 
from dotenv import load_dotenv
import psycopg2

load_dotenv()
TOKEN = str(os.getenv('TOKEN'))
GLOBAL_GUILD_ID = int(os.getenv('GUILD_ID'))  # Replace with your global guild id
intents = Intents.default()
intents.members = True
bot = commands.Bot(intents=intents)

host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB_NAME')
port = os.getenv('DB_PORT')

user_discord_select = '''
SELECT 
    first_name, 
    last_name, 
    class_id, 
    grade,
    elsys_email_verified,
    users.id
FROM 
    users 
JOIN info 
    ON info_id = info.id 
JOIN socials 
    ON socials_id = socials.id 
JOIN security
    ON security_id = security.id
JOIN discord 
    ON discord_id = discord.id
WHERE username = %s AND discriminator = %s
'''

classes = ['А','Б','В','Г',]

conn = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    port=port
)

cur = conn.cursor()

roles = {}

@bot.event
async def on_ready():

    guild = bot.get_guild(GLOBAL_GUILD_ID)

    print(
        f"{bot.user} is connected to the following guild:\n"
        f"{guild.name}(id: {guild.id})\n"
        f"*** Bot is up-and-running ***"
    )

    for role in await guild.fetch_roles():
        roles[role.name] = role

@bot.event
async def on_member_join(member):
    print(f"{member} has joined the server")
    username = member.name
    discriminator = member.discriminator
    cur.execute("SELECT * FROM discord WHERE username=%s AND discriminator=%s", (username, discriminator))
    result = cur.fetchone()

    if result is None:
        await member.send("You have not registered your Discord account to related HackTues account. Please do so at https://hacktues.bg/ \n If you have already registered your account, please contact us at https://hacktues.bg/contact-us \n After you have registered your account, please rejoin the server at https://discord.gg/9yAbMUCg \n Thank you for your understanding!")
        await member.kick(reason="Have not registered current Discord user to related HackTues account")
        print(f"{member} has been kicked from the server for not registering their Discord account to related HackTues account")
    else:
        print(f"{member} has been verified")
        cur.execute(user_discord_select, (username, discriminator))
        result = cur.fetchone()
        first_name = result[0]
        last_name = result[1]
        class_value = classes[int(result[2]) - 1]
        grade = result[3]
        elsys_email_verified = result[4]
        user_id = result[5]

        if elsys_email_verified:
            await member.edit(nick = f"{result[0]} {result[1]} {result[3]}({class_value})")
            cur.execute("SELECT * FROM user_technologies WHERE user_id=%s", str(user_id))
            result = cur.fetchall()
            for tech in result:
                technology = str(tech[5])
                cur.execute("SELECT * FROM technologies WHERE id=%s", (technology,))
                result = cur.fetchone()
                await member.add_roles(roles[result[4]])
            await member.send(f"Welcome to HackTues Discord server, {first_name} {last_name}! \n You have been verified and your roles have been assigned. \n If you have any questions, please contact us at https://hacktues.bg/contact-us \n Thank you for your understanding!")

        else:
            await member.send("You have not verified your ELSYS email. Please check your email to verify it. If you have not received the verification email, please contact us at https://hacktues.bg/contact-us \n After you have verified your email, please rejoin the server at https://discord.gg/9yAbMUCg \n Thank you for your understanding!")
            await member.kick(reason="Have not verified ELSYS email")
            print(f"{member} has been kicked from the server for not verifying their ELSYS email")
            

# command will be global if guild_ids is not specified
@bot.slash_command(guild_ids=[GLOBAL_GUILD_ID], description="Ping command")
async def ping(interaction: Interaction):
    await interaction.response.send_message(f"🏓Pong! ({bot.latency*1000}ms)")

@bot.slash_command(guild_ids=[GLOBAL_GUILD_ID], description="Motivate command")
async def motivate(interaction: Interaction):
    await interaction.response.send_message("You can do it!")

@bot.slash_command(guild_ids=[GLOBAL_GUILD_ID], description="Ticket command") # problem, and channel
async def problem(interaction: Interaction, problem: str = SlashOption(description="What is your problem?", required=True)):
    channel = interaction.channel
    roles = interaction.user.roles
    if "team" in channel.name:
        for role in roles:
            if "team" in role.name:

                def check_ticket(r, u):
                    return (str(r) == "🎟️" and u != bot.user)

                await interaction.response.send_message(f"Your problem has been sent to the team leaders! {problem}")
                mentor_role = interaction.guild.get_role(1024417339262910555)
                log = interaction.guild.get_channel(1024415063655862442)
                ticket = await log.send(f"{role.name} has a problem: {problem}! {mentor_role.mention} go in {channel.mention} and help them!")
                while True:
                    await ticket.add_reaction("🎟️")
                    _, mentor_user = await bot.wait_for("reaction_add", check=check_ticket)
                    mentor_user.add_roles(role)
                    await ticket.clear_reaction("🎟️")
                    await ticket.add_reaction("✅")
                    await ticket.add_reaction("❌")
                    await interaction.channel.send(f"{mentor_user.name} is helping {role.mention} with {problem}!")
                    claimed = interaction.guild.get_channel(1024426110265589931)
                    await claimed.send(f"{mentor_user.name} is helping {role.name} with {problem}!")
                    reaction, _ = await bot.wait_for("reaction_add", check=lambda r, u: (str(r) == "✅" or str(r) == "❌") and u == mentor_user)
                    await mentor_user.remove_roles(role)
                    await ticket.clear_reaction("✅")
                    await ticket.clear_reaction("❌")
                    if str(reaction) == "✅":
                        confirmation = await interaction.channel.send(f"{role.mention} your problem has been marked as solved!")
                        await confirmation.add_reaction("✅")
                        await confirmation.add_reaction("❌")
                        reaction, _ = await bot.wait_for("reaction_add", check=lambda r, u: (str(r) == "✅" or str(r) == "❌") and u != bot.user)
                        if str(reaction) == "✅":
                            await ticket.delete() 
                        else:
                            await confirmation.delete()
                            await interaction.channel.send(f"{role.mention} your problem has been reopened!")
                        await confirmation.clear_reaction("✅")
                        await confirmation.clear_reaction("❌")
                        break
                    break 
        else:
            await interaction.response.send_message("You are not in a team!")
    else:
        await interaction.response.send_message("You are not in a team channel!")
    

    
bot.run(TOKEN)
