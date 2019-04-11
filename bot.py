from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from database.SQLighter import *
import logging
from random import shuffle, choice
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import *

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ENTER_USERNAME, MENU, PLAY_BIG_QUIZ = range(3)

menu_keyboard = [['Большая\nвикторина📚', 'Викторина на скорость🚀'], ['Рейтинг📊', 'Очистить статистику🗑']]

RIGHT_ANSWERS = [
    'Правильно✅\n', 'Ты прав✅\n', 'Точно✅\n', 'Молодец, правильно✅\n'
]

WRONG_ANSWERS = [
    'Ты ошибся❌\nПравильный ответ: ',
    'А вот и нет❌\nПравильный ответ: ',
    'Ошибочка❌\nПравильный ответ: ',
    'Неееет❌\nПравильный ответ: ',
]


def generate_leaderboard(top, user, place):
    leadeboard = 'ТОП-10:\n\n'
    print(*zip(range(1, len(top) + 1), top))
    leadeboard += '\n'.join(
        list(map(lambda x: '{}.\t{}\t{}'.format(x[0], x[1][1][:10], x[1][2]), zip(range(1, len(top) + 1), top))))
    print(place)
    if user not in top:
        leadeboard += '\n...\n{}. {} {}'.format(place, user[1], user[2]) + '(вы)'

    return leadeboard


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)
    bot.send_message(191038878, text='Update "{}" caused error "{}"'.format(update, error))


def start(bot, update, user_data):
    user = update.message.from_user

    user_info = 'id: {}\nusername: {}\nfirst_name: {}\nlast_name: {}'.format(
        update.message.from_user.id, update.message.from_user.username,
        update.message.from_user.first_name, update.message.from_user.last_name
    )
    bot.send_message(191038878, text='Бота запустил:\n{}'.format(user_info))

    db_worker = SQLighter(DATABASE_NAME)
    all_users = db_worker.select_all('users')
    all_tasks = db_worker.select_all('tasks')

    shuffle(all_tasks)
    user_data['all_tasks'] = iter(all_tasks)
    user_data['uid'] = user.id
    user_data['streak'] = 0
    db_worker.close()

    is_registered = list(filter(lambda x: x[0] == user.id, all_users))

    if is_registered:
        update.message.reply_text(
            f'С возвращением, {is_registered[0][1]}! Готов освежить свои знания в ударениях? Тогда начинай викторину!',
            reply_markup=ReplyKeyboardMarkup(menu_keyboard)
        )

        return MENU
    else:

        update.message.reply_text(
            'Привет! Надеюсь ты уже прочитал описание бота, если нет - все просто, тренируйся в постановке ударений '
            'в формате викторины при помощи @WhereIsTheStressBot',
            reply_markup=ReplyKeyboardRemove()
        )
        update.message.reply_text(
            'Но сначала придумай себе никнейм для лидерборда (рейтинга) пользователей: ',
            reply_markup=ReplyKeyboardRemove()
        )

        return ENTER_USERNAME


def enter_username(bot, update, user_data):
    user = update.message.from_user
    username = update.message.text

    db_worker = SQLighter(DATABASE_NAME)
    user_data['username'] = username

    db_worker.add_user(user.id, username)
    db_worker.close()

    update.message.reply_text(f'Отлично, {username}, я тебя запомнил. Отправляемся в главное меню...',
                              reply_markup=ReplyKeyboardMarkup(menu_keyboard))
    return MENU


def send_next_big_quiz(bot, update, user_data):
    try:
        current_task = next(user_data['all_tasks'])
        user_data['current_task'] = current_task

        update.message.reply_text(f'Где ставится ударение в слове {current_task[0]}?',
                                  reply_markup=ReplyKeyboardMarkup([[current_task[1]], [current_task[2]], ['Вернуться '
                                                                                                           'в меню']]))
    except StopIteration:
        pass


def answer_checking_big_quiz(bot, update, user_data):
    word, o1, o2, right_answer = user_data['current_task']
    answers = [o1, o2]
    user_answer = update.message.text
    print(update.message.text)
    db_worker = SQLighter(DATABASE_NAME)

    if update.message.text == 'Вернуться в меню':
        update.message.reply_text('Возвращаемся в главное меню...', reply_markup=ReplyKeyboardMarkup(menu_keyboard))
        return MENU

    elif user_answer == answers[right_answer]:

        update.message.reply_text(choice(RIGHT_ANSWERS) + f'Следует говорить "{answers[right_answer]}"')
        user_data['streak'] += 1
        add = 1

        if user_data['streak'] % 5 == 0:
            update.message.reply_text(f"Ого, а вот и {user_data['streak']} подряд правильных ответов!")
            add = user_data['streak']

        db_worker.change_value_user(user_data['uid'], add)
        db_worker.close()
    else:
        update.message.reply_text(choice(WRONG_ANSWERS) + answers[right_answer])
        db_worker.change_value_user(user_data['uid'], -1)
        db_worker.close()
        user_data['streak'] = 0
    send_next_big_quiz(bot, update, user_data)


def main_menu(bot, update, user_data):
    text = update.message.text
    if text == menu_keyboard[0][0]:
        update.message.reply_text(
            'Большая викторина:\n1) Нет таймера\n2) Очень много заданий \n3) За '
            'правильный/неправильный ответ '
            'ты получаешь +1/-1 балл\n4) За пять правильных ответов ты получаешь +5 баллов, за десять - +10 и т.д.')
        send_next_big_quiz(bot, update, user_data)
        return PLAY_BIG_QUIZ

    elif text == menu_keyboard[0][1]:
        update.message.reply_text(
            'Приносим свои извинения, мы еще работаем над этим режимом. Совсем скоро он появится!')

    elif text == menu_keyboard[1][0]:
        db_worker = SQLighter(DATABASE_NAME)
        all_users = sorted(db_worker.select_all('users'), key=lambda x: x[2], reverse=True)
        my_result = list(filter(lambda x: x[0] == user_data['uid'], all_users))[0]
        my_place = all_users.index(my_result) + 1
        best_10_results = all_users[:10]

        update.message.reply_text(generate_leaderboard(best_10_results, my_result, my_place))
        db_worker.close()

    elif text == menu_keyboard[1][1]:
        db_worker = SQLighter(DATABASE_NAME)
        db_worker.delete_user(user_data['uid'])
        del user_data['all_tasks']
        db_worker.close()
        update.message.reply_text('Твоя статистика удалена! Для того, чтобы начать сначала - введи команду /start',
                                  reply_markup=ReplyKeyboardMarkup([['/start']]))
        return -1
    else:
        update.message.reply_text('Извини, я тебя не понимаю:(', reply_markup=ReplyKeyboardMarkup(menu_keyboard))


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_error_handler(error)

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True),
                      MessageHandler(Filters.text, start, pass_user_data=True)],

        states={
            ENTER_USERNAME: [MessageHandler(Filters.text, enter_username, pass_user_data=True)],
            MENU: [MessageHandler(Filters.text, main_menu, pass_user_data=True)],
            PLAY_BIG_QUIZ: [MessageHandler(Filters.text, answer_checking_big_quiz, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('restart', start, pass_user_data=True)]
    )
    dp.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
