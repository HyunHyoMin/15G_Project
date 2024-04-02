from flask import Flask, request, redirect, render_template
import sqlite3
from models import create_table_posts,create_table_users
from datetime import datetime

app = Flask(__name__)

now = datetime.now()
date = now.strftime('%Y-%m-%d %H:%M') 
DATABASE = 'database.db'

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

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?", (title, content, post_id))
        conn.commit()
        conn.close()
        return redirect(f'/post/{post_id}')
    else:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        post = cur.fetchone()
        conn.close()
        return render_template('edit.html', post=post)

@app.route('/delete/<int:post_id>', methods=['GET'])
def delete(post_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()
    return index()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('signup.html')


if __name__ == '__main__':
    create_table_posts()
    create_table_users()
    app.run(debug=True)