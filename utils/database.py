import sqlite3

conn = sqlite3.connect('./db/user_info.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL)
''')
conn.commit()
conn.close()