class Question(object):  # class that contains a question, 4 options and the index of the right answer
    question_number = 10

    def __init__(self):
        self.text = ""
        self.options = []
        self.right_answer = 0
        Question.question_number += 10

    def set_text(self, text):
        self.text = text

    def set_options(self, options):
        self.options = options

    def set_right_answer(self, right_answer_num):
        self.right_answer = right_answer_num

    def get_text(self):
        return self.text

    def get_options(self):
        return self.options

    def get_right_answer(self):
        return self.right_answer
