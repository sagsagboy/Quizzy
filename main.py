# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request, make_response, flash
from threading import Lock
import uuid
from database import *


from sqlalchemy.sql import select
from sqlalchemy import update

import hashlib
import binascii
import os
import random

# create the SQLalchemy engine and session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    'sqlite:///quizzy.db?check_same_thread=False', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
DbMutex = Lock()

# create the application object
app = Flask(__name__)


def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac(
        'sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    pwdhash = pwdhash.decode('ascii')
    salt = salt.decode('ascii')
    return pwdhash, salt


def verify_password(stored_password, salt, provided_password):
    """Verify a stored password against one provided by user"""
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


# use decorators to link the function to a url
@app.route('/')
def home():
    return render_template('home.html')  # return a string


@app.route('/quiz/select', methods=['GET'])
def select_quiz():
    user_name = request.cookies.get('user')
    exists = session.query(User.Name).filter_by(
        Name=user_name).scalar() is not None
    if exists:
        all_quizs = session.query(Game).filter_by(OwnerID=user_name).all()
        all_quiz_names = []
        for i in range(0, len(all_quizs)):
            all_quiz_names.append(all_quizs[i].Name)
        return render_template('select_quiz.html', all_quiz_names=all_quiz_names)

    else:
        return ("You need to login to an account or create a new one to create a quiz")


@app.route('/quiz/<quiz_name>', methods=['GET', 'POST'])
def run_quiz(quiz_name):
    def this_sess(x):
        return session.query(x)

    exists = this_sess(Game.Name).filter_by(
        Name=quiz_name).scalar() is not None
    if not exists:
        return ("<H1>this quiz does not exists</H1>")

    # Create game pin and make sure it doesnt already exist
    game_pin = random.randrange(1e3, 1e4 - 1)
    while game_pin in session.query(GameRun.gamePin).all():
        game_pin = random.randrange(1e3, 1e4 - 1)

    # Create GameRun database
    game_ids = this_sess(Game.ID).filter_by(Name=quiz_name).all()
    assert len(game_ids) == 1, 'There are two quizes with the same name. WTF.'
    game_id = int(game_ids[0][0])
    this_game = GameRun(gamePin=str(game_pin), Name=quiz_name, Status='True',
                        gameID=game_id, nextQTime=20, CurrQustion=0)
    with DbMutex:
        session.add(this_game)
        session.commit()
    return render_template('run_quiz.html', game_pin=game_pin)


@app.route('/quiz/start/<game_pin>', methods=['GET', 'POST'])
def start_screen_quiz(game_pin):
    if request.method == 'POST':
        game_runs_id = session.query(GameRun.gameID).filter_by(gamePin=game_pin).first()[0]
        question_id = session.query(Question.ID).filter_by(gameID=game_runs_id).first()[0]
        return redirect(url_for('in_game_host', game_pin=game_pin, question_id=question_id))
    players = session.query(userScore.nickName).filter_by(gameRunsID=game_pin)
    return render_template('start_screen.html', all_players=players)


@app.route('/quiz/start/<game_pin>/<question_id>', methods=['GET', 'POST'])
def in_game_host(game_pin, question_id):
    if request.method == 'POST':
        this_question_game_id = session.query(Question.gameID).filter_by(ID=question_id).first()
        next_question_id = int(question_id) + 1
        next_question_game_id = session.query(Question.gameID).filter_by(ID=next_question_id).first()
        if this_question_game_id == next_question_game_id:
            return redirect(url_for('in_game_host', game_pin=game_pin, question_id=str(int(question_id) + 1)))
        else:
            return redirect(url_for('leaderboard',game_pin=game_pin))

    question = session.query(Question.text).filter_by(ID=question_id).first()[0]
    questions = [Question.option1, Question.option1, Question.option3, Question.option4]
    a = [session.query(q).filter_by(ID=question_id).first()[0] for q in questions]

    return render_template('in_game_host.html', question=question, a=a)


@app.route('/quiz/leaderboard/<game_pin>')
def leaderboard(game_pin):
    if request.method == 'POST':
        return redirect(url_for('home'))
    players = session.query(userScore.nickName).filter_by(gameRunsID=game_pin).all()
    return render_template('leaderboard.html', all_players=players)


@app.route('/connect', methods=['GET', 'POST'])
def connect():
    if request.method == 'POST':
        game_pin = request.form['gamepin']
        nick_name = request.form['name']
        user_score = userScore(nickName=nick_name, gameRunsID=str(game_pin), score=0)
        with DbMutex:
            session.add(user_score)
            session.commit()
        resp = make_response(redirect(url_for('wait')))
        resp.set_cookie("nick_name", nick_name)
        return resp
    return render_template('connect.html')


@app.route('/connect/wait', methods=['GET', 'POST'])
def wait():
    if request.method == 'POST':
        nick_name = request.cookies.get('nick_name')
        game_runs_pin = session.query(userScore.gameRunsID).filter_by(nickName=nick_name).first()[0]
        game_runs_id = session.query(GameRun.gameID).filter_by(gamePin=game_runs_pin).first()[0]
        question_id = session.query(Question.ID).filter_by(gameID=game_runs_id).first()[0]
        return redirect(url_for('in_game_player', game_pin=game_runs_pin, question_id=question_id))
    return render_template('wait.html')


@app.route('/quiz/game/<game_pin>/<question_id>', methods=['GET', 'POST'])
def in_game_player(game_pin, question_id):
    if request.method == 'POST':
        answer = int(request.form['answers'])
        right_answer = int(session.query(Question.RightAnswer).filter_by(ID=question_id).first()[0])

        nickName = request.cookies.get('nick_name')
        player_answer = userAnswers(nickName=nickName, questionID=question_id, gameRunsID=game_pin, time=0,
                                    answer=answer)
        with DbMutex:
            session.add(player_answer)
            session.commit()
        res = redirect(
            url_for('in_game_wait_player', game_pin=game_pin, question_id=question_id, correct=answer == right_answer))
        if answer == right_answer:
            my_player = session.query(userScore).filter_by(nickName=nickName).first()
            my_player_score = my_player.score
            my_player_score += 1
            with DbMutex:
                my_player.score = my_player_score
                session.commit()
            print('Correct answer!!')
        this_question_game_id = session.query(Question.gameID).filter_by(ID=question_id).first()
        next_question_id = int(question_id) + 1
        next_question_game_id = session.query(Question.gameID).filter_by(ID=next_question_id).first()
        if this_question_game_id == next_question_game_id:
            return res
        else:
            score = session.query(userScore.score).filter_by(nickName=nickName).first()[0]
            score = score * 100
            return "you finished the quiz your score is " + str(score)

    question = session.query(Question.text).filter_by(ID=question_id).first()[0]
    questions = [Question.option1, Question.option1, Question.option3, Question.option4]
    a = [session.query(q).filter_by(ID=question_id).first()[0] for q in questions]

    return render_template('in_game_player.html', question=question, a=a)


@app.route('/quiz/game-wait/<game_pin>/<question_id>/<correct>', methods=['GET', 'POST'])
def in_game_wait_player(game_pin, question_id, correct):
    if request.method == 'POST':
        return redirect(url_for('in_game_player', game_pin=game_pin, question_id=str(int(question_id) + 1)))
    message = 'You got it right!🎉' if correct == 'True' else 'Lol noob 😎'
    return render_template('wait_for_next_question.html', question=question_id, message=message)
    # Once finished waiting, go to /quiz/game/<game_pin>/(<question_id> +1)


@app.route('/create/name', methods=['GET', 'POST'])
def crate_quiz_name():
    user_name = request.cookies.get('user')
    exists = session.query(User.Name).filter_by(
        Name=user_name).scalar() is not None
    if exists:
        if request.method == 'POST':
            new_quiz = Game(Name=request.form['quizName'], OwnerID=user_name)
            with DbMutex:
                session.add(new_quiz)
                session.commit()
            return redirect(url_for('create_quiz_question'))
    else:
        return ("You need to login to an account or create a new one to create a quiz")
    return render_template('create_quiz_name.html')


@app.route('/create/question', methods=['GET', 'POST'])
def create_quiz_question():
    user_name = request.cookies.get('user')
    exists = session.query(User.Name).filter_by(
        Name=user_name).scalar() is not None
    if exists:
        if request.method == 'POST':
            my_quiz = session.query(Game).filter_by(OwnerID=user_name).all()
            print(my_quiz)
            my_quiz = my_quiz[-1]
            quiz_ID = my_quiz.ID
            new_question = Question(text=request.form['Question'], option1=request.form['answer1'],
                                    option2=request.form['answer2'], option3=request.form['answer3'],
                                    option4=request.form['answer4'], RightAnswer=request.form['answers'],
                                    gameID=quiz_ID)
            with DbMutex:
                session.add(new_question)
                session.commit()
            return redirect(url_for('create_quiz_question'))
    else:
        return ("You need to login to an account or create a new one to create a quiz")

    return render_template('create_quiz_question.html')


# Route for handling the login page logic
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        exists = session.query(User.Name).filter_by(
            Name=request.form['username']).scalar() is not None
        if exists:
            error = 'username already exist please choose another one'
        else:
            passhash, salt = hash_password(request.form['password'])
            ps = User(Name=request.form['username'],
                      Passhash=passhash, Salt=salt)
            with DbMutex:
                session.add(ps)
                session.commit()
            return redirect(url_for('home'))
    return render_template('signup.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        my_user = session.query(User).filter_by(
            Name=request.form['username']).first()
        user_pass = my_user.Passhash
        salt = my_user.Salt
        given_pass = request.form['password']
        same_pass = verify_password(user_pass, salt, given_pass)
        if same_pass:
            session_hash = uuid.uuid4()
            with DbMutex:
                my_user.sessionHash = str(session_hash)
                session.commit()
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie("user", request.form['username'])
            resp.set_cookie("session", str(session_hash))
            return resp
        else:
            error = 'username or password may be incorrect'
    return render_template('login.html', error=error)


# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
