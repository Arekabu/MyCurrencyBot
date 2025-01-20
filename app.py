import telebot
from telebot import types
from extensions import CurrencyConverter, APIException
from config import TOKEN, currencies, country_flags, request_string

bot = telebot.TeleBot(TOKEN)

def is_number(string):
    string = string.replace(',', '.') if ',' in string else string
    try:
        float(string)
        return True
    except ValueError:
        return False

@bot.message_handler(commands=['start', 'help'])
def start_help(message: telebot.types.Message):
    request_string.clear()
    markup = types.InlineKeyboardMarkup(row_width=3)

    btns = [types.InlineKeyboardButton(text=f"{country_flags[key]} {key.title()}", callback_data = key) for key in currencies.keys()]
    # btn1 = types.InlineKeyboardButton(text='🇷🇺 Рубль', callback_data = 'рубль')
    # btn2 = types.InlineKeyboardButton(text='us Доллар', callback_data = 'доллар')
    # btn3 = types.InlineKeyboardButton(text='eu Евро', callback_data = 'евро')

    text = '''Бот конвертирует указанную сумму из первой валюты во вторую.\n
Напишите через пробел:\n
<первая валюта>  <вторая валюта>  <сумма первой валюты>\n
Пример запроса:\n
доллар рубль 1000\n
\n
Для просмотра доступных валют наберите команду /values\n
Запрос можно вводить вручную или использовать кнопки.
Выберите первую валюту:
    '''
    # bot.send_message(message.chat.id, text)
    markup.row(*btns)
    # markup.add(InlineKeyboardButton("Кнопка4", callback_data="button4"),InlineKeyboardButton("Кнопка5", callback_data="button5"))
    bot.send_message(message.from_user.id, text, reply_markup=markup)

@bot.message_handler(commands=['values'])
def legit_values(message: telebot.types.Message):
    text = 'Доступные валюты:'
    for key in currencies.keys():
        text = '\n    '.join([text, key])

    bot.reply_to(message, text)

@bot.message_handler(content_types=['text', ])
def convert(message: telebot.types.Message):
    try:
        if is_number(message.text) and len(request_string) == 2:
            request_string.append(f"{message.text}")
            values = request_string
        else:
            values = message.text.lower().split(' ')

        if len(values) != 3:
            raise APIException("В запросе должно быть 3 параметра.")

        base, quote, amount = values
        amount = amount.replace(',', '.') if ',' in amount else amount
        price = CurrencyConverter.get_price(base, quote, amount)
    except APIException as e:
        bot.reply_to(message, f'Ошибка пользователя.\n{e}')
    except Exception as e:
        bot.reply_to(message, f'Не удалось обработать команду.\n{e}')
    else:
        text = f'{amount} {currencies[base]} = {price} {currencies[quote]}'
        bot.reply_to(message, text)

    request_string.clear()

@bot.callback_query_handler(func = lambda callback: True)
def callpack_message(callback):
    markup = types.InlineKeyboardMarkup(row_width=3)
    if callback.data in currencies.keys():
        request_string.append(callback.data)
        if len(request_string) == 1:
            for key, value in currencies.items():
                if key == callback.data:
                    continue
                markup.add(types.InlineKeyboardButton(text=f"{country_flags[key]} {key.title()}", callback_data = key))
            bot.send_message(callback.message.chat.id, 'Выберите вторую валюту:', reply_markup=markup)
        else:
            btn1 = types.InlineKeyboardButton(text='1', callback_data = '1')
            btn2 = types.InlineKeyboardButton(text='100', callback_data='100')
            btn3 = types.InlineKeyboardButton(text='1000', callback_data='1000')
            markup.row(btn1, btn2, btn3)
            bot.send_message(callback.message.chat.id, 'Выберите или введите вручную в сообщении сумму:', reply_markup=markup)
    else:
        request_string.append(f'{callback.data}')

        callback.message.text = ' '.join(request_string)
        convert(callback.message)

bot.polling()
