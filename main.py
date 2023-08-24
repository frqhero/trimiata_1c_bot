import os

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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


def go_1c(update=False):
    url = os.getenv('STOCK_DATA_EQUIVALENCE')
    login = os.getenv('1C_LOGIN')
    password = os.getenv('1C_PASSWORD')
    if update:
        params = {'update': ''}
    else:
        params = {}
    response = requests.get(url, params, auth=(login, password))
    return response.text


def handle_callback(update: Update, context: CallbackContext):
    data = update.callback_query.data
    update.callback_query.answer()
    if data == '1':
        update.callback_query.message.edit_text('Делаем запрос...\nОжидание ~ 5 сек.')
        response = go_1c()
        update.callback_query.message.delete()
        update.callback_query.message.reply_text(response)
    elif data == '2':
        update.callback_query.message.edit_text('Делаем запрос...\nОжидание ~ 60 сек.')
        response = go_1c(update=True)
        update.callback_query.message.delete()
        update.callback_query.message.reply_text(response)
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
