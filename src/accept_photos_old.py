import os
import re
import shutil

import requests
from dotenv import load_dotenv
from telegram import Update

from env_settings import settings


class PhotoManager:
    def __init__(self, update: Update, photo_sources_path: str, kind: str):
        self.kind = kind.upper()
        if self.kind not in ('PHOTO', 'VIDEO'):
            raise ValueError('kind should be PHOTO or VIDEO')
        self.temp_message = update.message.reply_text('Accepting started...')
        self.src_path = os.path.join(
            photo_sources_path, 'PHOTO_TEAM', self.kind,
        )
        self.dst_path = os.path.join(photo_sources_path, 'ACCEPTED', self.kind)

    def start(self):
        try:
            document = Photos(self)
            document.check_folders()
            document.validate_files()
            document.move_files()
            self.temp_message.reply_text('Accepting completed.')
        except Exception as e:
            self.temp_message.reply_text(f'Error: {e}')


class Photos:
    url = settings.PHOTO_RENAMING_URL
    user = settings.LOGIN_1C
    password = settings.PASSWORD_1C

    def __init__(self, manager):
        self.manager = manager
        self.photos = []
        if self.manager.kind == 'PHOTO':
            self.pattern = r'^\d+_[123]\.jpeg$'
        elif self.manager.kind == 'VIDEO':
            self.pattern = r'^\d+_v1\.mp4'
        self.request_result = None

    def check_folders(self):
        assert (
            len(os.listdir(self.manager.src_path)) != 0
        ), 'The source folder is empty'
        assert (
            len(os.listdir(self.manager.dst_path)) == 0
        ), 'The destination folder is not empty'

    def validate_files(self):
        self.create_table()
        self.make_request()
        self.join_1c_data()
        self.validate_table()

    def create_table(self):
        """Заполняет таблицу."""
        for file_name in os.listdir(self.manager.src_path):
            self.photos.append(Photo(file_name, self.pattern))

    def get_unique_series(self):
        """Возвращает множество уникальных штрихкодов кроме пустых."""
        unique_series = {
            photo.barcode
            for photo in self.photos
            if photo.barcode
        }
        return unique_series

    def make_request(self):
        """Делает запрос к 1С."""
        load_dotenv(override=True)
        unique_series = self.get_unique_series()
        if not unique_series:
            return
        url = os.getenv('PHOTO_RENAMING_URL')
        user = os.getenv('1C_LOGIN')
        password = os.getenv('1C_PASSWORD')
        data = {'series': list(unique_series)}
        response = requests.post(url, json=data, auth=(user, password))
        response.raise_for_status()
        self.request_result = response.json()

    def join_1c_data(self):
        """Заполняет штрихкод фотографии из ответа от 1С."""
        for photo in self.photos:
            if not photo.barcode:
                continue
            # Для каждой строки таблицы из папки ищем штрихкод в ответе от 1С
            found_dict = next(
                request_line
                for request_line in self.request_result
                if request_line.get('ШК') == photo.barcode
            )
            photo.series = found_dict['Наименование']

    def validate_table(self):
        """
        Проверка таблицы.

        Проверяет таблицу на наличие невалидных имен файлов
        и несуществующих штрихкодов
        Если есть одно или второе, то файловых операций не будет выполнено
        """
        invalid_pattern_file_names = [
            photo.file_name
            for photo in self.photos
            if not photo.barcode
        ]
        non_existent_barcode_file_names = [
            photo.file_name
            for photo in self.photos
            if photo.barcode and not photo.series
        ]
        if invalid_pattern_file_names or non_existent_barcode_file_names:
            raise PhotoFileNamesError(
                invalid_pattern_file_names,
                non_existent_barcode_file_names,
            )

    def move_files(self):
        for photo in self.photos:
            src = os.path.join(
                self.manager.src_path, photo.file_name,
            )
            dst = os.path.join(self.manager.dst_path, photo.file_name)
            shutil.move(src, dst)


class Photo:
    def __init__(self, file_name, pattern):
        self.file_name = file_name
        self.barcode = None
        self.angle = None
        self.series = None

        if re.match(pattern, file_name):
            name, extension = file_name.split('.')
            self.barcode, self.angle = name.split('_')


class PhotoFileNamesError(Exception):
    def __init__(
        self, invalid_pattern_file_names, non_existent_barcode_file_names,
    ):
        message = 'There are photo naming issues\n'
        if invalid_pattern_file_names:
            message += '\nWrong file names:\n'
            message += '\n'.join(invalid_pattern_file_names)
        if non_existent_barcode_file_names:
            message += '\nNon existent barcodes:\n'
            message += '\n'.join(non_existent_barcode_file_names)
        super().__init__(message)
