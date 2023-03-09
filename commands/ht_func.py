import sys

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

sys.path.append('./utils')
import os
import smtplib
import ssl

from dotenv import load_dotenv
from ht_db import get_mentor, get_mentor_techs, verify_mentor, get_volunteer, get_volunteers_positions, verify_volunteer

load_dotenv()

smtp_server = "smtp.gmail.com"
port = 587  # For starttls
sender_email = "hacktues@elsys-bg.org"
password = os.getenv("EMAIL_PASSWORD")

context = ssl.create_default_context()

def send_email(name, email, verification_code):
    message = """From: HackTUES 9 <hacktues@elsys-bg.org>\nSubject: Verification Code\n\n%s""" % ( verification_code)
    print(message + " " + email)
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, password)
        server.sendmail(sender_email, email, message)


async def ticket_sys(interaction: Interaction, problem: str, bot: commands.Bot):
    await interaction.response.defer()
    channel = interaction.channel
    roles = interaction.user.roles
    guild = interaction.guild

    if "team" in channel.name:
        for role in roles:
            if "Team" in role.name:
                await interaction.followup.send(f"Вашият проблем е изпратен на менторите")

                available_mentor = guild.get_role(1024553918795091998)
                claimed_mentor = guild.get_role(1024554391887413328)
                log_channel = guild.get_channel(1024415063655862442)
                claims = guild.get_channel(1024426110265589931)
                closed = guild.get_channel(1024576000157306972)

                ticket = await log_channel.send(f"{available_mentor.mention},помогнете на {role.mention} с: \n{problem}")

                def check_ticket(r, u):
                    return (str(r) == "🎟️" and u != bot.user and (available_mentor in u.roles) and (r.message.id == ticket.id))

                while True:
                    await ticket.add_reaction("🎟️")
                    _, assigned_mentor = await bot.wait_for("reaction_add", check=check_ticket)
                    is_teams_mentor = True
                    #check if is already teams mentor
                    has_role = await assigned_mentor.get_role(role.id)
                    if has_role is None:
                        await assigned_mentor.add_roles(role)
                        is_teams_mentor = False

                    await assigned_mentor.add_roles(claimed_mentor)
                    await assigned_mentor.remove_roles(available_mentor)
                    await ticket.clear_reaction("🎟️")
                    await ticket.add_reaction("✅")
                    await ticket.add_reaction("❌")

                    def check_reaction(r, u):
                        return ((str(r) == "✅" or str(r) == "❌") and (u == assigned_mentor and u != bot.user) and (r.message.id == ticket.id))

                    def check_confirmation(r, u):
                        return((str(r) == "✅" or str(r) == "❌") and (role in u.roles) and (u != bot.user) and (r.message.id == confirmation.id))

                    await interaction.channel.send(f"{assigned_mentor.nick} се е заел с вашия проблем")

                    assignment = await claims.send(f"{assigned_mentor.nick} се е заел с проблема на {role.name}")

                    reaction, _ = await bot.wait_for("reaction_add", check=check_reaction)

                    if not is_teams_mentor:
                        await assigned_mentor.remove_roles(role)
                    await assigned_mentor.remove_roles(claimed_mentor)
                    await assigned_mentor.add_roles(available_mentor)
                    await ticket.clear_reaction("✅")
                    await ticket.clear_reaction("❌")

                    if str(reaction) == "✅":
                        confirmation = await interaction.channel.send(f"{role.mention}, проблема ви е зададен като решен!")

                        await confirmation.add_reaction("✅")
                        await confirmation.add_reaction("❌")

                        reaction, _ = await bot.wait_for("reaction_add", check=check_confirmation)
                        
                        await confirmation.clear_reaction("✅")
                        await confirmation.clear_reaction("❌")

                        if str(reaction) == "✅":
                            await ticket.delete()
                            await assignment.delete()
                            await closed.send(f"{assigned_mentor.name} реши проблема на {role.name}")
                            break
                        elif str(reaction) == "❌":
                            await interaction.channel.send(f"{role.mention}, проблема ви е отворен наново!")
                            ticket = await log_channel.send(f"{available_mentor.mention}, проблема на {role.mention} е отворен отново : \n{problem}")
                            continue
                    elif str(reaction) == "❌":
                        await interaction.channel.send(f"{role.mention}, проблема ви е отворен наново!")
                        ticket = await log_channel.send(f"{available_mentor.mention}, проблема на {role.mention} е отворен отново : \n{problem}")
                        continue

                break
        
    else:
        await interaction.followup.send("Можеш да пращаш проблеми само в каналите на отборите")

class MentorModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Verification")
        self.modalV = "register"
        self.emMail = nextcord.ui.TextInput(
            label="Имейл", min_length=1, max_length=2048, required=True, placeholder="john.doe@gmail.com")
        self.add_item(self.emMail)

    def change_modal(self):
        self.remove_items()
        self.modalV = "verification"
        self.emCode = nextcord.ui.TextInput(
            label="Код за верификация", min_length=6, max_length=6, required=True, placeholder="123456")
        self.add_item(self.emCode)

    def remove_items(self):
        self.clear_items()

    async def callback(self, interaction: Interaction):
        roles = {}
        guild = interaction.guild
        for role in await guild.fetch_roles():
            roles[role.name] = role
        if self.modalV == "register":
            mail = self.emMail.value
            user = await get_mentor(mail)
            print(user)
            if user is None:
                return await interaction.response.send_message("Няма потребител с този email", ephemeral=True)
            if user[14] is not None:
                return await interaction.response.send_message("Вече сте свързан с друг дискорд акаунт", ephemeral=True)
            
            verification_code = user[18]
            name = user[4] + " " + user[5]
            print(verification_code)
            send_email(name, mail, verification_code)
            # return await interaction.response.send_message(f"Име: {fname} \nФамилия: {lname} \nИмейл: {mail}", ephemeral=True)
            return await interaction.response.send_message("Изпратихме ви код за верификация на имейла \n когато получите кода моля използвайте командата : /mentor_code", ephemeral=True)
        elif self.modalV == "verification":
            code = self.emCode.value
            user_discord_id = interaction.user.id
            user, u_roles = await verify_mentor(code, user_discord_id)
            if user is None:
                return await interaction.response.send_message("Невалиден код или потребителят е верифициран", ephemeral=True)
            member = interaction.user
            for role in u_roles:
                print("ROLE" + role)
                await member.add_roles(roles[role])
            
            member_role = guild.get_role(1024553918795091998)
            available_mentor = guild.get_role(1072702941603037285)
            await member.add_roles(member_role)
            await member.add_roles(available_mentor)
            await member.remove_roles(roles["Unverified"])
            await member.edit(nick=user[4] + " " + user[5])
            return await interaction.response.send_message("Успешно верифициран", ephemeral=True)

        # return await interaction.response.send_message("Този бот е изключен за момента.", ephemeral=True)

class VolMentor(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Verification")
        self.modalV = "register"
        self.emMail = nextcord.ui.TextInput(
            label="Elsys Имейл", min_length=1, max_length=2048, required=True, placeholder="georgi.r.sabev.2019@elsys-bg.org")
        self.add_item(self.emMail)

    def change_modal(self):
        self.remove_items()
        self.modalV = "verification"
        self.emCode = nextcord.ui.TextInput(
            label="Код за верификация", min_length=6, max_length=6, required=True, placeholder="123456")
        self.add_item(self.emCode)

    def remove_items(self):
        self.clear_items()

    async def callback(self, interaction: Interaction):
        roles = {}
        guild = interaction.guild
        for role in await guild.fetch_roles():
            roles[role.name] = role
        if self.modalV == "register":
            mail = self.emMail.value
            user = await get_volunteer(mail)
            print(user)
            if user is None:
                return await interaction.response.send_message("Няма потребител с този email", ephemeral=True)
            if user[3] is not None:
                return await interaction.response.send_message("Вече сте свързан с друг дискорд акаунт", ephemeral=True)
            
            verification_code = user[10]
            name = user[1]
            print(verification_code)
            send_email(name, mail, verification_code)
            # return await interaction.response.send_message(f"Име: {fname} \nФамилия: {lname} \nИмейл: {mail}", ephemeral=True)
            return await interaction.response.send_message("Изпратихме ви код за верификация на имейла \n когато получите кода моля използвайте командата : /volunteer_code", ephemeral=True)
        elif self.modalV == "verification":
            code = self.emCode.value
            user_discord_id = interaction.user.id
            user, u_roles = await verify_volunteer(code, user_discord_id)
            if user is None:
                return await interaction.response.send_message("Невалиден код или потребителят е верифициран", ephemeral=True)
            member = interaction.user
            for role in u_roles:
                print("ROLE" + role)
                await member.add_roles(roles[role])
            
            member_role = guild.get_role(1072702826632970300)
            await member.add_roles(member_role)
            await member.remove_roles(roles["Unverified"])
            await member.edit(nick=user[1])
            return await interaction.response.send_message("Успешно верифициран", ephemeral=True)

        # return await interaction.response.send_message("Този бот е изключен за момента.", ephemeral=True)
