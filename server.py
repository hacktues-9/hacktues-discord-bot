from nextcord import Interaction, SlashOption, Intents, AudioSource, FFmpegOpusAudio, VoiceClient, PermissionOverwrite
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
    guild = bot.get_guild(GUILD_IDS[0])
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

        if result is None:
            #give user "Unverified" role
            await member.add_roles(roles["Unverified"])
            # exit function
            cur.close()
            conn.close()
            return

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

@bot.slash_command(guild_ids=GUILD_IDS, description="Ping the bot")
async def ping(interaction: Interaction):
    await interaction.response.send_message("Pong!")


@bot.slash_command(guild_ids=GUILD_IDS, description="Check if tech roles are in check")
@application_checks.has_permissions(administrator=True)
async def populate(interaction: Interaction):
    await interaction.response.defer()
    tech = await ht_db.get_techs()

    # go through roles delete all roles without members 
    for role in await interaction.guild.fetch_roles():
        if role.name in tech:
            if len(role.members) == 0:
                await role.delete()

    #refresh roles dict
    roles = {}
    for role in await interaction.guild.fetch_roles():
        roles[role.name] = role

    # create roles if not in guild roles
    for roleKey in tech:
        if roleKey not in roles:
            roles[roleKey] = await interaction.guild.create_role(name=roleKey)

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

    guild = interaction.guild
    await interaction.response.defer()
    # get the list of teams from the database
    cur, conn = await ht_db.connect()
    cur.execute("SELECT name FROM teams")
    teams = cur.fetchall()
    category_ids = {}
    print(teams)

    # create the roles for each team
    for team in teams:
        if f"Team {team[0]}" not in roles:
            print(f"Creating role = Team {team[0]}")
            roles[f"Team {team[0]}"] = await guild.create_role(name=f"Team {team[0]}")
    
    # create the categories for each team
    for team in teams:
        print(f"Creating category = TEAM {team[0].upper()}")
        # await guild.create_category(f"TEAM {team[1].upper()}")
        category = await guild.create_category(f"TEAM {team[0].upper()}", overwrites={
            guild.default_role: PermissionOverwrite(read_messages=False),
            roles[f"Team {team[0]}"]: PermissionOverwrite(read_messages=True)
        })
        category_ids[team[0]] = category.id

    # create the channels for each team
    for team in teams:
        print(f"Creating channel = team-{team[0].lower()}")
        category = guild.get_channel(category_ids[team[0]])
        await guild.create_text_channel(f"team-{team[0].lower()}", category=category)
        await guild.create_voice_channel(f"team-{team[0].lower()}", category=category)

    await interaction.followup.send("Teams have been created!")

    
    cur.close()
    conn.close()

@bot.slash_command(guild_ids=GUILD_IDS, description="Delete Teams")
@application_checks.has_permissions(administrator=True)
async def delete_teams(interaction: Interaction):
    # delete roles with "Team" in the name
    # delete categories with "TEAM" in the name

    guild = interaction.guild
    await interaction.response.defer()
    # get the list of teams from the database
    cur, conn = await ht_db.connect()
    cur.execute("SELECT name FROM teams")
    teams = cur.fetchall()
    category_ids = {}
    print(teams)

    # delete the roles for each team
    for team in teams:
        if f"Team {team[0]}" in roles:
            print(f"Deleting role = Team {team[0]}")
            await roles[f"Team {team[0]}"].delete()
            del roles[f"Team {team[0]}"]

    # get the category ids for each team
    for team in teams:
        # get channel with name "TEAM <team name>"
        for channel in guild.channels:
            if channel.name == f"TEAM {team[0].upper()}":
                category_ids[team[0]] = channel.id

    # delete the categories for each team
    for team in teams:
        print(f"Deleting category = TEAM {team[0].upper()}")
        if team[0] in category_ids:
            category = guild.get_channel(category_ids[team[0]])
            await category.delete()

    await interaction.followup.send("Teams have been deleted!")

@bot.slash_command(guild_ids=GUILD_IDS, description="Verification Message")
@application_checks.has_permissions(administrator=True)
async def verification_message(interaction: Interaction):
    await interaction.response.defer()
    await interaction.followup.send("Please send the verification message in the next 30 seconds")
    await interaction.send("Здравейте, ако сте Ментор, моля използвайте командата /mentor_verify, благодарим!")

@bot.slash_command(guild_ids=GUILD_IDS, description="Mentor Verification")
@application_checks.has_role("Unverified")
async def mentor_verify(interaction: Interaction):
    # await interaction.response.defer()
    member = interaction.user
    modal = ht_func.MentorModal()
    await interaction.response.send_modal(modal)
    await modal.wait()

@bot.slash_command(guild_ids=GUILD_IDS, description="Mentor code")
@application_checks.has_role("Unverified")
async def mentor_code(interaction: Interaction):
    # await interaction.response.defer()
    member = interaction.user
    modal = ht_func.MentorModal()
    modal.change_modal()
    await interaction.response.send_modal(modal)
    await modal.wait()

@bot.slash_command(guild_ids=GUILD_IDS, description="Volunteer Verification")
@application_checks.has_role("Unverified")
async def volunteer_verify(interaction: Interaction):
    # await interaction.response.defer()
    member = interaction.user
    modal = ht_func.VolMentor()
    await interaction.response.send_modal(modal)
    await modal.wait()

@bot.slash_command(guild_ids=GUILD_IDS, description="Volunteer code")
@application_checks.has_role("Unverified")
async def volunteer_code(interaction: Interaction):
    # await interaction.response.defer()
    member = interaction.user
    modal = ht_func.VolMentor()
    modal.change_modal()
    await interaction.response.send_modal(modal)
    await modal.wait()

@bot.slash_command(guild_ids=GUILD_IDS, description="Fix Member Tech Roles")
@application_checks.has_permissions(administrator=True)
async def fix_member_tech_roles(interaction: Interaction):
    await interaction.response.defer()
    guild = interaction.guild
    cur, conn = await ht_db.connect()
    request = """
    SELECT concat(u.first_name, ' ', u.last_name) as name, i.class_id, i.grade, u.id
    FROM users as u
    JOIN info i on u.info_id = i.id
    JOIN socials s on i.socials_id = s.id
    JOIN class c on i.class_id = c.id
    WHERE s.discord_id IS NOT NULL AND u.deleted_at IS NULL AND u.team_id IS NOT NULL AND u.team_id != 1
    """
    cur.execute(request)
    members = cur.fetchall()
    users = {member.display_name: member for member in guild.members}
    for member in members:
        name = member[0]
        class_value = classes[int(member[1]) - 1]
        grade = member[2]
        user_id = member[3]

        users_names = users.keys()
        if f"{name} {grade}({class_value})" in users_names:
            user = users[f"{name} {grade}({class_value})"]

            cur.execute(
            "SELECT technologies_id FROM user_technologies WHERE user_id=%s", (user_id,))
            result = cur.fetchall()
            for techId in result:
                technology = str(techId[0])
                cur.execute(
                    "SELECT technology FROM technologies WHERE id=%s", (technology,))
                result = cur.fetchone()
                await user.add_roles(roles[result[0]])

# @bot.slash_command(guild_ids=GUILD_IDS, description="Fix Mentor Tech Roles")
# @application_checks.has_permissions(administrator=True)
# async def fix_mentor_tech_roles(interaction: Interaction):
#     await interaction.response.defer()
#     guild = interaction.guild
#     cur, conn = await ht_db.connect()
#     request = """
#     SELECT concat(u.first_name, ' ', u.last_name) as name, i.class_id, i.grade, u.id
#     FROM users as u
#     JOIN info i on u.info_id = i.id
#     JOIN socials s on i.socials_id = s.id
#     JOIN class c on i.class_id = c.id
#     WHERE s.discord_id IS NOT NULL AND u.deleted_at IS NULL AND u.team_id = 1
#     """
#     cur.execute(request)
#     members = cur.fetchall()
#     users = {member.display_name: member for member in guild.members}
#     for member in members:
#         name = member[0]
#         class_value = classes[int(member[1]) - 1]
#         grade = member[2]
#         user_id = member[3]

#         users_names = users.keys()
#         if f"{name} {grade}({class_value})" in users_names:
#             user = users[f"{name} {grade}({class_value})"]

#             cur.execute(
#             "SELECT technologies_id FROM user_technologies WHERE user_id=%s", (user_id,))
#             result = cur.fetchall()
#             for techId in result:
#                 technology = str(techId[0])
#                 cur.execute(
#                     "SELECT technology FROM technologies WHERE id=%s", (technology,))
#                 result = cur.fetchone()
#                 await user.add_roles(roles[result[0]])

@bot.slash_command(guild_ids=GUILD_IDS, description="Fix Member Team Roles")
@application_checks.has_permissions(administrator=True)
async def fix_member_team_roles(interaction: Interaction):
    await interaction.response.defer()
    guild = interaction.guild
    cur, conn = await ht_db.connect()
    request = """
    SELECT concat(u.first_name, ' ', u.last_name) as name, i.class_id, i.grade, u.id, u.team_id
    FROM users as u
    JOIN info i on u.info_id = i.id
    JOIN socials s on i.socials_id = s.id
    JOIN class c on i.class_id = c.id
    WHERE s.discord_id IS NOT NULL AND u.deleted_at IS NULL AND u.team_id IS NOT NULL AND u.team_id != 1
    """
    cur.execute(request)
    members = cur.fetchall()
    users = {member.display_name: member for member in guild.members}

    # reload roles
    roles = {}
    for role in await guild.fetch_roles():
        roles[role.name] = role

    for member in members:
        name = member[0]
        class_value = classes[int(member[1]) - 1]
        grade = member[2]
        user_id = member[3]
        team_id = member[4]

        users_names = users.keys()
        if f"{name} {grade}({class_value})" in users_names:
            user = users[f"{name} {grade}({class_value})"]

            cur.execute("SELECT name FROM teams WHERE id=%s", (team_id,))
            result = cur.fetchone()
            team_name = result[0]
            # check if user has role "Team <team name>"
            if user.get_role(roles[f"Team {team_name}"].id) is not None:
                print(f"{user.name} already has role Team {team_name}")
                continue
            # check if role "Team <team name>" exists
            if f"Team {team_name}" in roles:
                print(f"Adding role Team {team_name} to {user.name}")
                await user.add_roles(roles[f"Team {team_name}"])
            else:
                interaction.send(f"Add role Team {team_name} to {user.name}")

@bot.slash_command(guild_ids=GUILD_IDS, description="Fix Mentor Team Roles")
@application_checks.has_permissions(administrator=True)
async def fix_mentor_team_roles(interaction: Interaction):
    await interaction.response.defer()
    guild = interaction.guild
    cur, conn = await ht_db.connect()
    request = """
    SELECT concat(m.first_name, ' ', m.last_name) as name, m.team_id
    FROM mentors as m
    WHERE m.deleted_at IS NULL AND m.team_id IS NOT NULL AND m.team_id != 1
    """
    cur.execute(request)
    members = cur.fetchall()
    users = {member.display_name: member for member in guild.members}

    # reload roles
    roles = {}
    for role in await guild.fetch_roles():
        roles[role.name] = role

    for member in members:
        name = member[0]
        team_id = member[1]

        users_names = users.keys()
        if name in users_names:
            user = users[name]

            

            cur.execute("SELECT name FROM teams WHERE id=%s", (team_id,))
            result = cur.fetchone()
            team_name = result[0]
            #
            # check if user has role "Team <team name>"
            if user.get_role(roles[f"Team {team_name}"].id) is not None:
                print(f"User {user.name} already has role Team {team_name}")
                continue
            # check if role "Team <team name>" exists
            if f"Team {team_name}" in roles:
                await user.add_roles(roles[f"Team {team_name}"])
            else:
                roles[f"Team {team_name}"] = await guild.create_role(name=f"Team {team_name}")
                await user.add_roles(roles[f"Team {team_name}"])

@bot.slash_command(guild_ids=GUILD_IDS, description="Fix Tech Roles")
@application_checks.has_permissions(administrator=True)
async def fix_tech_roles(interaction: Interaction):
    # remove duplicate roles
    await interaction.response.defer()
    guild = interaction.guild
    rols = {}
    # get list of roles from server and remove duplicates
    for role in guild.roles:
        if role.name in rols:
            print(f"Deleting role = {role.name}")
            await role.delete()
        else:
            rols[role.name] = role
    
    #refresh roles dict
    roles = {}
    for role in await interaction.guild.fetch_roles():
        roles[role.name] = role
    # that's it, we're done
    await interaction.followup.send("Tech roles have been fixed!")


@bot.slash_command(guild_ids=GUILD_IDS, description="Get Missing Members")
@application_checks.has_permissions(administrator=True)
async def get_missing_members(interaction: Interaction):
    # get the list of members from the database
    # get the list of members from the server
    # compare the two lists and return the missing members

    await interaction.response.defer()
    cur, conn = await ht_db.connect()
    request = """
    SELECT concat(u.first_name, ' ', u.last_name) as name, i.class_id, i.grade
    FROM users as u
    JOIN info i on u.info_id = i.id
    JOIN socials s on i.socials_id = s.id
    JOIN class c on i.class_id = c.id
    WHERE s.discord_id IS NOT NULL AND u.deleted_at IS NULL AND u.team_id IS NOT NULL AND u.team_id != 1
    ORDER BY i.grade, c.name, u.first_name, u.last_name;
    """ 
    # get the list of members from the server
    users = []
    for member in interaction.guild.members:
        users.append(member.display_name)
    cur.execute(request)
    members = cur.fetchall()
    missing_members = []
    for member in members:
        name = member[0]
        class_value = classes[int(member[1]) - 1]
        grade = member[2]
        if f"{name} {grade}({class_value})" not in users:
            missing_members.append(f"{name} {grade}({class_value})")
    await interaction.followup.send(f"Missing members: {missing_members}")

    cur.close()
    conn.close()

bot.run(TOKEN)
