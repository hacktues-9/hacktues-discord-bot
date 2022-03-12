# coding=utf-8
import aiohttp
from discord import utils
from discord.ext import tasks, commands

from utils import get_team_role, request, send_log

import channels

MAX_TEAMS_COUNT = 50

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.reason = 'tasks'
        self.bot = bot
        self.fetch_teams.start()
        # self.fetch_leaderboard.start()

    def cog_unload(self):
        self.fetch_teams.cancel()
        self.fetch_leaderboard.cancel()

    @tasks.loop(minutes=5)
    async def fetch_teams(self):
    #     print('Fetching teams...')

    #     async with aiohttp.ClientSession() as client:
    #         teams = await request(self.bot, client, path='api/team/get-teams')
    #         teams = teams['response']

        # ! Writes every team as a text message in a separate channel
        # await self.all_teams.delete()
        # self.all_teams = (await self.teams_channel.
        #                   send("self.all_teams: "))

        # count = len([elem for elem in teams if elem['approved'] is True])

        # if (count > MAX_TEAMS_COUNT):
        #     max = count
        # else:
        #     max = MAX_TEAMS_COUNT

        # ! Changes label of a channel to the current team count
        # await self.label.edit(name=f'Брой отбори: {count} / {max}')
        
        # for team in teams:
        #     team_name = 'team ' + team['teamName']
        #     await self.all_teams.edit(
        #         content=f"{self.all_teams.content}\n{team_name}"
        #     )
        '''
            # ? Cycle through every team's members and try
            # ? to find them in discord and set their *team* role
            role = await get_team_role(team_name, self.guild, self.reason)
            for user in team['member']:
                try:
                    member = await self.guild.fetch_member(user['discord_id'])
                except Exception:
                    continue
                await member.add_roles(role, reason=self.reason)
        '''
        # ? Cycle through users and sets *captain*, *team* roles
        print('Fetching users...')
        async with aiohttp.ClientSession() as client:
            users = await request(self.bot, client, path='api/user/get-discord-users')
            users = users['response']

        for user in users:
            print("user", user)

            # The owner of the guild
            if(user['discordId'] == channels.GUILD_OWNER_ID):
                continue

            try:
                member = await self.guild.fetch_member(user['discordId'])
            except Exception:
                continue

            reason = "Member joined"
            participant_r = utils.get(member.guild.roles, name='Участник')
            unapproved_r = utils.get(member.guild.roles, name='Непотвърден')

            if participant_r not in member.roles:
                await member.add_roles(participant_r, reason=reason)
            if unapproved_r in member.roles:
                await member.remove_roles(unapproved_r, reason=reason)

            if(user['teamName'] is not None):
                team_name = 'team ' + user['teamName']
                team_r = await get_team_role(team_name, member.guild, reason)

                # If user doesn't has the team role
                if team_r not in member.roles:
                    await member.add_roles(team_r, reason=reason)


            await member.edit(nick=f"{user['fullName']} {user['studentClass']}")

            roles = [role for role in member.roles if 'team' in role.name]
            if len(roles) > 0 and user['teamName'] is None:
                print("Removing roles for", user['fullName'])
                await member.remove_roles(*roles, reason=self.reason)

            if not user['isCaptain']:
                await member.remove_roles(self.captain_role,
                                          reason=self.reason)
            else:
                await member.add_roles(self.captain_role, reason=self.reason)

            if len(roles) > 1:
                await member.remove_roles(*roles, reason=self.reason)
                team_name = 'team ' + user["teamName"]
                role = await get_team_role(team_name, member.guild, reason)
                await member.add_roles(role, reason=self.reason)
                
    @tasks.loop(minutes=1)
    async def fetch_leaderboard(self):
        print("Fetching Leaderboard...")

        async with aiohttp.ClientSession() as client:
            leaderboard = await request(self.bot, client, path='api/team/get-leaderboard')
            leaderboard = leaderboard['response']
        leaderboard_message = ("**GrishoPoints (GP) класация**\n"
        "*GP се печелят от участие, събития или тайни задачи*\n"
        "\n"
        f":first_place: {leaderboard[0]['teamName']} ({leaderboard[0]['grishoPoints']})\n"
        f":second_place: {leaderboard[1]['teamName']} ({leaderboard[1]['grishoPoints']})\n"
        f":third_place: {leaderboard[2]['teamName']} ({leaderboard[2]['grishoPoints']})\n"
        f"       {leaderboard[3]['teamName']} ({leaderboard[3]['grishoPoints']})\n"
        f"       {leaderboard[4]['teamName']} ({leaderboard[4]['grishoPoints']})")

        # for team in leaderboard:
        #     leaderboard_message += f"{team['grishoPoints']} - {team['teamName']}\n"

        await self.leaderboard_message.edit(content=leaderboard_message)
        # print(leaderboard_message)


    @fetch_leaderboard.before_loop
    async def before_fetch_leaderboard(self):
        await self.bot.wait_until_ready()
        self.leaderboard_channel = await self.bot.fetch_channel(channels.LEADERBOARD)
        self.leaderboard_message = await self.leaderboard_channel.fetch_message(str(channels.LEADERBOARD_MESSAGE)) 

    @fetch_teams.before_loop
    async def after_init(self):
        await self.bot.wait_until_ready()
        self.guild = await self.bot.fetch_guild(channels.GUILD_ID)
        # self.label = await self.bot.fetch_channel(channels.REGISTERED)
        self.teams_channel = await self.bot.fetch_channel(channels.TEAMS)
        self.all_teams = await self.teams_channel.send(":")
        self.captain_role = utils.get(self.guild.roles, name='Капитан')

    @fetch_teams.error
    async def on_exception(self, exc):
        await send_log(str(exc), self.bot)
        self.fetch_teams.restart()
        raise exc
