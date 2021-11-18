import psycopg2
import config
from flask import Flask, render_template, request, url_for, flash, redirect, Response
from werkzeug.exceptions import abort
from datetime import datetime
import datetime
import logging
import os
import ssl
import sqlalchemy

def get_db_connection():
db_config = {
        # [START cloud_sql_postgres_sqlalchemy_limit]
        # Pool size is the maximum number of permanent connections to keep.
        "pool_size": 5,
        # Temporarily exceeds the set pool_size if no connections are available.
        "max_overflow": 2,
        # The total number of concurrent connections for your application will be
        # a total of pool_size and max_overflow.
        # [END cloud_sql_postgres_sqlalchemy_limit]

        # [START cloud_sql_postgres_sqlalchemy_backoff]
        # SQLAlchemy automatically uses delays between failed connection attempts,
        # but provides no arguments for configuration.
        # [END cloud_sql_postgres_sqlalchemy_backoff]

        # [START cloud_sql_postgres_sqlalchemy_timeout]
        # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
        # new connection from the pool. After the specified amount of time, an
        # exception will be thrown.
        "pool_timeout": 30,  # 30 seconds
        # [END cloud_sql_postgres_sqlalchemy_timeout]

        # [START cloud_sql_postgres_sqlalchemy_lifetime]
        # 'pool_recycle' is the maximum number of seconds a connection can persist.
        # Connections that live longer than the specified amount of time will be
        # reestablished
        "pool_recycle": 1800,  # 30 minutes
        # [END cloud_sql_postgres_sqlalchemy_lifetime]
    }


    return init_tcp_connection_engine(db_config)

def init_tcp_connection_engine(db_config):
    # [START cloud_sql_postgres_sqlalchemy_create_tcp]
    # Remember - storing secrets in plaintext is potentially unsafe. Consider using
    # something like https://cloud.google.com/secret-manager/docs/overview to help keep
    # secrets secret.
    db_user = "keijo"
    db_pass = "keijo"
    db_name = "keijo"
    db_host = "127.0.0.1"
    db_port = 5432

    pool = sqlalchemy.create_engine(
        # Equivalent URL:
        # postgresql+pg8000://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
        sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=db_user,  # e.g. "my-database-user"
            password=db_pass,  # e.g. "my-database-password"
            host=db_hostname,  # e.g. "127.0.0.1"
            port=db_port,  # e.g. 5432
            database=db_name  # e.g. "my-database-name"
        ),
        **db_config
    )
    # [END cloud_sql_postgres_sqlalchemy_create_tcp]
    pool.dialect.description_encoding = None
    return pool

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
