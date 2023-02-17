import os

import psycopg2
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

async def get_mentor(email):
    cur, conn = await connect()
    cur.execute("SELECT * FROM mentors WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

async def get_mentor_techs(mentor_id):
    cur, conn = await connect()
    cur.execute("SELECT technologies_id FROM mentor_technologies WHERE mentor_id = %s", (mentor_id,))
    techs = cur.fetchall()
    reformat = []
    for tech in techs:
        # get technology by id
        cur.execute("SELECT technology FROM technologies WHERE id = %s", (tech[0],))
        tech_name = cur.fetchone()
        reformat.append(tech_name[0])
    techs = reformat
    cur.close()
    conn.close()
    return techs

async def verify_mentor(code, discord_id):
    cur, conn = await connect()
    cur.execute("SELECT * FROM mentors WHERE ver_code = %s AND discord_id IS NULL", (code,))
    user = cur.fetchone()
    cur.execute("SELECT id FROM discord WHERE discord_user_id = %s", (str(discord_id),))
    discord_id = cur.fetchone()
    if user and discord_id:
        cur.execute("UPDATE mentors SET discord_id = %s WHERE ver_code = %s", (str(discord_id), code))
        conn.commit()
        techs = get_mentor_techs(user[0])
        cur.close()
        conn.close()
        return user, techs
        
    cur.close()
    conn.close()
    return None, None