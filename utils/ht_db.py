import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB_NAME')
port = os.getenv('DB_PORT')

async def connect():
    conn = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
    )

    cur = conn.cursor()
    return cur, conn

async def get_techs():
    cur, conn = await connect()
    cur.execute("SELECT technology FROM technologies")
    techs = cur.fetchall()
    reformat = []
    for tech in techs:
        reformat.append(tech[0])
    techs = reformat
    cur.close()
    conn.close()
    return techs