import os

import requests


class CancelOrder:
    def __init__(self, update, order_id):
        self.update = update
        self.order_id = order_id

    def start(self):
        url = 'https://api-1c.trimiata.ru/utd/hs/api/cancel-order'
        user = os.getenv('1C_LOGIN')
        password = os.getenv('1C_PASSWORD')
        params = {
            'order_id': self.order_id,
        }
        response = requests.get(url, params=params, auth=(user, password))
        response.raise_for_status()
        self.update.message.reply_text(response.text)
