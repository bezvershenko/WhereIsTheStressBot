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
PLAY, FINISH, END = range(3)



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
    )

    return PLAY


def answer_checking(bot, update, chat_data):
    pass



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
