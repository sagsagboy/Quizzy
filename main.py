# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request
import database
from database import User
from question import Question
from quiz import Quiz

import hashlib, binascii, os

# create the SQLalchemy engine and session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///C:\\Users\\Admin\\PycharmProjects\\Quizzy\\quizzy.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

# create the application object
app = Flask(__name__)
this_quiz = Quiz()
# this_quiz.add_question("what is my name?", "sagi", "yam", "shachar", "roy", "1")
# this_quiz.add_question("what is my age", "11", "13", "15", "17", "4")
index = 0


def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    pwdhash = pwdhash.decode('ascii')
    salt = salt.decode('ascii')
    return pwdhash, salt

# use decorators to link the function to a url
@app.route('/')
def home():
    return render_template('home.html')  # return a string


@app.route('/welcome')
def welcome():
    return render_template('welcome.html')  # render a template


@app.route('/crate', methods=['GET', 'POST'])
def crate_quiz():
    if request.method == 'POST':
        this_quiz.add_question(request.form['Question'],
                               request.form['answer1'],
                               request.form['answer2'],
                               request.form['answer3'],
                               request.form['answer4'],
                               request.form['answers'])
    return render_template('crate_quiz.html')


# Route for handling the login page logic
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        exists = session.query(User.Name).filter_by(Name=request.form['username']).scalar() is not None
        print(exists)
        if exists:
            error = 'username already exist please choose another one'
        else:
            passhash, salt = hash_password(request.form['password'])
            ps = User(Name=request.form['username'], Passhash=passhash, Salt=salt)
            session.add(ps)
            session.commit()
            return redirect(url_for('home'))
    return render_template('signup.html', error=error)


''''@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':


    return render_template('login.html', error=error'''


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
