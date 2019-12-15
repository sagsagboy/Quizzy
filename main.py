# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request
from database import Database
from question import Question
from quiz import Quiz

# create the application object
app = Flask(__name__)
DB = Database()
this_quiz = Quiz()
this_quiz.add_question("what is my name?", "sagi", "yam", "shachar", "roy", "1")
this_quiz.add_question("what is my age", "11", "13", "15", "17", "4")
index = 0


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
        if '@' not in request.form['email']:
            error = 'Invalid email. Please try again.'
        else:
            DB.add_user(request.form['username'], request.form['password'], request.form['email'])
            return redirect(url_for('home'))
    return render_template('signup.html', error=error)


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
    app.run(debug=True, host='0.0.0.0')
