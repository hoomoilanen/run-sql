import psycopg2
import config
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
from datetime import datetime


def get_db_connection():
    con = psycopg2.connect(**config.config())
    return con

#


def get_post(post_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM posts WHERE id = %s',
                        (post_id,))
    post = cur.fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post


app = Flask(__name__)
app.config['SECRET_KEY'] = 'do_not_touch_or_you_will_be_fired'


# this function is used to format date to a finnish time format from database format
# e.g. 2021-07-20 10:36:36 is formateed to 20.07.2021 klo 10:36
def format_date(post_date):
    isodate = post_date.replace(' ', 'T')
    newdate = datetime.fromisoformat(isodate)
    return newdate.strftime('%d.%m.%Y') + ' klo ' + newdate.strftime('%H:%M')


# this index() gets executed on the front page where all the posts are
@app.route('/')
def index():
    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM posts')
    posts=cursor.fetchall()
    con.close()
    # we need to iterate over all posts and format their date accordingly
    dictrows = []
    for post in posts:
        # using our custom format_date(...)
        dictrows.append({'id': post[0], 'created': post[1], 'title': post[2], 'content': post[3]})


    return render_template('index.html', posts=dictrows)


# here we get a single post and return it to the browser
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    posts = {'id': post[0], 'created': post[1], 'title': post[2], 'content': post[3]}
    return render_template('post.html', post=posts)


# here we create a new post
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            con = get_db_connection()
            cursor = con.cursor()
            cursor.execute('INSERT INTO posts (title, content) VALUES (%s, %s)',
                         (title, content))
            con.commit()
            con.close()
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            con = get_db_connection()
            cursor = con.cursor()
            cursor.execute('UPDATE posts SET title = %s, content = %s'
                         ' WHERE id = %s',
                         (title, content, id))
            con.commit()
            con.close()
            return redirect(url_for('index'))

    return render_template('edit.html', post={'id': post[0], 'created': post[1], 'title': post[2], 'content': post[3]})


# Here we delete a SINGLE post.
@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    post = get_post(id)
    con = get_db_connection()
    t = (id,)
    cursor = con.cursor()
    cursor.execute('DELETE FROM posts WHERE id = %s', t)
    con.commit()
    con.close()
    flash('"{}" was successfully deleted!'.format(post[2]))
    return redirect(url_for('index'))
