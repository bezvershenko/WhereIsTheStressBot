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

    def add_user(self, userid, username):
        self.cursor.execute("INSERT INTO users (userId, username, value)"
                            " VALUES (?, ?, ?)", (userid, username, 0))
        self.connection.commit()

    def inc_value_user(self, userId):
        self.cursor.execute("UPDATE users SET value = value + 1 WHERE ProductID = ?", (userId))
        self.connection.commit()


    def close(self):
        self.connection.close()
