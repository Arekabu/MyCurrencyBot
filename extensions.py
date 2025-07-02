import os
import requests
from dotenv import load_dotenv
from config import currencies


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
        except KeyError as e:
            raise APIException(f'Не удалось обработать валюту < {quote} >') from e

        try:
            base_ticker = currencies[base]
        except KeyError as e:
            raise APIException(f'Не удалось обратобать валюту < {base} >') from e

        try:
            float(amount)
        except ValueError as e:
            raise APIException(f'Не удалось обработать сумму < {amount} >') from e

        r = requests.get(
            f'https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{base_ticker}/{quote_ticker}/{amount}',
            timeout=10).json()
        return round(float(r['conversion_result']), 4)


class Queue:
    call_list = {}

    @classmethod
    def check(cls, r_id):
        if r_id in cls.call_list:
            return cls.call_list
        cls.call_list[r_id] = []
        return cls.call_list

    @classmethod
    def add(cls, r_id, data):
        if r_id in cls.call_list:
            if ' ' in data:
                cls.call_list[r_id] = data.split(' ')
            else:
                cls.call_list[r_id].append(f'{data}')

    @classmethod
    def delete(cls, r_id):
        if r_id in cls.call_list:
            del cls.call_list[r_id]

    @classmethod
    def get(cls, r_id):
        if r_id in cls.call_list:
            return cls.call_list[r_id]
        return None

    @classmethod
    def len(cls, r_id):
        if r_id in cls.call_list:
            return len(cls.call_list[r_id])
        return None
