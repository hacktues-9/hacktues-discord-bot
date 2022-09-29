from nextcord import Interaction, SlashOption, Intents, AudioSource, FFmpegOpusAudio, VoiceClient
from nextcord.ext import commands
import os, sys
import time
import asyncio
import re
from dotenv import load_dotenv
import psycopg2
from slh_commands import ticket_sys
from typing import Dict, List
import atexit
import requests
import urllib.parse, urllib.request
import yt_dlp

load_dotenv()
TOKEN = str(os.getenv('TOKEN'))
GUILD_IDS = [int(os.getenv('GUILD_ID1')), int(os.getenv('GUILD_ID2'))]
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

ytdl_format_options = {'format': 'bestaudio',
                       'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
                       'restrictfilenames': True,
                       'no-playlist': True,
                       'nocheckcertificate': True,
                       'ignoreerrors': False,
                       'logtostderr': False,
                       'geo-bypass': True,
                       'quiet': True,
                       'no_warnings': True,
                       'default_search': 'auto',
                       'source_address': '0.0.0.0'}
ffmpeg_options = {'options': '-vn -sn'}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class Source:
    """Parent class of all music sources"""

    def __init__(self, audio_source: AudioSource, metadata):
        self.audio_source: AudioSource = audio_source
        self.metadata = metadata
        self.title: str = metadata.get('title', 'Unknown title')
        self.url: str = metadata.get('url', 'Unknown URL')

    def __str__(self):
        return f'{self.title} ({self.url})'


class YTDLSource(Source):
    """Subclass of YouTube sources"""

    def __init__(self, audio_source: AudioSource, metadata):
        super().__init__(audio_source, metadata)
        self.url: str = metadata.get('webpage_url', 'Unknown URL')  # yt-dlp specific key name for original URL

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        metadata = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in metadata: metadata = metadata['entries'][0]
        filename = metadata['url'] if stream else ytdl.prepare_filename(metadata)
        return cls(await FFmpegOpusAudio.from_probe(filename, **ffmpeg_options), metadata)


class ServerSession:
    def __init__(self, guild_id, voice_client):
        self.guild_id: int = guild_id
        self.voice_client: VoiceClient = voice_client
        self.queue: List[Source] = []

    def display_queue(self) -> str:
        currently_playing = f'Currently playing: 0. {self.queue[0]}'
        return currently_playing + '\n' + '\n'.join([f'{i + 1}. {s}' for i, s in enumerate(self.queue[1:])])

    async def add_to_queue(self, ctx, url):  # does not auto start playing the playlist
        yt_source = await YTDLSource.from_url(url, loop=bot.loop, stream=False)  # stream=True has issues and cannot use Opus probing
        self.queue.append(yt_source)
        if self.voice_client.is_playing():
            await ctx.response.send_message(f'Added to queue: {yt_source.title}')
            pass  # to stop the typing indicator

    async def start_playing(self, ctx):
        self.voice_client.play(self.queue[0].audio_source, after=lambda e=None: self.after_playing(ctx, e))
        await ctx.response.send_message(f'Now playing: {self.queue[0].title}')

    async def after_playing(self, ctx, error):
        if error:
            raise error
        else:
            if self.queue:
                await self.play_next(ctx)

    async def play_next(self, ctx):  # should be called only after making the first element of the queue the song to play
        self.queue.pop(0)
        if self.queue:
            await self.voice_client.play(self.queue[0].audio_source, after=lambda e=None: self.after_playing(ctx, e))
            await ctx.response.send_message(f'Now playing: {self.queue[0].title}')

server_sessions: Dict[int, ServerSession] = {}  # guild_id: ServerSession

def clean_cache_files():
    if not server_sessions:  # only clean if no servers are connected
        for file in os.listdir():
            if os.path.splitext(file)[1] in ['.webm', '.mp4', '.m4a', '.mp3', '.ogg'] and time.time() - os.path.getmtime(file) > 7200:  # remove all cached webm files older than 2 hours
                os.remove(file)

def get_res_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller
     Relative path will always get extracted into root!"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    if os.path.isfile(os.path.join(base_path, relative_path)):
        return os.path.join(base_path, relative_path)
    else:
        raise FileNotFoundError(f'Embedded file {os.path.join(base_path, relative_path)} is not found!')

@atexit.register
def cleanup():
    global server_sessions
    for vc in server_sessions.values():
        vc.disconnect()
        vc.cleanup()
    server_sessions = {}
    clean_cache_files()

async def connect_to_voice_channel(ctx, channel):
    voice_client = await channel.connect()
    if voice_client.is_connected():
        server_sessions[ctx.guild.id] = ServerSession(ctx.guild.id, voice_client)
        await ctx.response.send_message(f'Connected to {voice_client.channel.name}.')
        return server_sessions[ctx.guild.id]
    else:
        await ctx.response.send_message(f'Failed to connect to voice channel {ctx.author.voice.channel.name}.')

@bot.slash_command(name='disconnect', description='Disconnects the bot from the voice channel.')
async def disconnect(ctx):
    """Disconnect from voice channel"""
    guild_id = ctx.guild.id
    if guild_id in server_sessions:
        voice_client = server_sessions[guild_id].voice_client
        await voice_client.disconnect()
        voice_client.cleanup()
        del server_sessions[guild_id]
        await ctx.response.send_message(f'Disconnected from {voice_client.channel.name}.')

@bot.slash_command(name='pause', description='Pauses the currently playing song.')
async def pause(ctx):
    """Pause the current song"""
    guild_id = ctx.guild.id
    if guild_id in server_sessions:
        voice_client = server_sessions[guild_id].voice_client
        if voice_client.is_playing():
            voice_client.pause()
            await ctx.response.send_message('Paused')


@bot.slash_command(name='resume', description='Resumes the currently paused song.')
async def resume(ctx):
    """Resume the current song"""
    guild_id = ctx.guild.id
    if guild_id in server_sessions:
        voice_client = server_sessions[guild_id].voice_client
        if voice_client.is_paused():
            voice_client.resume()
            await ctx.response.send_message('Resumed')

@bot.slash_command(name='skip', description='Skips the current song.')
async def skip(ctx):
    """Skip the current song"""
    guild_id = ctx.guild.id
    if guild_id in server_sessions:
        session = server_sessions[guild_id]
        voice_client = session.voice_client
        if voice_client.is_playing():
            if len(session.queue) > 1:
                voice_client.stop()  # this will trigger after_playing callback and in that will call play_next so here no need call play_next
                await ctx.response.send_message('Skipped')
            else:
                await ctx.response.send_message('This is already the last item in the queue!')

@bot.slash_command(name='queue', description='Displays the current queue.')
async def show_queue(ctx):
    """Show the current queue"""
    guild_id = ctx.guild.id
    if guild_id in server_sessions:
        await ctx.response.send_message(f'{server_sessions[guild_id].display_queue()}')

@bot.slash_command(name='remove', description='Removes a song from the queue.')
async def remove(ctx, i: int):
    """Remove an item from queue by index (1, 2...)"""
    guild_id = ctx.guild.id
    if guild_id in server_sessions:
        if i == 0:
            await ctx.response.send_message('Cannot remove current playing song, please use !skip instead.')
        elif i >= len(server_sessions[guild_id].queue):
            await ctx.response.send_message(f'The queue is not that long, there are only {len(server_sessions[guild_id].queue)-1} items in the queue.')
        else:
            removed = server_sessions[guild_id].queue.pop(i)
            removed.audio_source.cleanup()
            await ctx.response.send_message(f'Removed {removed} from queue.')

@bot.slash_command(name='queue', description='Displays the current queue.')
async def clear(ctx):
    """Clear the queue and stop current song"""
    guild_id = ctx.guild.id
    if guild_id in server_sessions:
        voice_client = server_sessions[guild_id].voice_client
        server_sessions[guild_id].queue = []
        if voice_client.is_playing():
            voice_client.stop()
        await ctx.response.send_message('Queue cleared.')

@bot.slash_command(name='song', description='Displays the currently playing song.')
async def song(ctx):
    """Show the current song"""
    guild_id = ctx.guild.id
    if guild_id in server_sessions:
        await ctx.response.send_message(f'Now playing {server_sessions[guild_id].queue[0]}')

@bot.slash_command(name='play', description='Plays a song from YouTube.')
async def play(ctx, query: str):
    guild_id = ctx.guild.id
    if guild_id not in server_sessions:
        if ctx.user.voice is None:
            await ctx.response.send_message(f'{ctx.author.mention} you are not connected to a voice channel.')
            return 
        else:
            session = await connect_to_voice_channel(ctx, ctx.user.voice.channel)
    else:
        session = server_sessions[guild_id]
        if session.voice_client.channel != ctx.user.voice.channel:
            await session.voice_client.move_to(ctx.user.voice.channel)
            await ctx.response.send_message(f'Moved to {ctx.user.voice.channel.name}.')
    try :
        requests.get(query)
    except(requests.ConnectionError, requests.exceptions.MissingSchema):
        query_string = urllib.parse.urlencode({"search_query" : url})
        formatUrl = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
        search_results = re.findall(r"watch\?v=(\S{11})", formatUrl.read().decode())
        url = "http://www.youtube.com/watch?v=" + search_results[0]
    else:
        url = query

    await session.add_to_queue(ctx, url)
    if not session.voice_client.is_playing() and len(session.queue) <= 1:
        await session.start_playing(ctx)

@bot.slash_command(name='join', description='Joins the voice channel you are in.')
async def join(ctx):
    guild_id = ctx.guild.id
    if guild_id not in server_sessions:
        if ctx.user.voice is None:
            await ctx.response.send_message(f'{ctx.author.mention} you are not connected to a voice channel.')
            return 
        else:
            session = await connect_to_voice_channel(ctx, ctx.user.voice.channel)
    else:
        session = server_sessions[guild_id]
        if session.voice_client.channel != ctx.user.voice.channel:
            await session.voice_client.move_to(ctx.user.voice.channel)
            await ctx.response.send_message(f'Moved to {ctx.user.voice.channel.name}.')

@bot.event
async def on_ready():

    guild = bot.get_guild(GUILD_IDS[1])

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
            
@bot.slash_command(guild_ids=GUILD_IDS, description="Motivate command")
async def motivate(interaction: Interaction):
    await interaction.response.send_message("https://media.discordapp.net/attachments/809713428490354759/820931975199850516/smert.gif")

@bot.slash_command(guild_ids=GUILD_IDS, description="Ticket command")
async def problem(interaction: Interaction, problem: str = SlashOption(description="What's your problem?", required=True)):
    await ticket_sys(interaction, problem, bot)

bot.run(TOKEN)
