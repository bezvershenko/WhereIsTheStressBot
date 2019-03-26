from database.SQLighter import SQLighter

db_worker = SQLighter('tasks.db')
db_worker_2 = SQLighter('tasks2.db')

all_1 = db_worker.select_all()

all_2 = db_worker_2.select_all()

for elem in all_2:
    if elem not in all_1:
        db_worker.add_task(*elem)
    else:
        print('ъеъ')

db_worker.close()
db_worker_2.close()