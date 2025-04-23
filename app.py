from datetime import datetime
import os
import telebot
from telebot import types
from dotenv import load_dotenv
from extensions import CurrencyConverter, APIException, Requests
from config import currencies, country_flags

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
def convert(message: telebot.types.Message):
    id = message.chat.id
    Requests.check(id)

    try:
        if is_number(message.text) and Requests.len(id) == 2:
            bot.delete_message(id, message.message_id - 1)

        Requests.add(id, message.text)
        values = Requests.get(id)

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

    with open('logs.txt', 'a') as write_log:
        write_log.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} username:{message.chat.username} id:{id} request:{Requests.get(id)}\n')

    Requests.delete(id)

@bot.callback_query_handler(func = lambda callback: True)
def callback_message(callback):
    id = callback.from_user.id
    Requests.check(id)
    markup = types.InlineKeyboardMarkup(row_width=3)

    if callback.data in currencies:
        Requests.add(id, callback.data)
        if Requests.len(id) == 1:
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
        Requests.add(id, callback.data)
        bot.answer_callback_query(callback.id)
        bot.edit_message_text(chat_id=callback.message.chat.id,
                              message_id=callback.message.message_id,
                              text=f'Сумма первой валюты: {callback.data}',
                              reply_markup=None)
        callback.message.text = ' '.join(Requests.get(id))
        convert(callback.message)

bot.infinity_polling(none_stop=True)
