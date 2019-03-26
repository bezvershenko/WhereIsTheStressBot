import sqlite3


class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def select_all(self):
        with self.connection:
            return self.cursor.execute('SELECT * FROM tasks').fetchall()

    def add_task(self, word, o1, o2, correct):
        self.cursor.execute("INSERT INTO tasks (word, option_1, option_2, correct)"
                            " VALUES (?, ?, ?, ?)", (word, o1, o2, correct))

        self.connection.commit()

    def close(self):
        self.connection.close()


