import sqlite3

DATABASE = 'database.db'

def create_table_posts():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def create_table_users():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
