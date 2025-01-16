import telebot
from extensions import CurrencyConverter, APIException
from config import TOKEN, currencies

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def start_help(message: telebot.types.Message):
    text = '''Бот конвертирует указанную сумму из первой валюты во вторую.\n
Напишите через пробел:\n
<первая валюта>  <вторая валюта>  <сумма первой валюты>\n
Пример запроса:\n
доллар рубль 1000\n
\n
Для просмотра доступных валют наберите команду /values
    '''
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['values'])
def legit_values(message: telebot.types.Message):
    text = 'Доступные валюты:'
    for key in currencies.keys():
        text = '\n    '.join([text, key])

    bot.reply_to(message, text)

@bot.message_handler(content_types=['text', ])
def convert(message: telebot.types.Message):
    try:
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

bot.polling()
