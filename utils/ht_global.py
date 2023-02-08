import os
from dotenv import load_dotenv
load_dotenv()

classes = ['А','Б','В','Г',]
TOKEN = str(os.getenv('TOKEN'))
# split GUILD IDS by comma and put them in a list
GUILD_IDS =  [int(x) for x in os.getenv('GUILD_IDS').split(', ')]