import json
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

from photo_renaming import main as photo_renaming
from find_photos_with_same_article import main as find_photos_with_same_article
from check_sources import main as check_sources


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
    return json.dumps(response.json(), indent=2, ensure_ascii=False)


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


def stock_data_equivalence(update: Update, context: CallbackContext):
    message = update.message
    temp_message = message.reply_text(f'Делаем запрос...\nОжидание > 10 сек.')
    start = perf_counter()
    response = go_1c(False)
    finish = perf_counter()
    temp_message.edit_text(
        f'Запрос занял {int(finish - start)} сек.\nСпасибо за ожидание 🙂'
    )
    temp_message.reply_text(response, quote=False)


def stock_data_equivalence_update(update: Update, context: CallbackContext):
    message = update.message
    temp_message = message.reply_text(f'Делаем запрос...\nОжидание > 60 сек.')
    start = perf_counter()
    response = go_1c(True)
    finish = perf_counter()
    temp_message.edit_text(
        f'Запрос занял {int(finish - start)} сек.\nСпасибо за ожидание 🙂'
    )
    temp_message.reply_text(response, quote=False)


def rename_photos(update: Update, context: CallbackContext):
    temp_message = update.message.reply_text('Renaming started...')
    result = photo_renaming()
    if result['exception']:
        temp_message.edit_text(result['exception'])
        if result['wrong_names']:
            temp_message.reply_document(
                result['wrong_names'], 'wrong_names.txt'
            )
        if result['wrong_barcodes']:
            temp_message.reply_document(
                result['wrong_barcodes'], 'wrong_barcodes.txt'
            )
    else:
        temp_message.edit_text(
            'The renaming operation was successfully completed.\n'
            f'It took {result["renaming_duration"]} seconds.\n'
            f'Before the operation, the destination folder contained {result["photo_number_before"]} files, '
            f'and it has {result["photo_number_after"]} files afterward.'
        )


def handler_find_photos_with_same_article(
    update: Update, context: CallbackContext
):
    result = find_photos_with_same_article()
    update.message.reply_document(
        result['bytes'], 'find_photos_with_same_article.txt'
    )


def check_sources_handler(update: Update, context: CallbackContext):
    result = check_sources()
    if result['PHOTO'] or result['VIDEO']:
        if result['PHOTO']:
            update.message.reply_text('PHOTO')
            if
            update.message.reply_document(result['PHOTO'])

    update.message.reply_text()


def main():
    load_dotenv()

    telegram_token = os.getenv('TELEGRAM_TOKEN')
    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('bot', start))
    dispatcher.add_handler(
        CallbackQueryHandler(handle_callback, pattern='^\d$')
    )

    dispatcher.add_handler(
        CommandHandler('stock_data_equivalence', stock_data_equivalence)
    )
    dispatcher.add_handler(
        CommandHandler(
            'stock_data_equivalence_update', stock_data_equivalence_update
        )
    )
    dispatcher.add_handler(CommandHandler('rename_photos', rename_photos))
    dispatcher.add_handler(
        CommandHandler(
            'find_photos_with_same_article',
            handler_find_photos_with_same_article,
        )
    )
    dispatcher.add_handler(
        CommandHandler('check_sources', check_sources_handler)
    )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
