import requests
from config import currencies
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')

class APIException(Exception):
    pass

class CurrencyConverter:
    @staticmethod
    def get_price(base: str, quote: str, amount: str) -> float:
        if quote == base:
            raise APIException(f'Невозможно конвертироваь одинаковые валюты < {quote} >.')

        try:
            quote_ticker = currencies[quote]
        except KeyError:
            raise APIException(f'Не удалось обработать валюту < {quote} >')

        try:
            base_ticker = currencies[base]
        except KeyError:
            raise APIException(f'Не удалось обратобать валюту < {base} >')

        try:
            amount_check = float(amount)
        except ValueError:
            raise APIException(f'Не удалось обработать сумму < {amount} >')

        r = requests.get(f'https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{base_ticker}/{quote_ticker}/{amount}').json()
        return round(float(r['conversion_result']), 4)
