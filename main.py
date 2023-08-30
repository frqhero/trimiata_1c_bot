import os
from time import perf_counter

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
)
import requests

load_dotenv()


def start(update: Update, context: CallbackContext) -> None:
    """Inform user about what this bot can do"""
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text='Показать сверку', callback_data='1')],
            [
                InlineKeyboardButton(
                    text='Загрузить отчет и показать сверку', callback_data='2'
                )
            ],
            [InlineKeyboardButton(text='Отмена', callback_data='3')],
        ]
    )

    update.message.reply_text('Приветствие', reply_markup=keyboard)


def go_1c(update):
    url = os.getenv('STOCK_DATA_EQUIVALENCE')
    login = os.getenv('1C_LOGIN')
    password = os.getenv('1C_PASSWORD')
    if update:
        params = {'update': ''}
    else:
        params = {}
    response = requests.get(url, params, auth=(login, password))
    return str(response.json())


def execute_main_logic(message: Message, update_requred=False):
    query_duration = ('5', '60')
    message.edit_text(
        f'Делаем запрос...\nОжидание ~ {query_duration[update_requred]} сек.'
    )
    start = perf_counter()
    response = go_1c(update_requred)
    finish = perf_counter()
    message.edit_text(
        f'Запрос занял {int(finish - start)} сек.\nСпасибо за ожидание 🙂'
    )
    message.reply_text(response, quote=False)


def handle_callback(update: Update, context: CallbackContext):
    data = update.callback_query.data
    update.callback_query.answer()
    if data == '1':
        execute_main_logic(update.callback_query.message)
    elif data == '2':
        execute_main_logic(update.callback_query.message, True)
    elif data == '3':
        update.callback_query.message.delete()


def main():
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('bot', start))
    dispatcher.add_handler(
        CallbackQueryHandler(handle_callback, pattern='^\d$')
    )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
