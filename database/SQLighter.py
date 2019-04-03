import sqlite3


class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def select_all(self, table):
        with self.connection:
            return self.cursor.execute(f'SELECT * FROM {table}').fetchall()

    def add_task(self, word, o1, o2, correct):
        self.cursor.execute("INSERT INTO tasks (word, option_1, option_2, correct)"
                            " VALUES (?, ?, ?, ?)", (word, o1, o2, correct))

        self.connection.commit()

    def delete_user(self, uid):
        self.cursor.execute('DELETE FROM users WHERE userId=?', (uid,))
        self.connection.commit()

    def add_user(self, userid, username):
        self.cursor.execute("INSERT INTO users (userId, username, value)"
                            " VALUES (?, ?, ?)", (userid, username, 0))
        self.connection.commit()

    def change_value_user(self, uid, upd):
        self.cursor.execute(f"UPDATE users SET value = value + {upd} WHERE userId=?", (uid,))
        self.connection.commit()

    def close(self):
        self.connection.close()

