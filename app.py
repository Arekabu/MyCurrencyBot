'''
Бот конвертирует суммы в валютах указанных в config.py из одной в другуюю.
Данные о курсах берутся с ресурса https://app.exchangerate-api.com
Рабочий бот: @myprimus_bot
Рабочий бот размещён на бесплатном хостинге,
так что может отваливаться из-за внеплановых работ на сервере.
После 10:00 МСК рабочий бот становится доступен в 99% случаев.
'''


import logging
import time
from logging.handlers import RotatingFileHandler
import os
import telebot
from telebot import types
from dotenv import load_dotenv
from extensions import CurrencyConverter, APIException, Queue
from config import currencies, country_flags


handler = RotatingFileHandler(
    filename='/home/Kryakzenpuk/MyCurrencyBot/warnings.log',
    maxBytes=5*1024*1024,  # 5 MB
    backupCount=3,
    encoding='utf-8'
)

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler],
    force=True
)

logger = logging.getLogger(__name__)

logger_requests = logging.getLogger('requests_logger')
logger_requests.setLevel(logging.INFO)

file_handler = logging.FileHandler(
    '/home/Kryakzenpuk/MyCurrencyBot/requests.log',
    encoding='utf-8',
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
file_handler.setLevel(logging.INFO)
logger_requests.addHandler(file_handler)
logger_requests.propagate = False

telebot_logger = logging.getLogger('telebot')
telebot_logger.addHandler(handler)
telebot_logger.setLevel(logging.WARNING)


load_dotenv()


bot = telebot.TeleBot(os.getenv('TOKEN'))


def is_number(string):
    string = string.replace(',', '.') if ',' in string else string
    try:
        float(string)
        return True
    except ValueError:
        return False


@bot.message_handler(commands=['start', 'help'])
def start_help(message: telebot.types.Message):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(
        text=f"{country_flags[key]} {key.title()}",
        callback_data = key) for key in currencies]
    text = '''Бот конвертирует указанную <u>сумму</u> из <u>первой валюты</u> во <u>вторую</u>.\n
Напишите через пробел:\n
<b><u>первая валюта</u>  <u>вторая валюта</u>  <u>сумма первой валюты</u></b>\n
Пример запроса: <code>доллар рубль 100</code>\n
Для просмотра доступных валют наберите /values\n
Запрос можно вводить вручную или использовать кнопки.\n
<b>Выберите первую валюту:</b>
    '''
    markup.add(*btns)
    bot.send_message(message.from_user.id, text, reply_markup=markup, parse_mode="HTML")


@bot.message_handler(commands=['values'])
def legit_values(message: telebot.types.Message):
    text = 'Доступные валюты:'
    for key in currencies:
        text = '\n    '.join([text, key])

    bot.reply_to(message, text)


@bot.message_handler(content_types=['text', ])
def convert(message: telebot.types.Message, r_id=None):
    if not r_id:
        r_id = message.from_user.id
    Queue.check(r_id)

    try:
        if is_number(message.text) and Queue.len(r_id) == 2:
            bot.delete_message(message.chat.id, message.message_id - 1)

        Queue.add(r_id, message.text)
        values = Queue.get(r_id)

        if len(values) != 3:
            raise APIException("В запросе должно быть 3 параметра.")

        base, quote, amount = values
        amount = amount.replace(',', '.') if ',' in amount else amount
        price = CurrencyConverter.get_price(base, quote, amount)

        if '.' in amount:
            amount = f'{float(amount):_}'.replace('_', ' ')
        else:
            amount = f'{int(amount):_}'.replace('_', ' ')

        price = f'{price:_}'.replace('_', ' ')

    except APIException as e:
        bot.reply_to(message, f'Ошибка пользователя.\n{e}')
    except Exception as e:
        bot.reply_to(message, f'Не удалось обработать команду.\n{e}')
    else:
        text = f'{amount} {currencies[base]} = {price} {currencies[quote]}'
        bot.send_message(message.chat.id, text)

    logger_requests.info(f'username:{message.chat.username} id:{r_id} request:{Queue.get(r_id)}')

    Queue.delete(r_id)


@bot.callback_query_handler(func = lambda callback: True)
def callback_message(callback):
    r_id = callback.from_user.id
    Queue.check(r_id)
    markup = types.InlineKeyboardMarkup(row_width=3)

    if callback.data in currencies:
        Queue.add(r_id, callback.data)
        if Queue.len(r_id) == 1:
            for key in currencies:
                if key == callback.data:
                    continue
                markup.add(types.InlineKeyboardButton(
                    text=f"{country_flags[key]} {key.title()}",
                    callback_data = key))
            bot.edit_message_text(chat_id=callback.message.chat.id,
                                  message_id=callback.message.message_id,
                                  text=f'Первая валюта: {country_flags[callback.data]} {callback.data.title()}',
                                  reply_markup=None)
            bot.answer_callback_query(callback.id)
            bot.send_message(callback.message.chat.id, 'Выберите вторую валюту:', reply_markup=markup)
        else:
            btn1 = types.InlineKeyboardButton(text='1', callback_data = '1')
            btn2 = types.InlineKeyboardButton(text='100', callback_data='100')
            btn3 = types.InlineKeyboardButton(text='1000', callback_data='1000')
            markup.row(btn1, btn2, btn3)
            bot.answer_callback_query(callback.id)
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f'Вторая валюта: {country_flags[callback.data]} {callback.data.title()}',
                reply_markup=None)
            bot.send_message(
                callback.message.chat.id,
                'Выберите или введите вручную в сообщении сумму:',
                reply_markup=markup)
    else:
        Queue.add(r_id, callback.data)
        bot.answer_callback_query(callback.id)
        bot.edit_message_text(chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id,
                              text=f'Сумма первой валюты: {callback.data}',
                              reply_markup=None)
        callback.message.text = ' '.join(Queue.get(r_id))
        convert(callback.message, r_id)


def start_polling():
    while True:
        try:
            logger.warning("Запуск polling...")
            bot.remove_webhook()
            bot.infinity_polling(
                interval=2,
                timeout=30,
                long_polling_timeout=10,
                none_stop=True,
                logger_level=logging.WARNING
            )
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}. Перезапуск через 10 секунд...")
            time.sleep(10)


if __name__ == '__main__':
    logger.warning("Бот запущен")
    start_polling()
