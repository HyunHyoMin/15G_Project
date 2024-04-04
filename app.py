from flask import Flask, request, redirect, render_template, abort, session
import sqlite3
from models import create_table_comments, create_table_posts, create_table_users
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = '15G is secret_key'

now = datetime.now()
date = now.strftime('%Y-%m-%d %H:%M')
DATABASE = 'database.db'


@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # 날짜순으로 내림차순 정렬
    cur.execute("SELECT * FROM posts ORDER BY date DESC")
    posts = cur.fetchall()
    conn.close()

    # 등록된 날짜와 시간을 datetime 객체로 변환합니다.
    formatted_posts = [(post[0], post[1], post[2], post[3], datetime.strptime(
        post[4], '%Y-%m-%d %H:%M')) for post in posts]

    # 시간이 같은 경우 먼저 등록된 게시글이 아래로 가도록 정렬합니다.
    sorted_posts = sorted(formatted_posts, key=lambda x: (x[4], x[0]), reverse=True)
    
    if session.get("logged_in"):
        return render_template('index.html', posts=sorted_posts, logged_id=session["username"])
    
    return render_template('index.html', posts=sorted_posts)

@app.route("/login", methods=["POST"])
def login():
    login_id = request.form.get("login_id")
    login_pw = request.form.get("login_pw")
    
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT username, password FROM users WHERE username = ?", (login_id,))
    user_info = cur.fetchone()
    conn.close()
    
    if user_info and user_info[1] == login_pw:
        session['logged_in'] = True
        session['username'] = user_info[0]
        return redirect('/')
    else:
        return '''
            <script> alert("아이디 또는 비밀번호가 잘못되었습니다.");
            location.href="/"
            </script>
            '''

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect('/')

@app.route('/create/', methods=['GET', 'POST'])
def create():
    # create.html에서 글을 다 쓰고, 작성하기를 누른 경우
    if request.method == 'POST' and request.form['btn'] == '1':
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        #로그인을 하지 않은 경우
        if not session.get("logged_in"):
            username = request.form['username']
            password = request.form['password']
        #로그인을 한 경우    
        else :
            username = session["username"]
            cur.execute(
            "SELECT password FROM users WHERE username=?", (username,))
            password = cur.fetchone()[0]
        title = request.form['title']
        content = request.form['content']
        cur.execute(
            "SELECT * FROM users WHERE (username,password)=(?,?)", (username, password))
        info = cur.fetchone()
        # 입력한 계정이 유효한 경우
        if not info is None:
            cur.execute("INSERT INTO posts (username,title, content, date) VALUES (?,?,?,?)",
                        (username, title, content, date))
            conn.commit()
            new_post_id = cur.lastrowid
            conn.close()
            return redirect(f'/post/{new_post_id}')
        # 입력한 계정이 유효하지 않은(회원가입 되어 있지 않은) 경우 = Bad request
        else:
            abort(400)
    # create.html에서 뒤로가기를 누른 경우
    elif request.method == 'POST' and request.form['btn'] == '0':
        return index()
    # index.html에서 글쓰기를 누른 경우
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
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # edit.html에서 수정을 누른 경우
    if request.method == 'POST' and request.form['btn'] == '1':
        title = request.form['title']
        content = request.form['content']
        cur.execute(
            "UPDATE posts SET title = ?, content = ? WHERE id = ?", (title, content, post_id))
        conn.commit()
        conn.close()
        return redirect(f'/post/{post_id}')
    # edit.html에서 뒤로가기 누른 경우
    elif request.method == 'POST' and request.form['btn'] == '0':
        return redirect(f'/post/{post_id}')
    # post.html 에서 수정을 누른 경우    
    else:
        if not session.get("logged_in"):
                return '''
                <script> alert("수정 권한이 없습니다. 로그인을 해주세요.");
                location.href="/"
                </script>
                '''
        #로그인을 한 경우
        else :
            #로그인 정보
            username = session["username"]
            #게시글 정보
            cur.execute(
            "SELECT P.username FROM posts P INNER JOIN users U ON P.username=U.username WHERE P.id = ?", (post_id,))
            result = cur.fetchall()
            if result[0][0]==username or "admin" == session["username"]:
                cur.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
                post = cur.fetchone()
                conn.close()
                return render_template('edit.html', post=post)
            else :
                return f'''
                <script> alert("수정 권한이 없습니다.");
                location.href="/post/{post_id}"
                </script>
                '''


@app.route('/delete/<int:post_id>', methods=['POST'])  # 메소드를 POST로 변경
def delete(post_id):
    # index.html 에서 삭제하기를 누른 경우
    if request.method == 'POST':
        if request.form.get('confirm_delete') == '1':
            #로그인을 하지 않은 경우
            if not session.get("logged_in"):
                return '''
                <script> alert("삭제 권한이 없습니다. 로그인을 해주세요.");
                location.href="/"
                </script>
                '''
            #로그인을 한 경우
            else :
                conn = sqlite3.connect(DATABASE)
                cur = conn.cursor()
                username = session["username"]
                #게시글 정보
                cur.execute(
                "SELECT P.username FROM posts P INNER JOIN users U ON P.username=U.username WHERE P.id = ?", (post_id,))
                result = cur.fetchall()
                if result[0][0]==username or "admin" == session["username"]:
                    cur.execute("DELETE FROM posts WHERE id=?", (post_id,))
                    cur.execute("DELETE FROM comments WHERE post_id=?", (post_id,))
                    conn.commit()
                    conn.close()
                else :
                    return '''
                    <script> alert("삭제 권한이 없습니다.");
                    location.href="/"
                    </script>
                    '''
            return index()
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
    # comment에 내용이 있을 경우
    if comment_text:
        # 로그인을 하고 있는 경우
        if session.get("logged_in"):
            conn = sqlite3.connect(DATABASE)
            cur = conn.cursor()
            cur.execute("INSERT INTO comments (username,post_id, comment, date) VALUES (?, ?, ?, ?)",
                        (session["username"],post_id, comment_text, date))
            conn.commit()
            conn.close()
            return redirect(f'/post/{post_id}')
        else :
            return '''
                    <script> alert("댓글을 다시려면 로그인하셔야 합니다.");
                    location.href="/"
                    </script>
                    '''
    # comment가 blank인 경우
    else:
        return f'''
        <script> alert("빈 댓글은 게시할 수 없습니다");
        location.href="/post/{post_id}"
        </script>
        '''


@app.route('/delete_comment/<int:comment_id>', methods=['GET'])
def delete_comment(comment_id):
    # 로그인을 하고 있는 경우
    if session.get("logged_in"):
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT username,post_id FROM comments WHERE id = ?", (comment_id,))
        result=cur.fetchone()
        username,post_id=result[0],result[1]
        #삭제하려는 것이 본인 댓글일 때 + admin 계정일 때
        if  session["username"]==username or session["username"]=='admin':
            cur.execute("DELETE FROM comments WHERE id=?", (comment_id,))
            conn.commit()
            conn.close()
            return post(post_id)
        else :
            return f'''
            <script> alert("삭제 권한이 없습니다.");
            location.href="/post/{post_id}"
            </script>
            '''
    # 로그인 없이 삭제하려는 경우
    else :
        return '''
            <script> alert("삭제 권한이 없습니다. 로그인을 해주세요.");
            location.href="/"
            </script>
            '''

@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
def edit_comment(comment_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # edit_comment.html 에서 수정하기 눌렀을 때
    if request.method == 'POST':
        new_comment_text = request.form['comment']
        cur.execute("UPDATE comments SET comment = ? WHERE id = ?",
                    (new_comment_text, comment_id))
        cur.execute("SELECT post_id FROM comments WHERE id = ?", (comment_id,))
        post_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return post(post_id)
    # post.html 에서 EDIT을 눌렀을 때
    else:
        cur.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
        comment = cur.fetchone()
        conn.close()
        return render_template('edit_comment.html', comment_id=comment[0], comment_text=comment[2])


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()  # 공백 제거
        password = request.form['password']
        re_password = request.form['re_password']
        
        # 1. 공백칸 회원가입 불가능
        if not (username and password and re_password):
            return '''
                <script> alert("모든 항목을 입력해주세요.");
                location.href="/signup"
                </script>
                '''
        
        # 2. 이메일 형식으로만 회원가입 가능
        if not re.match(r'^[\w\.-]+@[\w\.-]+$', username):
            return '''
                <script> alert("올바른 이메일 주소를 입력해주세요.");
                location.href="/signup"
                </script>
                '''

        # 3. 비밀번호 조건
        if len(password) < 8 or not any(char.isdigit() for char in password) \
                or not any(char.islower() for char in password) \
                or not any(char.isupper() for char in password):
            return '''
                <script> alert("비밀번호는 8자 이상이어야 하며, 특수문자, 대문자, 소문자가 최소 하나씩 포함되어야 합니다.");
                location.href="/signup"
                </script>
                '''

        # 4. 회원가입 성공
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
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return '''
                <script> alert("회원가입에 성공했습니다.");
                location.href="/"
                </script>
                '''
    return render_template('signup.html')

@app.route('/search', methods=['POST'])
def search():
    search = request.form.get("search")
    search_type=request.form["search_type"]
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    # Column 명은 동적으로 할당할 수 없다고 하네요 ㅜㅜ
    if search_type == 'title':
        cur.execute("SELECT * FROM posts WHERE title LIKE ? ORDER BY date DESC", ('%' + search + '%',))
    elif search_type == 'username':
        cur.execute("SELECT * FROM posts WHERE username LIKE ? ORDER BY date DESC", ('%' + search + '%',))
    elif search_type == 'content':
        cur.execute("SELECT * FROM posts WHERE content LIKE ? ORDER BY date DESC", ('%' + search + '%',))
    search_post = cur.fetchall()
    conn.close()
    return render_template('index.html', search_post=search_post, logged_id=session["username"])

if __name__ == '__main__':
    create_table_users()
    create_table_posts()
    create_table_comments()
    app.run(debug=True)