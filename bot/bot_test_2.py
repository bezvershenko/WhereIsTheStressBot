from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

import requests

from maps_api.request import geocoder_request, map_request
from maps_api.geocoder import get_pos, get_bbox, get_country_code, get_city, check_response
from maps_api.static import get_static_map

from news_parser.parser import parse_news

from weather.weather import get_current_weather, get_forecast_weather

from schedule_api.airports import airs
from schedule_api.schedule import get_flights

from speech_api.speech_analyze import speech_analyze
from speech_api.xml_parser import speech_parser

from headhunter_api.suggestions import keywords_suggest, region_suggest
from headhunter_api import vacancies_request, full_vacancy_request

from os import environ
# from config import TELEGRAM_TOKEN, SPEECH_TOKEN, WEATHER_TOKEN
TELEGRAM_TOKEN = environ['telegram']
SPEECH_TOKEN = environ['speech']
WEATHER_TOKEN = environ['weather']

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

keyboard1 = [['↪️Пропустить']]
keyboard2 = [['🗺Показать на карте'], ['🗞Последние новости'], ['🌧Погода'], ['🛩Расписания'], ['💸Вакансии'],
             ['🔙Вернуться назад']]
keyboard3 = [['🔙Вернуться назад']]
keyboard4 = [['🌤Текущая погода'], ['☔️Прогноз на 6 дней'], ['🔙Вернуться назад']]
keyboard5 = [['✈️Найти авиарейс'], ['🔙Вернуться назад']]
keyboard6 = [['📚Сервисы для города'], ['👤Показать текущий профиль вакансий'], ['⚙Настройки профиля вакансий']]
keyboard7 = [['🔠Настройка ключевых слов'], ['🌆Настройка города'], ['🔙Вернуться назад']]

inline_news_state1 = InlineKeyboardMarkup(
    [[InlineKeyboardButton('Следующая новость▶️', callback_data=1)], [InlineKeyboardButton('🔙Назад', callback_data=3)]])

inline_news_state2 = InlineKeyboardMarkup([
    [InlineKeyboardButton('◀️Предыдущая новость', callback_data=2),
     InlineKeyboardButton('Следующая новость▶️', callback_data=1)],
    [InlineKeyboardButton('🔙Назад', callback_data=3)]
])

inline_news_state3 = InlineKeyboardMarkup([
    [InlineKeyboardButton('◀️Предыдущая новость', callback_data=2)],
    [InlineKeyboardButton('🔙Назад', callback_data=3)]
])

inline_maps = InlineKeyboardMarkup([
    [InlineKeyboardButton('🗺Карта', callback_data='map')],
    [InlineKeyboardButton('🛰Спутник', callback_data='sat')],
    [InlineKeyboardButton('🗺➕🛰Гибрид', callback_data='sat,skl')],
])

inline_sch_state1 = InlineKeyboardMarkup(
    [[InlineKeyboardButton('Следующий рейс▶️', callback_data=1)], [InlineKeyboardButton('🔙Назад', callback_data=3)]])

inline_sch_state2 = InlineKeyboardMarkup([
    [InlineKeyboardButton('◀️Предыдущий рейс', callback_data=2),
     InlineKeyboardButton('Следующий рейс▶️', callback_data=1)],
    [InlineKeyboardButton('🔙Назад', callback_data=3)]
])

inline_sch_state3 = InlineKeyboardMarkup([
    [InlineKeyboardButton('⏮Предыдущий рейс', callback_data=2)],
    [InlineKeyboardButton('🔙Назад', callback_data=3)]
])


def start(bot, update):
    update.message.reply_text(
        'Как Вас зовут?', reply_markup=ReplyKeyboardMarkup(keyboard1), one_time_keyboard=False)

    return ENTER_NAME


def enter_name(bot, update, user_data):
    name = update.message.text
    if name != '↪️Пропустить':
        user_data['username'] = name
    else:
        user_data['username'] = None

    user_data['vacancy'] = {
        'region_name': None,
        'region_id': None,
        'keywords': None
    }

    update.message.reply_text('В каком городе Вы живете?')
    return ENTER_LOCATION


def enter_location(bot, update, user_data):
    location = update.message.text

    if location != '↪️Пропустить':
        user_data['location'] = location

        suggests = region_suggest(location)
        user_data['region_suggests'] = suggests

        if len(suggests) != 0:
            location_keyboard = [['↪️Пропустить']]
            for suggestion in suggests:
                location_keyboard.append([suggestion])

            update.message.reply_text(
                'Найдено несколько регионов, соответствующих введенному.\n'
                'Выберите один из них.',
                reply_markup=ReplyKeyboardMarkup(location_keyboard)
            )

            return LOCATION_APPLY

        update.message.reply_text(
            'Данный город не найдена в базе регионов.'
        )

    else:
        user_data['location'] = None

    name = ', {}'.format(user_data['username']) if user_data['username'] is not None else ''
    update.message.reply_text('Добро пожаловать{}!'.format(name), reply_markup=ReplyKeyboardMarkup(keyboard6))

    return MAIN_MENU


def location_apply(bot, update, user_data):
    text = update.message.text

    if text in user_data['region_suggests']:
        user_data['location'] = text
        user_data['vacancy']['region_name'] = text
        user_data['vacancy']['region_id'] = user_data['region_suggests'][text]
        update.message.reply_text(
            'Город успешно установлен!'
        )

    elif text != '↪️Пропустить':
        update.message.reply_text(
            'Введенный текст не является ни одним из перечисленных регионов.\n'
            'Попробуйте ввести название региона ещё раз.'
        )
        return LOCATION_APPLY

    name = ', {}'.format(user_data['username']) if user_data['username'] is not None else ''
    update.message.reply_text('Добро пожаловать{}!'.format(name), reply_markup=ReplyKeyboardMarkup(keyboard6))
    return MAIN_MENU


def main_menu(bot, update, user_data):
    text = update.message.text

    if text == '📚Сервисы для города':
        update.message.reply_text(
            'Введите город, информацию о котором Вы хотите узнать',
            reply_markup=ReplyKeyboardMarkup(keyboard3)
        )
        return SEARCH_HANDLER

    elif text == '👤Показать текущий профиль вакансий':
        region = user_data['vacancy']['region_name']
        if region is None:
            if user_data['location'] is None:
                region = 'Не указано'
            else:
                region = 'Указанный город не найден в базе данных HeadHunter'

        keywords = user_data['vacancy']['keywords']
        if keywords is None: keywords = 'Не указано'

        update.message.reply_text(
            'Город: {}\n'
            'Ключевые слова: {}\n'.format(
                region, keywords
            )
        )

    elif text == '⚙Настройки профиля вакансий':
        update.message.reply_text(
            'Выберите параметры, которые Вы хотите настроить',
            reply_markup=ReplyKeyboardMarkup(keyboard7)
        )
        return PROFILE_CONFIG

    return MAIN_MENU


def profile_config(bot, update, user_data):
    text = update.message.text

    if text == '🔠Настройка ключевых слов':
        update.message.reply_text(
            'Введите ключевые слова, которые будут использоваться при поиске вакансий',
            reply_markup=ReplyKeyboardMarkup(keyboard3)
        )
        return KEYWORDS_CONFIG

    elif text == '🌆Настройка города':
        update.message.reply_text('Введите город, в котором ищите вакансию',
                                  reply_markup=ReplyKeyboardMarkup(keyboard1))
        return ENTER_LOCATION

    elif text == '🔙Вернуться назад':
        update.message.reply_text('Что Вы хотите сделать?', reply_markup=ReplyKeyboardMarkup(keyboard6))
        return MAIN_MENU

    return PROFILE_CONFIG


def keywords_config(bot, update, user_data):
    text = update.message.text
    suggests = keywords_suggest(text)

    if text == '🔙Вернуться назад':
        update.message.reply_text(
            'Возвращаемся в меню настроек',
            reply_markup=ReplyKeyboardMarkup(keyboard7)
        )
        return PROFILE_CONFIG

    if len(suggests) != 0:
        user_data['keywords_suggests'] = suggests

        keywords_keyboard = [['🔙Вернуться назад']]
        for suggestion in suggests:
            keywords_keyboard.append([suggestion])

        update.message.reply_text(
            'Бот нашел несколько схожих ключевых слов. Выберите одно из них',
            reply_markup=ReplyKeyboardMarkup(keywords_keyboard)
        )

        return KEYWORDS_APPLY

    else:
        user_data['vacancy']['keywords'] = text
        update.message.reply_text(
            'Ключевые слова успешно установлены! Возвращаемся в меню настроек',
            reply_markup=ReplyKeyboardMarkup(keyboard7)
        )

    return PROFILE_CONFIG


def keywords_apply(bot, update, user_data):
    text = update.message.text

    if text in user_data['keywords_suggests']:
        user_data['vacancy']['keywords'] = text
        update.message.reply_text(
            'Ключевые слова успешно установлены! Возвращаемся в меню настроек',
            reply_markup=ReplyKeyboardMarkup(keyboard7)
        )
        return PROFILE_CONFIG

    elif text == '🔙Вернуться назад':
        update.message.reply_text(
            'Возвращаемся в меню настроек',
            reply_markup=ReplyKeyboardMarkup(keyboard7)
        )
        return PROFILE_CONFIG

    else:
        update.message.reply_text(
            'Введенный текст не является ни одним из перечисленных ключевых слов.\n'
            'Попробуйте ввести ключевые слова ещё раз.'
        )

    return KEYWORDS_APPLY


def search_handler(bot, update, user_data):
    text = update.message.text

    if text == '🔙Вернуться назад':
        update.message.reply_text(
            'Возвращаемся в главное меню',
            reply_markup=ReplyKeyboardMarkup(keyboard6)
        )
        return MAIN_MENU

    response = geocoder_request(geocode=text, format='json')

    if check_response(response):
        update.message.reply_text(
            'Город определен',
            reply_markup=ReplyKeyboardMarkup(keyboard2)
        )
        update.message.reply_text('Выберите одну из возможных функций для данного города:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard2))

        user_data['current_response'] = response
        return LOCATION_HANDLER
    update.message.reply_text('Заданный город не найден.')

    return SEARCH_HANDLER


def voice_to_text(bot, update, user_data):
    voice = update.message.voice.get_file()
    file = requests.get(voice.file_path).content
    response = speech_analyze(SPEECH_TOKEN, file)

    text = speech_parser(response)
    data = geocoder_request(geocode=text, format='json')

    if check_response(data):
        update.message.reply_text(
            'Город определен',
            reply_markup=ReplyKeyboardMarkup(keyboard2)
        )
        update.message.reply_text('Выберите одну из возможных функций для данного города:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard2))

        user_data['current_response'] = data
        return LOCATION_HANDLER

    update.message.reply_text('По данному адресу ничего не найдено.')

    return SEARCH_HANDLER


def location_handler(bot, update, user_data):
    text = update.message.text

    if text == '🗺Показать на карте':
        res = "[​​​​​​​​​​​]({}){}".format(get_static_map(user_data),
                                           'Карта для города ' + get_city(user_data['current_response'], 'ru-RU'))
        update.message.reply_text(res, parse_mode='markdown', reply_markup=inline_maps)

    elif text == '🗞Последние новости':
        news = parse_news(user_data['current_response'])
        if news is not None:
            user_data['array'] = news
            user_data['index'] = 0
            user_data['length'] = len(news)
            update.message.reply_text('Найдено новостей в заданном городе: {}'.format(len(news)),
                                      reply_markup=ReplyKeyboardRemove())
            update.message.reply_text('*{0}*\n{1}\n[Подробнее:]({2})'.format(*news[0]), parse_mode='markdown',
                                      reply_markup=inline_news_state1)
            return NEWS_HANDLER

        else:
            update.message.reply_text('Новостей для этой местности не найдено')

    elif text == '🌧Погода':
        update.message.reply_text(
            'Что вы хотите узнать о погоде в городе {}?'.format(get_city(user_data['current_response'], 'ru-RU')),
            reply_markup=ReplyKeyboardMarkup(keyboard4))
        return WEATHER_HANDLER

    elif text == '🛩Расписания':
        update.message.reply_text(
            'Выберите один из вариантов поиска:',
            reply_markup=ReplyKeyboardMarkup(keyboard5))
        return RASP_HANDLER

    elif text == '💸Вакансии':
        try:
            data = geocoder_request(geocode=get_city(user_data['current_response']), format='json')
            city = get_city(data, 'ru_RU')
            region = list(region_suggest(city).items())[0][1]

        except:
            update.message.reply_text(
                'Данный город не найден в базе данных HeadHunter.',
                reply_markup=ReplyKeyboardMarkup(keyboard2)
            )
            return LOCATION_HANDLER

        try:
            params = {
                'area': region
            }
            if user_data['vacancy']['keywords'] is not None:
                params['text'] = user_data['vacancy']['keywords']
            user_data['vacancies_response'] = vacancies_request(**params)['items']
            if len(user_data['vacancies_response']) == 0:
                update.message.reply_text(
                    'Для данного города не найдено ни одной вакансии.',
                    reply_markup=ReplyKeyboardMarkup(keyboard2)
                )
                return LOCATION_HANDLER

            user_data['vacancies_index'] = 0
            user_data['vacancies_image'] = 'logo'

            update.message.reply_text('Найдено несколько вакансий', reply_markup=ReplyKeyboardRemove())
            _keyboard = [
                [InlineKeyboardButton('Следующая вакансия▶️', callback_data=1)],
                [InlineKeyboardButton('🗺Местоположение', callback_data=4)],
                [InlineKeyboardButton('🔙Назад', callback_data=3)]
            ]

            if len(user_data['vacancies_response']) == 1:
                _keyboard.pop(0)

            reply = form_vacancy_reply(user_data)
            if reply['address'] == 'Адрес не указан':
                _keyboard.pop(1)

            update.message.reply_text(
                (
                    '*{title}*\n'
                    '{experience}\n'
                    '{address}\n'
                    '[Подробнее:]({url})\n'
                    '[​​​​​​​​​​​]({image_url})'  # EMPTY STRING IN BRACKETS
                ).format(**reply),
                parse_mode='markdown',
                reply_markup=InlineKeyboardMarkup(_keyboard)
            )

            return VACANCIES_HANDLER

        except Exception as e:
            logger.exception(e)

    elif text == '🔙Вернуться назад':
        update.message.reply_text(
            'Введите город, информацию о котором Вы хотите узнать',
            reply_markup=ReplyKeyboardMarkup(keyboard3)
        )
        return SEARCH_HANDLER

    return LOCATION_HANDLER


def scrolling_vacancy(bot, update, user_data):
    query = update.callback_query
    try:
        if query.data == '1':
            if user_data['vacancies_index'] != len(user_data['vacancies_response']) - 1:
                user_data['vacancies_index'] += 1

        elif query.data == '2':
            if user_data['vacancies_index'] != 0:
                user_data['vacancies_index'] -= 1

        elif query.data == '3':
            bot.deleteMessage(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id
            )

            bot.send_message(
                query.message.chat_id,
                'Выберите одну из возможных функций для данного местоположения:',
                reply_markup=ReplyKeyboardMarkup(keyboard2)
            )

            return LOCATION_HANDLER

        elif query.data == '4':
            user_data['vacancies_image'] = 'location'

        elif query.data == '5':
            user_data['vacancies_image'] = 'logo'

        keyboard = [
            [],
            [],
            [InlineKeyboardButton('🔙Назад', callback_data=3)]
        ]

        if user_data['vacancies_index'] != 0:
            keyboard[0].append(InlineKeyboardButton(
                '◀️Предыдущая вакансия', callback_data=2
            ))

        if user_data['vacancies_index'] != len(user_data['vacancies_response']) - 1:
            keyboard[0].append(InlineKeyboardButton(
                'Следующая вакансия▶️', callback_data=1
            ))

        reply = form_vacancy_reply(
            user_data,
            user_data['vacancies_image'] == 'location'
        )

        if reply['address'] != 'Адрес не указан':
            if user_data['vacancies_image'] == 'location':
                keyboard[1].append(InlineKeyboardButton('🎫Логотип', callback_data=5))
            else:
                keyboard[1].append(InlineKeyboardButton('🗺Местоположение', callback_data=4))

        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=(
                '*{title}*\n'
                '{experience}\n'
                '{address}\n'
                '[​​​​​​​​​​​]({image_url})'  # EMPTY STRING IN BRACKETS
                '[Подробнее:]({url})\n'
            ).format(**reply),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='markdown'
        )

        return VACANCIES_HANDLER
    except Exception as e:
        logger.exception(e)


def form_vacancy_reply(user_data, add_location_image=False):
    vacancy_id = user_data['vacancies_response'][user_data['vacancies_index']]['id']
    vacancy = full_vacancy_request(vacancy_id)

    title = vacancy['name']
    experience = vacancy['experience']['name']
    address = vacancy['address']
    if address is not None:
        try:
            address = address['city'] + ', ' + address['street'] + ' ' + address['building']
        except TypeError:
            address = 'Адрес не указан'
    else:
        address = 'Адрес не указан'

    vacancy_url = vacancy['alternate_url']

    if add_location_image:
        if vacancy['address'] is not None:
            pos = vacancy['address']['lng'], vacancy['address']['lat']
            image_url = map_request(
                ll='{},{}'.format(*pos),
                pt='{},{},pm2rdm'.format(*pos),
                l='map'
            )
        else:
            if vacancy['employer']['logo_urls'] is not None:
                image_url = vacancy['employer']['logo_urls']['original']
            else:
                image_url = ''
    else:
        if vacancy['employer']['logo_urls'] is not None:
            image_url = vacancy['employer']['logo_urls']['original']
        else:
            image_url = ''

    return {
        'title': title,
        'experience': experience,
        'address': address,
        'url': vacancy_url,
        'image_url': image_url
    }


def scrolling_news(bot, update, user_data):
    query = update.callback_query
    d = {0: inline_news_state1, user_data['length'] - 1: inline_news_state3}
    if query.data == '1':
        user_data['index'] = min(user_data['length'], user_data['index'] + 1)

    elif query.data == '2':
        user_data['index'] = max(0, user_data['index'] - 1)

    elif query.data == '3':
        bot.deleteMessage(chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
        bot.send_message(query.message.chat_id, 'Выберите одну из возможных функций для данного местоположения:',
                         reply_markup=ReplyKeyboardMarkup(keyboard2))

        return LOCATION_HANDLER
    try:
        bot.edit_message_text(text='*{0}*\n{1}\n[Подробнее:]({2})'.format(*user_data['array'][user_data['index']]),
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, parse_mode='markdown',
                              reply_markup=d[user_data['index']] if user_data['index'] in d else inline_news_state2)
    except IndexError:
        if user_data['index'] < 0:
            user_data['index'] = 0

        else:
            user_data['index'] = user_data['length'] - 1


def choosing_map_type(bot, update, user_data):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                          text="[​​​​​​​​​​​]({}){}".format(get_static_map(user_data, query.data),
                                                            'Карта для города ' + get_city(
                                                                user_data['current_response'], 'ru-RU')),
                          parse_mode='markdown', reply_markup=inline_maps)


def enter_the_map(bot, update):
    text = update.message.text
    if text == '🔙Вернуться назад':
        return LOCATION_HANDLER


def weather(bot, update, user_data):
    text = update.message.text

    if text == '🌤Текущая погода':
        city, code = get_city(user_data['current_response']), get_country_code(user_data['current_response'])
        update.message.reply_text(
            get_current_weather(city, code, WEATHER_TOKEN, get_city(user_data['current_response'], 'ru-RU')))

    elif text == '☔️Прогноз на 6 дней':
        city, code = get_city(user_data['current_response']), get_country_code(user_data['current_response'])
        update.message.reply_text(
            get_forecast_weather(city, code, WEATHER_TOKEN, get_city(user_data['current_response'], 'ru-RU')))

    elif text == '🔙Вернуться назад':
        update.message.reply_text('Выберите одну из возможных функций для данного местоположения:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard2))

        return LOCATION_HANDLER


def schedule(bot, update, user_data):
    text = update.message.text

    if text == '✈️Найти авиарейс':
        city_ru, city_en = get_city(user_data['current_response'], 'ru_RU'), get_city(user_data['current_response'])
        airports = airs.get(city_ru, []) + airs.get(city_en, [])

        if airports:
            airport_question(update, city_ru, city_en)
            return SET_SECOND_CITY_HANDLER

        else:
            update.message.reply_text(
                'В заданном городе аэропорта не найдено')

    elif text == '🔙Вернуться назад':
        update.message.reply_text('Выберите одну из возможных функций для данного местоположения:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard2))

        return LOCATION_HANDLER


def set_second_city(bot, update, user_data):
    text = update.message.text

    if text == '🔙Вернуться назад':
        update.message.reply_text(
            'Выберите один из вариантов поиска:',
            reply_markup=ReplyKeyboardMarkup(keyboard5))
        return RASP_HANDLER

    elif text == '🔚Вернуться в меню':
        update.message.reply_text('Выберите одну из возможных функций для данного местоположения:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard2))

        return LOCATION_HANDLER

    else:
        user_data['airport1'] = text.split(', ')[-1]
        update.message.reply_text('Введите город пункта назначения:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard3 + [['🔚Вернуться в меню']]))
        return SET_SECOND_AIRPORT_HANDLER


def set_second_airport(bot, update, user_data):
    text = update.message.text

    if text == '🔙Вернуться назад':
        city_ru, city_en = get_city(user_data['current_response'], 'ru_RU'), get_city(user_data['current_response'])
        airport_question(update, city_ru, city_en)
        return SET_SECOND_CITY_HANDLER

    elif text == '🔚Вернуться в меню':
        update.message.reply_text('Выберите одну из возможных функций для данного местоположения:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard2))

        return LOCATION_HANDLER

    else:
        response = geocoder_request(geocode=text, format='json')
        if check_response(response):
            user_data['city2'] = get_city(response, 'ru_RU')
            city_en = get_city(response)
            airports = airs.get(user_data['city2'], []) + airs.get(city_en, [])
            if not airports:
                update.message.reply_text('Введеный город не найден. Проверьте написание.')
                return SET_SECOND_AIRPORT_HANDLER
            update.message.reply_text('Выберите аэропорт прибытия:',
                                      reply_markup=ReplyKeyboardMarkup(
                                          [[elem[1] + ', ' + elem[0]] for elem in airports] + [['🔙Вернуться назад'],
                                                                                               ['🔚Вернуться в меню']]))
            return FIND_FLIGHTS_HANDLER
        update.message.reply_text('Введеный город не найден. Проверьте написание.')


def find_flights(bot, update, user_data):
    text = update.message.text

    if text == '🔙Вернуться назад':
        city_ru, city_en = get_city(user_data['current_response'], 'ru_RU'), get_city(user_data['current_response'])
        airport_question(update, city_ru, city_en)
        return SET_SECOND_CITY_HANDLER

    elif text == '🔚Вернуться в меню':
        update.message.reply_text('Выберите одну из возможных функций для данного местоположения:',
                                  reply_markup=ReplyKeyboardMarkup(keyboard2))

        return LOCATION_HANDLER

    else:
        airport2 = text.split(', ')[-1]
        flights = get_flights(user_data['airport1'], airport2)
        if not flights:
            update.message.reply_text('Рейсов между указанными ранее аэропортами не найдено!')
            city_ru, city_en = get_city(user_data['current_response'], 'ru_RU'), get_city(user_data['current_response'])
            airport_question(update, city_ru, city_en)
            return SET_SECOND_CITY_HANDLER

        user_data['array'] = flights
        user_data['index'] = 0
        user_data['length'] = len(flights)
        update.message.reply_text('Найдено рейсов для данного направления: {}'.format(len(flights)),
                                  reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(
            '[Данные предоставлены сервисом Яндекс.Расписания](http://rasp.yandex.ru/)',
            parse_mode='markdown'
        )
        update.message.reply_text(flights[0],
                                  reply_markup=inline_sch_state1 if len(flights) > 1 else ReplyKeyboardMarkup(
                                      keyboard3))


def scrolling_flights(bot, update, user_data):
    print(user_data['array'])
    query = update.callback_query
    d = {0: inline_sch_state1, user_data['length'] - 1: inline_sch_state3}
    if query.data == '1':
        user_data['index'] = min(user_data['length'], user_data['index'] + 1)

    elif query.data == '2':
        user_data['index'] = max(0, user_data['index'] - 1)

    elif query.data == '3':
        bot.deleteMessage(chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
        city_ru, city_en = get_city(user_data['current_response'], 'ru_RU'), get_city(user_data['current_response'])
        airports = airs.get(city_ru, []) + airs.get(city_en, [])
        bot.sendMessage(text='Из какого аэропорта города {} вы хотите найти рейс?'.format(city_ru),
                        chat_id=query.message.chat_id,
                        reply_markup=ReplyKeyboardMarkup(
                            [[elem[1] + ', ' + elem[0]] for elem in airports] + [['🔙Вернуться назад'],
                                                                                 ['🔚Вернуться в меню']]))
        return SET_SECOND_CITY_HANDLER

    try:
        bot.edit_message_text(text=user_data['array'][user_data['index']],
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id, parse_mode='markdown',
                              reply_markup=d[user_data['index']] if user_data['index'] in d else inline_sch_state2)
    except IndexError:
        if user_data['index'] < 0:
            user_data['index'] = 0

        else:
            user_data['index'] = user_data['length'] - 1


def airport_question(update, city_ru, city_en):
    airports = airs.get(city_ru, []) + airs.get(city_en, [])
    update.message.reply_text('Из какого аэропорта города {} вы хотите найти рейс?'.format(city_ru),
                              reply_markup=ReplyKeyboardMarkup(
                                  [[elem[1] + ', ' + elem[0]] for elem in airports] + [['🔙Вернуться назад'],
                                                                                       ['🔚Вернуться в меню']]))


def stop(bot, update):
    update.message.reply_text('Пока!', reply_markup=ReplyKeyboardRemove())
    update.message.reply_text('Для того, чтобы начать работу с ботом заново напишите /start')
    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    updater = Updater(TELEGRAM_TOKEN)

    dp = updater.dispatcher
    dp.add_error_handler(error)
    dp.add_handler(conversation_handler)

    updater.start_polling()
    updater.idle()


(
    ENTER_NAME, ENTER_LOCATION, SEARCH_HANDLER, LOCATION_HANDLER,
    LOCATION_APPLY, MAIN_MENU, PROFILE_CONFIG, KEYWORDS_CONFIG, KEYWORDS_APPLY,
    VACANCIES_HANDLER, NEWS_HANDLER, WEATHER_HANDLER, RASP_HANDLER,
    SET_SECOND_CITY_HANDLER, SET_SECOND_AIRPORT_HANDLER,
    FIND_FLIGHTS_HANDLER
) = range(16)

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states={
        ENTER_NAME: [MessageHandler(Filters.text, enter_name, pass_user_data=True)],
        ENTER_LOCATION: [MessageHandler(Filters.text, enter_location, pass_user_data=True)],
        LOCATION_APPLY: [MessageHandler(Filters.text, location_apply, pass_user_data=True)],

        MAIN_MENU: [MessageHandler(Filters.text, main_menu, pass_user_data=True)],

        PROFILE_CONFIG: [MessageHandler(Filters.text, profile_config, pass_user_data=True)],

        KEYWORDS_CONFIG: [MessageHandler(Filters.text, keywords_config, pass_user_data=True)],
        KEYWORDS_APPLY: [MessageHandler(Filters.text, keywords_apply, pass_user_data=True)],

        SEARCH_HANDLER: [
            MessageHandler(Filters.text, search_handler, pass_user_data=True),
            MessageHandler(Filters.voice, voice_to_text, pass_user_data=True)
        ],

        LOCATION_HANDLER: [
            MessageHandler(Filters.text, location_handler, pass_user_data=True),
            CallbackQueryHandler(choosing_map_type, pass_user_data=True),
        ],

        NEWS_HANDLER: [
            CallbackQueryHandler(scrolling_news, pass_user_data=True)
        ],

        VACANCIES_HANDLER: [
            CallbackQueryHandler(scrolling_vacancy, pass_user_data=True)
        ],

        WEATHER_HANDLER: [
            MessageHandler(Filters.text, weather, pass_user_data=True)
        ],

        RASP_HANDLER: [
            MessageHandler(Filters.text, schedule, pass_user_data=True)
        ],

        SET_SECOND_CITY_HANDLER: [
            MessageHandler(Filters.text, set_second_city, pass_user_data=True)
        ],

        SET_SECOND_AIRPORT_HANDLER: [
            MessageHandler(Filters.text, set_second_airport, pass_user_data=True)
        ],

        FIND_FLIGHTS_HANDLER: [
            MessageHandler(Filters.text, find_flights, pass_user_data=True),
            CallbackQueryHandler(scrolling_flights, pass_user_data=True),
        ]
    },

    fallbacks=[CommandHandler('stop', stop)]
)

if __name__ == '__main__':
    main()