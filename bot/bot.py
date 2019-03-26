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

TOKEN, DATABASE_NAME = environ['TOKEN'], environ['DATABASE_NAME']
ENTER_USERNAME = range(1)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)
    bot.send_message(191038878, text='Update "{}" caused error "{}"'.format(update, error))


def start(bot, update, chat_data):
    user = 'id: {}\nusername: {}\nfirst_name: {}\nlast_name: {}'.format(
        update.message.from_user.id, update.message.from_user.username,
        update.message.from_user.first_name, update.message.from_user.last_name
    )
    bot.send_message(191038878, text='Бота запустил:\n{}'.format(user))

    update.message.reply_text(
        'Привет! Это первый запуск бота! Тестируемся!'
        'Ввведи свой никнейм:'
    )

    return ENTER_USERNAME


def enter_username(bot, update, user_data):
    user = update.message.from_user
    username = update.message.text

    db_worker = SQLighter(DATABASE_NAME)
    db_worker.add_user(user.id, username)
    db_worker.close()



def finish(bot, update, chat_data):
    update.message.reply_text(
        'Игра закончена! Ты отгадал {}/{} песен!'.format(chat_data['result'], chat_data['len']),
        reply_markup=ReplyKeyboardMarkup([['/restart']]))
    return


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_error_handler(error)

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True)],

        states={
            ENTER_USERNAME: [MessageHandler(Filters.text, enter_name, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('restart', start, pass_user_data=True)]
    )
    dp.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
