import sqlite3


class Database(object):
    def __init__(self):
        self._database = sqlite3.connect('sagidb.db', check_same_thread=False)
        self._cursor = self._database.cursor()
        #self._cursor.execute('''CREATE TABLE users (username text, password text, email text)''')

    def add_user(self, name, password, email):
        self._cursor.execute("INSERT INTO users VALUES(?,?,?)", (name, password, email))
        self._database.commit()
