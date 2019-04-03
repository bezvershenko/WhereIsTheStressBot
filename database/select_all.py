from database.SQLighter import SQLighter

db_worker = SQLighter('tasks.db')


all_1 = db_worker.select_all('tasks')
print(len(set(all_1)))