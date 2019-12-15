from question import Question


class Quiz:
    def __init__(self):
        self.questions = []
        self.score = 0

    def set_questions(self, questions):
        self.questions = questions

    def set_score(self, score):
        self.score = score

    def get_questions(self):
        return self.questions

    def get_score(self):
        return self.score

    def add_question(self, text, a1, a2, a3, a4, right_a):
        question = Question()
        question.set_text(text)
        question.set_options([a1, a2, a3, a4])
        question.set_right_answer(right_a)
        self.questions.append(question)
