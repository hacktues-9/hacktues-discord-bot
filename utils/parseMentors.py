# read through the parsementors.csv file and create a list of mentors
import psycopg2
import csv
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

insert_query = """INSERT INTO mentors (first_name, last_name, email, mobile, profile_picture, company, position, description, role_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 4)"""

insert_tech_query = """INSERT INTO mentor_technologies (mentor_id, technologies_id) VALUES (%s, %s)"""
insert_time_frame_query = """INSERT INTO mentors_time_frames (mentor_id, time_frame_id) VALUES (%s, %s)"""
async def get_techs():
    cur, conn = await connect()
    cur.execute("SELECT id, technology FROM technologies")
    techs = cur.fetchall()
    reformat = {}
    for tech in techs:
        reformat[tech[1]] = int(tech[0])
    cur.close()
    conn.close()
    return techs

async def read_mentors():
    with open('parseNewMentors.csv', 'r', encoding="utf8") as f:
        csv_reader = csv.reader(f, delimiter=',')
        mentors = []
        for row in csv_reader:
            mentors.append(row)
        mentors.pop(0)  

    return mentors

async def get_mentors():
    mentors = await read_mentors()
    reformed_mentors = []
    m_id = 1
    for mentor in mentors:
        m_id += 1
        first_name = mentor[1].split(' ')[0]
        last_name = mentor[1].split(' ')[1]
        #change \n to newline character in description
        mentor[7] = mentor[7].replace('\\n', '\n')
        # format for rows is : date, email, Name, _, _, mobile, profile_picture, _, _, _, _, _, technologies, _, _, _, shirt_size, eating_preference, _, _,...
        # print(f"Name: {mentor[2]}, Email: {mentor[1]}, Mobile: {mentor[5]}, Technologies: {mentor[12]}, Shirt Size: {mentor[16]}, Eating Preference: {mentor[17]}")
        reformed_mentors.append([first_name, last_name, mentor[0], mentor[4], mentor[5], mentor[2], mentor[3], mentor[7], mentor[11], m_id, mentor[12], mentor[13]])

    return reformed_mentors

async def print_mentors(mentors):
    for mentor in mentors:
        print(f"Name: {mentor[0]} {mentor[1]}, Email: {mentor[2]}, Mobile: {mentor[3]}, Profile Picture: {mentor[4]}, Company: {mentor[5]}, Position: {mentor[6]}, Time Frames: {mentor[10]}, Place : {mentor[11]}")


async def get_mentor_techs(mentors):
    mentor_techs = []
    for mentor in mentors:
        # add all the technologies to a list without duplicates
        techs = mentor[8].split(',')
        for tech in techs:
            tech = tech.lstrip()
            if tech not in mentor_techs:
                #remove space at the start of the string
                mentor_techs.append(tech)

    # order the list alphabetically
    mentor_techs.sort()

    return mentor_techs

async def insert_mentors(mentors):
    cur, conn = await connect()
    for mentor in mentors:
        cur.execute(insert_query, (mentor[0], mentor[1], mentor[2], mentor[3], mentor[4], mentor[5], mentor[6], mentor[7]))
    conn.commit()
    cur.close()
    conn.close()

async def insert_techs(mentors):
    cur, conn = await connect()
    for mentor in mentors:
        m_techs = mentor[8].split(',')
        for tech in m_techs:
            tech = tech.lstrip()
            cur.execute("SELECT id FROM technologies WHERE technology = %s", (tech,))
            tech_id = cur.fetchone()
            if tech_id is None:
                #skip the tech if it is not in the database
                continue
            cur.execute(insert_tech_query, (mentor[9], tech_id))
    conn.commit()
    cur.close()
    conn.close()

async def insert_time_frames(mentors):
    cur, conn = await connect()
    for mentor in mentors:
        time_frames = mentor[10].split(',')
        for time_frame in time_frames:
            time_frame = time_frame.lstrip()
            print(time_frame)
            if time_frame == '':
                continue
            date = time_frame.split(' ')[0].lstrip()
            start_time = time_frame.split(' ')[1].lstrip()
            # cur.execute("SELECT id FROM time_frames WHERE date = %s AND start_time = %s", (date, start_time)) 
            # select id where date = date and start_time = start_time
            cur.execute("SELECT id FROM time_frames WHERE date = %s AND start_time = %s", (date, start_time))
            time_frame_id = cur.fetchone()
            if time_frame_id is None:
                continue
            cur.execute(insert_time_frame_query, (mentor[9], time_frame_id))
        
        # online = mentor[11].split(',')[0] to bool if 1 then true else false
        online = mentor[11].split(',')[0] == '1'
        # on_site = mentor[11].split(',')[1] to bool if 1 then true else false
        on_site = mentor[11].split(',')[1] == '1'
    
        cur.execute("UPDATE mentors SET online = %s, on_site = %s WHERE id = %s", (online, on_site, mentor[9]))
        
    conn.commit()
    cur.close()
    conn.close()

async def fix_on_site(mentors):
    cur, conn = await connect()
    for mentor in mentors:
        print(mentor[11])
        on_site = mentor[11].split(',')[1].lstrip()
        on_site_bool = on_site == '1'
        cur.execute("UPDATE mentors SET on_site = %s WHERE id = %s", (on_site_bool, mentor[9]))
    conn.commit()
    cur.close()
    conn.close()

#run print_mentors() to see the list of mentors

async def main():
    mentors = await get_mentors()
    m_techs = await get_mentor_techs(mentors)
    techs = await get_techs()

    #compare the mentor techs to the techs in the database and print the ones that are not in the database
    # for tech in m_techs:
    #     if tech not in techs:
    #         print(tech)

    # await insert_mentors(mentors)

    # await insert_techs(mentors)

    # await insert_time_frames(mentors)

    await fix_on_site(mentors)

    # await print_mentors(mentors)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())