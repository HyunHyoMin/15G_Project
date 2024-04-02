from flask import Flask, request, redirect, render_template, abort
import sqlite3
from models import create_table_comments, create_table_posts, create_table_users
from datetime import datetime

app = Flask(__name__)

now = datetime.now()
date = now.strftime('%Y-%m-%d %H:%M')
DATABASE = 'database.db'

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id, title, date FROM posts ORDER BY date DESC")  # 날짜순으로 내림차순 정렬
    posts = cur.fetchall()
    conn.close()

    # 등록된 날짜와 시간을 datetime 객체로 변환합니다.
    formatted_posts = [(post[0], post[1], datetime.strptime(post[2], '%Y-%m-%d %H:%M')) for post in posts]

    # 시간이 같은 경우 먼저 등록된 게시글이 아래로 가도록 정렬합니다.
    sorted_posts = sorted(formatted_posts, key=lambda x: (x[2], x[0]), reverse=True)

    return render_template('index.html', posts=sorted_posts)


@app.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'POST' and request.form['btn'] == '1':
        title = request.form['title']
        content = request.form['content']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("INSERT INTO posts (title, content, date) VALUES (?, ?, ?)", (title, content, date))
        conn.commit()
        new_post_id = cur.lastrowid
        conn.close()
        return redirect(f'/post/{new_post_id}')
    elif request.method == 'POST' and request.form['btn'] == '0':
        return index()
    return render_template('create.html')

@app.route('/post/<int:post_id>', methods=['GET'])
def post(post_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cur.fetchone()
    cur.execute("SELECT * FROM comments WHERE post_id = ?", (post_id,))
    comments = cur.fetchall()
    conn.close()

    # 게시글이 없을 경우 404 에러 반환
    if not post:
        abort(404)

    return render_template('post.html', post=post, comments=comments)

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

@app.route('/delete/<int:post_id>', methods=['POST'])  # 메소드를 POST로 변경
def delete(post_id):
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("DELETE FROM posts WHERE id=?", (post_id,))
        cur.execute("DELETE FROM comments WHERE post_id=?", (post_id,))
        conn.commit()
        conn.close()
        return redirect('/')
    else:
        return "Method Not Allowed", 405  # 잘못된 메소드를 수신할 경우 에러 코드 405를 반환

@app.route('/comment/<int:post_id>', methods=['GET'])
def view_comments(post_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM comments WHERE post_id = ?", (post_id,))
    comments = cur.fetchall()
    conn.close()
    return render_template('comments.html', comments=comments, post_id=post_id)

@app.route('/create_comment/<int:post_id>', methods=['POST'])
def create_comment(post_id):
    comment_text = request.form['comment']
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("INSERT INTO comments (post_id, comment, date) VALUES (?, ?, ?)", (post_id, comment_text, date))
    conn.commit()
    conn.close()
    return redirect(f'/post/{post_id}')

@app.route('/delete_comment/<int:comment_id>', methods=['GET'])
def delete_comment(comment_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer)

@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
def edit_comment(comment_id):
    if request.method == 'POST':
        new_comment_text = request.form['comment']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("UPDATE comments SET comment = ? WHERE id = ?", (new_comment_text, comment_id))
        conn.commit()
        conn.close()
        return redirect(request.referrer)
    else:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
        comment = cur.fetchone()
        conn.close()
        return render_template('edit_comment.html', comment_id=comment[0], comment_text=comment[2])

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        re_password = request.form['re_password']
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT username FROM users")
        existing_usernames = [row[0] for row in cur.fetchall()]
        if username in existing_usernames:
            conn.close()
            return '''
                <script> alert("해당 ID가 이미 존재합니다.");
                location.href="/signup"
                </script>
                '''
        if password != re_password:
            return '''
                <script> alert("비밀번호가 서로 다릅니다.");
                location.href="/signup"
                </script>
                '''
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
    return render_template('signup.html')

if __name__ == '__main__':
    create_table_posts()
    create_table_users()
    create_table_comments()
    app.run(debug=True)
