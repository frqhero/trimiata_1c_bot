import os

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
)

from find_photos_with_same_article import main as find_photos_with_same_article
from rename_photos import RenamePhotos
from stock_equivalence import StockEquivalence


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


def handle_callback(update: Update, context: CallbackContext):
    data = update.callback_query.data
    update.callback_query.answer()
    if data == '1':
        StockEquivalence(update, update_1c_required=False).start()
    elif data == '2':
        StockEquivalence(update, update_1c_required=True).start()
    elif data == '3':
        update.callback_query.message.delete()


def stock_data_equivalence(update: Update, context: CallbackContext):
    StockEquivalence(update, update_1c_required=False).start()


def stock_data_equivalence_update(update: Update, context: CallbackContext):
    StockEquivalence(update, update_1c_required=True).start()


def rename_photos(update: Update, context: CallbackContext):
    photo_sources_path = os.getenv('PHOTO_SOURCES_PATH')
    rename_photos_class = RenamePhotos(update, photo_sources_path)
    rename_photos_class.start()


def handler_find_photos_with_same_article(
    update: Update, context: CallbackContext
):
    result = find_photos_with_same_article()
    update.message.reply_document(
        result['bytes'], 'find_photos_with_same_article.txt'
    )


def check_sources_handler(update: Update, context: CallbackContext):
    result = check_sources()
    if (
        result['PHOTO']['wrong_names']
        or result['PHOTO']['wrong_barcodes']
        or result['VIDEO']['wrong_names']
        or result['VIDEO']['wrong_barcodes']
    ):
        if result['PHOTO']['wrong_names'] or result['PHOTO']['wrong_barcodes']:
            update.message.reply_text('PHOTO')
            if result['PHOTO']['wrong_names']:
                update.message.reply_document(result['PHOTO']['wrong_names'])
            if result['PHOTO']['wrong_barcodes']:
                update.message.reply_document(
                    result['PHOTO']['wrong_barcodes']
                )
        if result['VIDEO']['wrong_names'] or result['VIDEO']['wrong_barcodes']:
            update.message.reply_text('VIDEO')
            if result['VIDEO']['wrong_names']:
                update.message.reply_document(result['VIDEO']['wrong_names'])
            if result['VIDEO']['wrong_barcodes']:
                update.message.reply_document(
                    result['VIDEO']['wrong_barcodes']
                )
    else:
        update.message.reply_text(
            'Files in /SOURCES/PHOTO and /SOURCES/VIDEO '
            'have correct names and existing barcodes'
        )


def main():
    load_dotenv(override=True)

    telegram_token = os.getenv('TELEGRAM_TOKEN')
    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('bot', start))
    dispatcher.add_handler(
        CallbackQueryHandler(handle_callback, pattern='^\d$')
    )

    # data equivalence
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
