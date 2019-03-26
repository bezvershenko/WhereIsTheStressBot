from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, DispatcherHandlerStop
from database.SQLighter import *
import logging
from random import shuffle, choice
from telegram import ReplyKeyboardMarkup
from time import sleep
from os import environ

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TOKEN, DATABASE_NAME = environ['token'], environ['database_name']
PLAY, FINISH, END = range(3)

RIGHT_ANSWERS = [
    'Правильно!', 'Ты угадал!', 'Точно!',
    'А ты разбираешься в музыке!', 'Молодец, угадал!'
]

WRONG_ANSWERS = [
    'Ты ошибся. Правильный ответ: ',
    'А вот и нет! Правильный ответ: ',
    'Ошибочка! Праивльный ответ: ',
    'Не угадал! Праивльный ответ: ',
    'Почти, но нет. Праивльный ответ: '
]


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)
    bot.send_message(191038878, text='Update "{}" caused error "{}"'.format(update, error))


def start(bot, update, chat_data):
    user = 'id: {}\nusername: {}\nfirst_name: {}\nlast_name: {}'.format(
        update.message.from_user.id, update.message.from_user.username,
        update.message.from_user.first_name, update.message.from_user.last_name
    )
    bot.send_message(191038878, text='Игру начал:\n{}'.format(user))

    update.message.reply_text(
        'Привет! Давай сыграем с тобой в "Угадай за 10 секунд". '
        'Суть игры проста: я присылаю десятисекундую часть песни '
        'и предлагаю 4 варианта ответа, твоя задача - угадать эту песню. Удачи:)'
    )
    db_worker = SQLighter(DATABASE_NAME)
    music = db_worker.select_all()
    db_worker.close()
    shuffle(music)
    chat_data['len'] = len(music)
    chat_data['music'] = iter(music)
    chat_data['result'] = 0
    send(bot, update, chat_data)
    return PLAY


def answer_checking(bot, update, chat_data):
    n, file, right_answer, wrong_answers = chat_data['current']
    print(update.message.text)
    if update.message.text == 'Завершить игру':
        return finish(bot, update, chat_data)
    elif update.message.text == right_answer:
        print('Угадано')
        update.message.reply_text(choice(RIGHT_ANSWERS))
        chat_data['result'] += 1
        sleep(2)
    else:
        print('Не угадал')
        update.message.reply_text(choice(WRONG_ANSWERS) + right_answer)
        sleep(2)
    send(bot, update, chat_data)


def send(bot, update, chat_data):
    try:
        current = next(chat_data['music'])
        chat_data['current'] = current
        update.message.reply_voice(current[1], reply_markup=generate_markup(current[2], current[3]))
    except StopIteration:
        finish(bot, update, chat_data)


def finish(bot, update, chat_data):
    update.message.reply_text(
        'Игра закончена! Ты отгадал {}/{} песен!'.format(chat_data['result'], chat_data['len']),
        reply_markup=ReplyKeyboardMarkup([['/restart']]))
    return


def generate_markup(right_answer, wrong_answers):
    all_answers = '{},{}'.format(right_answer, wrong_answers).split(',')
    shuffle(all_answers)
    keyboard = [[elem] for elem in all_answers] + [['Завершить игру']]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('send', send, pass_chat_data=True))
    dp.add_error_handler(error)
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_chat_data=True)],
        states={
            PLAY: [MessageHandler(Filters.text, answer_checking, pass_chat_data=True)]
        },
        fallbacks=[CommandHandler('restart', start, pass_chat_data=True)]
    )
    dp.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()