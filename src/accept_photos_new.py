import os
import re

import requests

from src.env_settings import settings


class Request1C:
    url = settings.PHOTO_RENAMING_URL
    user = settings.LOGIN_1C
    password = settings.PASSWORD_1C

    def __init__(self, unique_series):
        self.unique_series = unique_series
        self.data = {'series': self.unique_series}
        data = {'series': list(unique_series)}
        response = requests.post(self.url, json=data, auth=(self.user, self.password))
        response.raise_for_status()
        self.request_result = response.json()

    def get_result(self):
        """Делает запрос в 1С."""
        pass


class Photo:
    def __init__(self, file_name, pattern):
        self.file_name = file_name
        self.barcode = None
        self.angle = None
        self.series = None

        if re.match(pattern, file_name):
            name, extension = file_name.split('.')
            self.barcode, self.angle = name.split('_')

    def __str__(self):
        return f'{self.file_name}'


class PhotoAccept:
    photo_sources_path = os.getenv('PHOTO_SOURCES_PATH')

    @classmethod
    def set_source_folder(cls, path: str):
        cls.photo_sources_path = path

    def __init__(self, kind: str):
        self.kind = kind.upper()
        if self.kind not in ('PHOTO', 'VIDEO'):
            raise ValueError('kind should be PHOTO or VIDEO')
        if kind == 'PHOTO':
            self.pattern = r'^\d+_[123]\.jpeg$'
        elif kind == 'VIDEO':
            self.pattern = r'^\d+_v1\.mp4'
        self.source_path = os.path.join(self.photo_sources_path, 'PHOTO_TEAM', self.kind)
        self.destination_path = os.path.join(self.photo_sources_path, 'ACCEPTED', self.kind)
        self.files = []
        if self.kind == 'PHOTO':
            self.pattern = r'^\d+_[123]\.jpeg$'
        elif self.kind == 'VIDEO':
            self.pattern = r'^\d+_v1\.mp4'
        self.request_result = None

    def start(self):
        self.check_folders()
        self.fill_files_from_folder()
        request_1c = Request1C(self.get_unique_series())
        self.join_1c_data(request_1c.request_result)


    def check_folders(self):
        """Проверяет, что папки готовы к работе."""
        assert (
            len(os.listdir(self.source_path)) != 0
        ), 'The source folder is empty'
        assert (
            len(os.listdir(self.destination_path)) == 0
        ), 'The destination folder is not empty'

    def fill_files_from_folder(self):
        """Заполняет таблицу."""
        for file_name in os.listdir(self.source_path):
            self.files.append(Photo(file_name, self.pattern))

    def get_unique_series(self):
        """Возвращает множество уникальных штрихкодов кроме пустых."""
        unique_series = {
            photo.barcode
            for photo in self.files
            if photo.barcode
        }
        return list(unique_series)

    def join_1c_data(self, request_result):
        """Заполняет штрихкод фотографии из ответа от 1С."""
        for photo in self.files:
            photo.

            if not photo.barcode:
                continue
            # Для каждой строки таблицы из папки ищем штрихкод в ответе от 1С
            found_dict = next(
                request_line
                for request_line in self.request_result
                if request_line.get('ШК') == photo.barcode
            )
            photo.series = found_dict['Наименование']
