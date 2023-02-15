from nextcord import Interaction, SlashOption, Intents, AudioSource, FFmpegOpusAudio, VoiceClient
from nextcord.ext import commands, application_checks
import os
import sys
import time
import asyncio
import re
from dotenv import load_dotenv
import psycopg2
from typing import Dict, List
import atexit
import requests
import urllib.parse
import urllib.request
import yt_dlp
sys.path.append('./commands')
sys.path.append('./utils')
from ht_global import classes, GUILD_IDS, TOKEN
import ht_db
import ht_func

load_dotenv()
intents = Intents.default()
intents.members = True
bot = commands.Bot(intents=intents)
roles = {}

user_discord_select = '''
SELECT 
    concat(u.first_name, ' ', u.last_name) as name,
    i.class_id, 
    i.grade,
    sec.elsys_email_verified,
    u.id, 
    u.role_id,
    u.team_id
FROM 
    users u
JOIN info i ON u.info_id = i.id 
JOIN socials s ON i.socials_id = s.id 
JOIN security sec ON u.security_id = sec.id
JOIN discord d ON s.discord_id = d.id
WHERE d.username = %s AND d.discriminator = %s
'''


@bot.event
async def on_ready():

    guild = bot.get_guild(GUILD_IDS[0])

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
    # id = member.id as a string
    id = str(member.id)
    cur, conn = await ht_db.connect()
    cur.execute(
        "SELECT username, discriminator FROM discord WHERE discord_user_id=%s", (id,))
    result = cur.fetchone()

    if result is None:
        # await member.send("You have not registered your Discord account to related HackTues account. Please do so at https://hacktues.bg/ \n If you have already registered your account, please contact us at https://hacktues.bg/contact-us \n After you have registered your account, please rejoin the server at https://discord.gg/9yAbMUCg \n Thank you for your understanding!")
        await member.send("Здравейте, {member.mention}! \n Не сте регистрирали своя Discord акаунт към своя HackTues акаунт. Моля, направете го на https://hacktues.bg/ \n Ако сте регистрирали своя акаунт, моля, свържете се с нас на https://hacktues.bg/contact-us \n След като сте регистрирали своя акаунт, моля, влезте отново в сървъра на https://discord.gg/UqFRDF6RcN \n Благодарим за разбирането!")
        await member.kick(reason="Have not registered current Discord user to related HackTues account")
        print(f"{member} has been kicked from the server for not registering their Discord account to related HackTues account")
    else:
        print(f"{member} has been verified")
        username = result[0]
        discriminator = result[1]
        cur.execute(user_discord_select, (username, discriminator))
        result = cur.fetchone()
        name = result[0]
        class_value = classes[int(result[1]) - 1]
        grade = result[2]
        elsys_email_verified = result[3]
        user_id = result[4]
        role_id = result[5]
        team_id = result[6]

        if elsys_email_verified:
            await member.edit(nick=f"{name} {grade}({class_value})")
            await member.add_roles(roles["Участник"])
            # if role id = 2, add role "Капитан"
            if role_id == 2:
                await member.add_roles(roles["Капитан"])

            # if team id != 0, get team name and add role "Team <team name>"
            if team_id != 0 or team_id is not None:
                cur.execute("SELECT name FROM team WHERE id=%s", (team_id,))
                result = cur.fetchone()
                team_name = result[0]
                # check if role "Team <team name>" exists
                if f"Team {team_name}" in roles:
                    await member.add_roles(roles[f"Team {team_name}"])
                else:
                    roles[f"Team {team_name}"] = await guild.create_role(name=f"Team {team_name}")
                    await member.add_roles(roles[f"Team {team_name}"])

            cur.execute(
                "SELECT technologies_id FROM user_technologies WHERE user_id=%s", (user_id,))
            result = cur.fetchall()
            for techId in result:
                technology = str(techId[0])
                cur.execute(
                    "SELECT technology FROM technologies WHERE id=%s", (technology,))
                result = cur.fetchone()
                await member.add_roles(roles[result[0]])
            # await member.send(f"Welcome to HackTues Discord server, {first_name} {last_name}! \n You have been verified and your roles have been assigned. \n If you have any questions, please contact us at https://hacktues.bg/contact-us \n Thank you for your understanding!")
            await member.send(f"Добре дошли в HackTues Discord сървър, {name}! \n Вие сте били верифицирани и вашият роли са били присвоени. \n Ако имате въпроси, моля, свържете се с нас на https://hacktues.bg/contact-us \n Благодарим за разбирането!")

        else:
            # await member.send("You have not verified your ELSYS email. Please check your email to verify it. If you have not received the verification email, please contact us at https://hacktues.bg/contact-us \n After you have verified your email, please rejoin the server at https://discord.gg/9yAbMUCg \n Thank you for your understanding!")
            await member.send(f"Здравейте, {name}! \n Не сте верифицирали своя ELSYS имейл. Моля, проверете своя имейл, за да го верифицирате. Ако не сте получили имейла за верификация, моля, свържете се с нас на https://hacktues.bg/contact-us . \n Ако не сте се регистрирали, може да го направите на https://hacktues.bg/signup \n След като сте верифицирали своя имейл, моля, влезте отново в сървъра на https://discord.gg/UqFRDF6RcN \n Благодарим за разбирането!")
            await member.kick(reason="Have not verified ELSYS email")
            print(
                f"{member} has been kicked from the server for not verifying their ELSYS email")

    cur.close()
    conn.close()


@bot.slash_command(guild_ids=GUILD_IDS, description="Check if tech roles are in check")
@application_checks.has_permissions(administrator=True)
async def populate(interaction: Interaction):
    await interaction.response.defer()
    tech = await ht_db.get_techs()

    # create roles
    for roleKey in tech:
        role = await interaction.guild.create_role(name=roleKey)
        roles[roleKey] = role

    await interaction.followup.send("Roles created")


@bot.slash_command(guild_ids=GUILD_IDS, description="Check if tech roles are in check")
@application_checks.has_permissions(administrator=True)
async def check(interaction: Interaction):
    await interaction.response.defer()
    role_names = []
    for roleKey in roles:
        role_names.append(roleKey)
    diff = list(set(tech) - set(role_names))
    await interaction.followup.send(f"Missing roles: {diff}")


@bot.slash_command(guild_ids=GUILD_IDS, description="Drop roles from tech roles")
@application_checks.has_permissions(administrator=True)
async def drop(interaction: Interaction):
    await interaction.response.defer()
    nonTechRoles = ['admin', 'Hack Tues 9 Dev', 'Организатори',
                    'mentor', 'available-mentor', 'claimed-mentor', '@everyone']
    for roleKey in roles:
        if roleKey not in nonTechRoles:
            print(roleKey)
            await roles[roleKey].delete()
    await interaction.followup.send("Roles have been dropped!")


@bot.slash_command(guild_ids=GUILD_IDS, description="Motivate command")
async def motivate(interaction: Interaction):
    await interaction.response.send_message("https://media.discordapp.net/attachments/809713428490354759/820931975199850516/smert.gif")


@bot.slash_command(guild_ids=GUILD_IDS, description="Ticket command")
async def problem(interaction: Interaction, problem: str = SlashOption(description="What's your problem?", required=True)):
    await ht_func.ticket_sys(interaction, problem, bot)


@bot.slash_command(guild_ids=GUILD_IDS, description="Reload roles")
async def reload(interaction: Interaction):
    member = interaction.user
    guild = interaction.guild
    cur, conn = await ht_db.connect()
    username = member.name
    discriminator = member.discriminator
    print(username, discriminator)
    cur.execute(user_discord_select, (username, discriminator))
    result = cur.fetchone()
    name = result[0]
    class_value = classes[int(result[1]) - 1]
    grade = result[2]
    elsys_email_verified = result[3]
    user_id = result[4]
    role_id = result[5]
    team_id = result[6]
    await interaction.response.defer()
    if elsys_email_verified:
        await member.edit(nick=f"{name} {grade}({class_value})")
        await member.add_roles(roles["Участник"])
        # if role id = 2, add role "Капитан"
        if role_id == 2:
            await member.add_roles(roles["Капитан"])

            # if team id != 0, get team name and add role "Team <team name>"
        if team_id != 0 and team_id is not None and team_id != "None" and team_id != "":
            print(team_id)
            cur.execute("SELECT name FROM team WHERE id=%s", (team_id,))
            result = cur.fetchone()
            team_name = result[0]
            # check if role "Team <team name>" exists
            if f"Team {team_name}" in roles:
                await member.add_roles(roles[f"Team {team_name}"])
            else:
                roles[f"Team {team_name}"] = await guild.create_role(name=f"Team {team_name}")
                await member.add_roles(roles[f"Team {team_name}"])

        cur.execute(
            "SELECT technologies_id FROM user_technologies WHERE user_id=%s", (user_id,))
        result = cur.fetchall()
        for techId in result:
            technology = str(techId[0])
            cur.execute(
                "SELECT technology FROM technologies WHERE id=%s", (technology,))
            result = cur.fetchone()
            await member.add_roles(roles[result[0]])
        await interaction.followup.send("Roles have been reloaded!")


@bot.slash_command(guild_ids=GUILD_IDS, description="Create Teams")
@application_checks.has_permissions(administrator=True)
async def create_teams(interaction: Interaction):
    # go through the list of teams and create a role for each one
    # then create a category for each team and a channel for each team in that category and a voice channel for each team in that category as well
    # then create a role for each team and give it the permissions to view the channels in the category
    # then give the team role to all the members in the team

    await interaction.response.defer()
    guild = interaction.guild
    # get the list of teams from the database
    cur, conn = await ht_db.connect()
    cur.execute("SELECT name FROM teams")
    teams = cur.fetchall()
    team_ids = []
    cur.close()
    conn.close()

    # create the roles for each team
    for team in teams:
        roles[team[0]] = await guild.create_role(name=team[0])

    # create the categories for each team
    for team in teams:
        # await guild.create_category(f"TEAM {team[1].upper()}")
        await guild.create_category(f"TEAM {team[0].upper()}", overwrites={
            guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
            roles[team[0]]: nextcord.PermissionOverwrite(read_messages=True)
        })

    # # create the channels for each team
    # for team in teams:
    #     category = guild.get_channel(int(team[0]))
    #     await guild.create_text_channel(f"team-{team[1].lower()}", category=category)
    #     await guild.create_voice_channel(f"team-{team[1].lower()}", category=category)


bot.run(TOKEN)
