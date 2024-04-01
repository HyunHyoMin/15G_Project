from flask import Flask, request, redirect, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)

now = datetime.now()
date = now.strftime('%Y-%m-%d %H:%M') 
DATABASE = 'database.db'

def create_table():
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

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id, title, date FROM posts")
    posts = cur.fetchall()
    conn.close()
    return render_template('index.html', posts = posts)

@app.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'POST' and request.form['btn']=='1':
        title = request.form['title']
        content = request.form['content']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("INSERT INTO posts (title, content, date) VALUES (?, ?, ?)", (title, content, date))
        conn.commit()
        new_post_id = cur.lastrowid
        conn.close()
        return redirect(f'/post/{new_post_id}')
    elif request.method == 'POST' and request.form['btn']=='0':
        return index()
    return render_template('create.html')

@app.route('/post/<int:post_id>', methods=['GET'])
def post(post_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cur.fetchone()
    conn.close()
    return render_template('post.html', post=post)

if __name__ == '__main__':
    create_table()
    app.run(debug=True)