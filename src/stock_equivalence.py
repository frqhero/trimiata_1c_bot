import json
import os
from time import perf_counter

import requests


# Когда через кнопку, то колбек и меняем наше сообщение, пишем, что выполняется.
# Потом опять его меняем пишем сколько заняло плюс еще одно сообщение с результатом

# Когда через команду, то сразу отправляем сообщение, пишем, что выполняется.
# Потом опять его меняем пишем сколько заняло плюс еще одно сообщение с результатом


class StockEquivalence:
    def __init__(self, update, update_1c_required):
        self.callback_query = bool(update.callback_query)
        self.message = update.callback_query.message if self.callback_query else update.message
        self.update_1c_required = update_1c_required
        self.duration = '60' if update_1c_required else '5'
        initial_response = f'Делаем запрос...\nОжидание ~ {self.duration} сек.'
        if self.callback_query:
            self.message.edit_text(initial_response)
        else:
            self.message2 = self.message.reply_text(initial_response)

    def make_request(self):
        url = os.getenv('STOCK_DATA_EQUIVALENCE')
        login = os.getenv('LOGIN_1C')
        password = os.getenv('PASSWORD_1C')
        if self.update_1c_required:
            params = {'update': ''}
        else:
            params = {}
        response = requests.get(url, params, auth=(login, password))
        return json.dumps(response.json(), indent=2, ensure_ascii=False)

    def start(self):
        start = perf_counter()
        response = self.make_request()
        finish = perf_counter()

        time_taken_msg = (
            f'Запрос занял {int(finish - start)} сек.\nСпасибо за ожидание 🙂'
        )
        if self.callback_query:
            self.message.edit_text(time_taken_msg)
            self.message.reply_text(response, quote=False)
        else:
            self.message2.edit_text(time_taken_msg)
            self.message2.reply_text(response, quote=False)
