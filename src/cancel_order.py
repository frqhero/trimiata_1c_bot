import requests

from src.env_settings import settings


class CancelOrder:
    url = settings.CANCEL_ORDER_URL
    user = settings.LOGIN_1C
    password = settings.PASSWORD_1C

    def __init__(self, update, order_id):
        self.update = update
        self.order_id = order_id

    def start(self):
        params = {
            'order_id': self.order_id,
        }
        response = requests.get(self.url, params=params, auth=(self.user, self.password))
        response.raise_for_status()
        self.update.message.reply_text(response.text)
