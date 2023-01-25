import psycopg2

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