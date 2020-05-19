# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request, make_response
from threading import Lock
import uuid
from database import *
from quiz import Quiz

from sqlalchemy.sql import select
from sqlalchemy import update

import hashlib
import binascii
import os

# create the SQLalchemy engine and session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///quizzy.db?check_same_thread=False', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
DbMutex = Lock()

# create the application object
app = Flask(__name__)
this_quiz = Quiz()
index = 0


def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
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


@app.route('/welcome')
def welcome():
    return render_template('welcome.html')  # render a template


@app.route('/crate', methods=['GET', 'POST'])
def crate_quiz():
    user_name = request.cookies.get('user')
    #session_hash = request.cookies.get('session')
    exists = session.query(User.Name).filter_by(Name=user_name).scalar() is not None
    if exists:
        if request.method == 'POST':
            new_question = Question(text=request.form['Question'],option1=request.form['answer1'],
                                    option2=request.form['answer2'],option3=request.form['answer3'],
                                    option4=request.form['answer4'],RightAnswer=request.form['answers'])
            with DbMutex:
                session.add(new_question)
                session.commit()

    else:
        return ("You need to login to an account or create a new one to create a quiz")

    return render_template('crate_quiz.html')


# Route for handling the login page logic
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        exists = session.query(User.Name).filter_by(Name=request.form['username']).scalar() is not None
        if exists:
            error = 'username already exist please choose another one'
        else:
            passhash, salt = hash_password(request.form['password'])
            ps = User(Name=request.form['username'], Passhash=passhash, Salt=salt)
            with DbMutex:
                session.add(ps)
                session.commit()
            return redirect(url_for('home'))
    return render_template('signup.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        my_user = session.query(User).filter_by(Name=request.form['username']).first()
        user_pass = my_user.Passhash
        salt = my_user.Salt
        given_pass = request.form['password']
        same_pass = verify_password(user_pass, salt, given_pass)
        if same_pass:
             session_hash = uuid.uuid4()
             print(session_hash)
             with DbMutex:
                my_user.sessionHash = str(session_hash)
                session.commit()
             resp = make_response(redirect(url_for('home')))
             resp.set_cookie("user", request.form['username'])
             resp.set_cookie("session",  str(session_hash))
             return resp
        else:
            error = 'username or password may be incorrect'
    return render_template('login.html', error=error)


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    global index
    print("lol " + str(index))
    if request.method == 'POST':
        answer = request.form['answers']
        if answer == this_quiz.questions[index].get_right_answer():
            this_quiz.score += 100
        index += 1
    print("seemek " + str(index))
    if len(this_quiz.questions) <= index:
        index = 0
        return ("Your score is " + str(this_quiz.get_score()))
    print(index)
    return render_template('quiz.html', question_site=this_quiz.questions[index].get_text(),
                           answer1_site=this_quiz.questions[index].get_options()[0],
                           answer2_site=this_quiz.questions[index].get_options()[1],
                           answer3_site=this_quiz.questions[index].get_options()[2],
                           answer4_site=this_quiz.questions[index].get_options()[3])


# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True,)
