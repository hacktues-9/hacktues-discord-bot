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

async def get_positions():
    cur, conn = await connect()
    cur.execute("SELECT name FROM positions")
    positions = cur.fetchall()
    reformat = []
    for position in positions:
        reformat.append(position[0])
    positions = reformat
    cur.close()
    conn.close()
    return positions

async def get_volunteer(email):
    cur, conn = await connect()
    cur.execute("SELECT * FROM volunteers WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

async def get_mentor(email):
    cur, conn = await connect()
    cur.execute("SELECT * FROM mentors WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

async def get_volunteers_positions(volunteer_id):
    cur, conn = await connect()
    cur.execute("SELECT position_id FROM volunteers_positions WHERE volunteer_id = %s", (volunteer_id,))
    positions = cur.fetchall()
    reformat = []
    for position in positions:
        # get position by id
        cur.execute("SELECT name FROM positions WHERE id = %s", (position[0],))
        position_name = cur.fetchone()
        reformat.append(position_name[0])
    positions = reformat
    cur.close()
    conn.close()
    return positions

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

async def verify_volunteer(code, discord_id):
    cur, conn = await connect()
    cur.execute("SELECT * FROM volunteers WHERE ver_code = %s AND discord_id IS NULL", (code,))
    user = cur.fetchone()
    cur.execute("SELECT id FROM discord WHERE discord_user_id = %s", (str(discord_id),))
    discord_id = cur.fetchone()
    if user and discord_id:
        cur.execute("UPDATE volunteers SET discord_id = %s WHERE ver_code = %s", (str(discord_id[0]), code))
        conn.commit()
        positions = await get_volunteers_positions(user[0])
        cur.close()
        conn.close()
        return user, positions
        
    cur.close()
    conn.close()
    return None, None

async def verify_mentor(code, discord_id):
    cur, conn = await connect()
    cur.execute("SELECT * FROM mentors WHERE ver_code = %s AND discord_id IS NULL", (code,))
    user = cur.fetchone()
    cur.execute("SELECT id FROM discord WHERE discord_user_id = %s", (str(discord_id),))
    discord_id = cur.fetchone()
    if user and discord_id:
        cur.execute("UPDATE mentors SET discord_id = %s WHERE ver_code = %s", (str(discord_id[0]), code))
        conn.commit()
        techs = await get_mentor_techs(user[0])
        cur.close()
        conn.close()
        return user, techs
        
    cur.close()
    conn.close()
    return None, None