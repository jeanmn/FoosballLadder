# all the imports
import sqlite3
import MySQLdb
from flask import Flask, request, session, g, redirect, url_for, \
             abort, render_template, flash
from contextlib import closing
from operator import itemgetter
from datetime import datetime
import os

from math_ import update_rating

# configuration
DATABASE = os.path.join(os.path.expanduser('~'), 'FoosballLadder/db/Ladder.db')
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
#    return sqlite3.connect(app.config['DATABASE'])
    return MySQLdb.connect(
        host='mysql.server',
        user='foosballladder',
        passwd='dendi',
        db='foosballladder$default'
    )

def init_db():  # TODO Is this right for online? probably not...
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def main_page():
    cur = g.db.cursor()
    cur.execute('select name, points from entries order by points desc')
    entries = [dict(name=row[0], points=row[1]) for row in cur.fetchall()]
    cur.close()
    return render_template('main_page.html', entries=entries)



@app.route('/add_score', methods=['GET', 'POST'])
def add_score():
    if not session.get('logged_in'):
        abort(401)
    loser = session['username']
    winner, loser_res_str, winner_res_str = itemgetter(
        'winner', 'loser_res', 'winner_res'
    )(request.form)
    loser_res = int(loser_res_str)
    winner_res = int(winner_res_str)
    if not winner_res > loser_res:
        flash('Incorrect entry!')
        return redirect(url_for('main_page'))

    cur = g.db.cursor()
    cur.execute(
        'select points, K, n_games from entries where name in ("{}", "{}")'.format(loser, winner)
    )
    (loser_points_before, loser_K, loser_n_games), (winner_points_before, winner_K, winner_n_games) = cur.fetchall()
    print('tjoho')

    new_winner_rating, new_loser_rating = update_rating(
        winner_points_before, loser_points_before,
        winner_K, loser_K,
        winner_res, loser_res
    )

    cur.execute(
        'update entries set points=(%s) where name="{}"'.format(winner),
        (new_winner_rating,)
    )
    cur.execute(
        'update entries set n_games=(%s) where name="{}"'.format(winner),
        (winner_n_games + 1,)
    )
    cur.execute(
        'update entries set points=(%s) where name="{}"'.format(loser),
        (new_loser_rating,)
    )
    cur.execute(
        'update entries set n_games=(%s) where name="{}"'.format(loser),
        (loser_n_games + 1,)
    )
    cur.execute(
        'insert into results (winner, loser, winner_points_before, loser_points_before, winner_res, loser_res, date_) values (%s, %s, %s, %s, %s, %s, %s)',
        (winner, loser, winner_points_before, loser_points_before, winner_res, loser_res, datetime.now().date())
    )

    g.db.commit()
    cur.close()
    flash('New entry was successfully posted')
    return redirect(url_for('main_page'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    cur = g.db.cursor()
    cur.execute(
        'select name, password from entries'
    )
    user_pws = {un: pw for (un, pw) in cur.fetchall()}
    cur.close()
    if request.method == 'POST':
        given_username = request.form['username']
        if given_username not in user_pws.keys():
            error = 'Invalid username'
        elif request.form['password'] != user_pws[given_username]:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['username'] = given_username
            flash('You were logged in as {}'.format(given_username))
            return redirect(url_for('main_page'))
    return render_template('login.html', error=error)

@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        pw = request.form['pw']
        pw_again = request.form['pw_again']
        if pw != pw_again:
            error = 'Passwords must match!'
        elif (username.encode('ascii', 'ignore') != username) or (pw.encode('ascii', 'ignore') != pw):
            error = 'Only ascii characters allowed'
        else:
            cur = g.db.cursor()
            print((str(request.form['username']), str(request.form['pw']), '1500', '40', '0'))
            cur.execute(
                'insert into entries (name, password, points, K, n_games) values (%s, %s, %s, %s, %s)',
                (str(request.form['username']), str(request.form['pw']), '1500', '40', '0')
            )
            g.db.commit()
            cur.close()
            flash('New Player! Welcome {}!'.format(username))
            return redirect(url_for('main_page'))
    return render_template('newuser.html', error=error)

@app.route('/watch_history')
def watch_history():
    print('WATCH HISTORY')
    if not session.get('logged_in'):
        abort(401)
    cur = g.db.cursor()
    cur.execute('select * from results order by id desc')
    entries = [
        dict(
            winner=row[1],
            loser=row[2],
            winner_points_before=row[3],
            loser_points_before=row[4],
            winner_res=row[5],
            loser_res=row[6],
            date_=row[7],
        ) for row in cur.fetchall()
    ]
    cur.close()

    return render_template('watch_history.html', entries=entries)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('main_page'))

if __name__ == '__main__':
    #init_db()  # NOTE Needs to be used first time. Initializes and resets db
    app.run(debug=True)
