# read through the parseVolunteers.csv file and create a list of volunteers
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

position_ids = {
    "Хамал" : 1,
    "Общак" : 2,
    "Регистрация" : 3,
    "Информация" : 4,
    "Food Corner" : 5,
    "Фотограф" : 6,
}

classes = {
    "А" : 1,
    "Б" : 2,
    "В" : 3,
    "Г" : 4,
}

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

insert_query = """INSERT INTO volunteers (name, email, grade, class_id) VALUES (%s, %s, %s, %s)"""
insert_positions_query = """INSERT INTO volunteers_positions (volunteer_id, position_id) VALUES (%s, %s)"""

async def read_volunteers():
    with open('parseVolunteers.csv', 'r', encoding="utf8") as f:
        csv_reader = csv.reader(f, delimiter=',')
        volunteers = []
        for row in csv_reader:
            volunteers.append(row)
        volunteers.pop(0)  

    return volunteers

async def get_volunteers():
    volunteers = await read_volunteers()
    reformed_volunteers = []
    v_id = 1
    for volunteer in volunteers:
        v_id += 1
        name = volunteer[2] + " " + volunteer[3]
        # format for rows is : date, email, Name, _, _, mobile, profile_picture, _, _, _, _, _, technologies, _, _, _, shirt_size, eating_preference, _, _,...
        # print(f"Name: {volunteer[2]}, Email: {volunteer[1]}, Mobile: {volunteer[5]}, Technologies: {volunteer[12]}, Shirt Size: {volunteer[16]}, Eating Preference: {volunteer[17]}")
        reformed_volunteers.append([volunteer[1], name, volunteer[5], volunteer[6], volunteer[9], v_id])

    return reformed_volunteers

async def print_volunteers(volunteers):
    for volunteer in volunteers:
        print(f"ID: {volunteer[5]}, Name: {volunteer[1]}, Email: {volunteer[0]}, Class: {volunteer[2]} {volunteer[3]}, Positions: {volunteer[4]}")

async def insert_volunteers(volunteers):
    cur, conn = await connect()
    for volunteer in volunteers:
        #name, email, grade, class_id
        cur.execute(insert_query, (volunteer[1], volunteer[0], volunteer[2], classes[volunteer[3]]))
    conn.commit()
    cur.close()
    conn.close()

async def insert_volunteers_positions(volunteers):
    cur, conn = await connect()
    for volunteer in volunteers:
        positions = volunteer[4].split(", ")
        for position in positions:
            # print(f"Volunteer ID: {volunteer[5]}, Position ID: {position_ids[position]}")
            cur.execute(insert_positions_query, (volunteer[5], position_ids[position]))
    conn.commit()
    cur.close()
    conn.close()
    
async def main():
    volunteers = await get_volunteers()


    # await insert_volunteers(volunteers)

    await insert_volunteers_positions(volunteers)

    # await fix_on_site(volunteers)

    # await print_volunteers(volunteers)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())