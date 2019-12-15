from question import Question
from quiz import Quiz


def main():
    this_quiz = Quiz()
    this_quiz.add_question("what is my name", "sagi", "yam", "shachar", "roy", "1")
    print(this_quiz.questions[0].get_text())
    for i in range(0, 4):
        print(str(i+1) + ")" + this_quiz.questions[0].get_options()[i])
    print("enter the number of the correct answer (1-4)")
    user_answer = input()
    while int(user_answer) >= 5:
        print("enter the number of the correct answer (1-4)")
        user_answer = input()

    if user_answer == this_quiz.questions[0].get_right_answer():
        print("good job")
        this_quiz.score += 100
        print("your score is " + str(this_quiz.score))
    else:
        print("wrong")
        print("your score is " + str(this_quiz.score))


if __name__ == "__main__":
    main()
