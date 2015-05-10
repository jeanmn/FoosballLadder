# all the imports
import sqlite3
import MySQLdb
from flask import Flask, request, session, g, redirect, url_for, \
             abort, render_template, flash, make_response
from contextlib import closing
from operator import itemgetter
from datetime import datetime
import os

from math_ import update_rating, expected_score, boX_expected_score

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

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
    LOCAL = True   # TODO Automate
    if LOCAL:
        return MySQLdb.connect(
            host='localhost',
            user='root',
            passwd='fibo112358',
            db='foosballladder'
        )
    else:
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

def update_with_ES(D):
    username = session.get('username')
    cur = g.db.cursor()
    cur.execute('select points from entries where name="{}"'.format(username))
    (user_points,) = cur.fetchone()

    if user_points != D['points']:
        ES = expected_score(user_points, D['points'])
        res = round(boX_expected_score(ES, X=15), 2)
        if ES > 0.5:
            D['ES'] = '(Expected Win: 8 - {})'.format(res)
        else:
            D['ES'] = '(Expected Loss: {} - 8)'.format(res)

    return D

@app.route('/')
def main_page():
    cur = g.db.cursor()
    cur.execute('select name, points from entries order by points desc')
    entries_ = [dict(
        name=row[0],
        points=row[1],
    ) for row in cur.fetchall()]
    if session.get('logged_in'):
        entries = map(
            update_with_ES,
            entries_
        )
    else:
        entries = entries_

    cur.close()
    return render_template('show_entries.html', entries=entries, intround=lambda x: int(round(x)))



@app.route('/add_score', methods=['GET', 'POST'])
def add_score():
    if not session.get('logged_in'):
        abort(401)
    try:
        loser = session['username']
        winner, loser_res_str, winner_res_str = itemgetter(
            'winner', 'loser_res', 'winner_res'
        )(request.form)
        loser_res = int(loser_res_str)
        winner_res = int(winner_res_str)
        if not winner_res > loser_res:
            flash('Incorrect entry! winner_res <= loser_res')
            return redirect(url_for('main_page'))
        if winner == loser:
            flash('Incorrect entry! winner==loser')
            return redirect(url_for('main_page'))

        cur = g.db.cursor()
        cur.execute(
            'select points, K, n_games from entries where name="{}"'.format(loser)
        )
        (loser_points_before, loser_K, loser_n_games), = cur.fetchall()
        cur.close()
        cur = g.db.cursor()
        cur.execute(
            'select points, K, n_games from entries where name="{}"'.format(winner)
        )
        (winner_points_before, winner_K, winner_n_games), = cur.fetchall()

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
            'insert into results (winner, loser, winner_points_before, loser_points_before, winner_points_after, loser_points_after, winner_res, loser_res, date_) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (
                winner, loser,
                winner_points_before, loser_points_before,
                new_winner_rating, new_loser_rating,
                winner_res, loser_res,
                datetime.now().date())
        )

        flash('Winner ({}): {} -> {}'.format(
            winner,
            int(round(winner_points_before)),
            int(round(new_winner_rating)),
        ))
        flash('Loser ({}): {} -> {}'.format(
            loser,
            int(round(loser_points_before)),
            int(round(new_loser_rating)),
        ))

        g.db.commit()
        cur.close()
        flash('New entry was successfully posted')
    except Exception as e:
        flash('Undhandled error: {}'.format(e))
    return redirect(url_for('main_page'))
   # return render_template('show_entries.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
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
    except Exception as e:
        flash('Unhandled error', e)
        return redirect(url_for('main_page'))

@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    try:
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
                session['logged_in'] = True
                session['username'] = username
                flash('You were logged in as {}'.format(username))
                return redirect(url_for('main_page'))
        return render_template('newuser.html', error=error)
    except Exception as e:
        flash('Unhandled error', e)
        return redirect(url_for('main_page'))

@app.route('/watch_plot')
def watch_plot():
    try:
        print('WATCH PLOT')
        if not session.get('logged_in'):
            abort(401)

        return render_template('watch_plot.html')
    except Exception as e:
        flash('Unhandled error', e)
        return redirect(url_for('main_page'))

@app.route('/plot.png')
def plot_stuff():
    from matplotlib import pyplot as plt
    import StringIO
    cur = g.db.cursor()
    cur.execute('select winner, loser, winner_points_after, loser_points_after, winner_points_before, loser_points_before, date_ from results where (winner="{}" or loser="{}")'.format(
        session['username'], session['username']    
    ))
    entries = [
        dict(
            winner=row[0],
            loser=row[1],
            winner_points_after=row[2],
            loser_points_after=row[3],
            winner_points_before=row[4],
            loser_points_before=row[5],
            date_=row[6],
        ) for row in cur.fetchall()
    ]
    filtered_entries = filter(
        lambda entry: entry['winner_points_after'] != None,
        entries
    )  # TODO Fix this with the SQL statement instead
    temp = [entry['winner'] for entry in filtered_entries]
    def take_point(entry):
        if entry['winner'] == session['username']:
            if entry['winner_points_after'] != None:
                point = entry['winner_points_after']
            else:
                point = entry['winner_points_before']
        else:
            if entry['loser_points_after'] != None:
                point = entry['loser_points_after']
            else:
                point = entry['loser_points_before']
        print(entry.keys())
        date = entry['date_']
        return point, date

    print(filtered_entries)
    print(temp)
    points, dates = zip(*map(take_point, filtered_entries))

    plt.clf()
    plt.plot(dates, points, marker='*')
    figure = plt.gcf()
    figure.set_size_inches(6, 4)
    canvas = FigureCanvas(figure)
    output = StringIO.StringIO()
    canvas.print_png(output, dpi=100)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route('/watch_history')
def watch_history():
    try:
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
                winner_change=(row[8] - row[3]) if row[8] else 'N/A',
                loser_change=(row[9] - row[4]) if row[9] else 'N/A',
            ) for row in cur.fetchall()
        ]  # TODO This can be smoothened up quite a bit
        cur.close()

        return render_template('watch_history.html', entries=entries)
    except Exception as e:
        flash('Unhandled error', e)
        return redirect(url_for('main_page'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('main_page'))

if __name__ == '__main__':
    #init_db()  # NOTE Needs to be used first time. Initializes and resets db
    app.run(debug=True)
