import os
import re
import shutil

import requests

from env_settings import settings
from pydantic_models import PhotoRenamingResponse


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


class CallPhotoRenaming:
    url = settings.PHOTO_RENAMING_URL
    user = settings.LOGIN_1C
    password = settings.PASSWORD_1C

    def __init__(self, unique_series):
        self.unique_series = unique_series
        self.data = {'series': self.unique_series}
        data = {'series': list(unique_series)}
        response = requests.post(self.url, json=data, auth=(self.user, self.password))
        response.raise_for_status()
        self.request_result = PhotoRenamingResponse(response=response.json()).response


class MediaFile:
    photo_pattern = r'^\d+_[123]\.jpeg$'
    video_pattern = r'^\d+_v1\.mp4$'

    def __init__(self, file_name, kind):
        self.file_name = file_name
        self.barcode = None
        self.angle = None
        self.series = None
        self.article = None

        pattern = self.photo_pattern if kind == 'PHOTO' else self.video_pattern

        if re.match(pattern, file_name):
            name, extension = file_name.split('.')
            self.barcode, self.angle = name.split('_')

    def __str__(self):
        return f'{self.file_name}'

    def __repr__(self):
        return f'[{self.file_name}, {self.article}]'

    def __eq__(self, other):
        if isinstance(other, str):
            return self.article == other
        return NotImplemented

    def __hash__(self):
        return hash(self.file_name)

    def fill_1c_data(self, request_result):
        if not self.barcode:
            return
        photo_renaming_row = next(
            photo_renaming_row
            for photo_renaming_row in request_result
            if photo_renaming_row.barcode == self.barcode
        )
        self.series = photo_renaming_row.name
        self.article = photo_renaming_row.article


class SourceArticles:
    media_sources_path = settings.MEDIA_SOURCES_PATH

    def __init__(self, media_type: str):
        self.media_type = media_type
        if self.media_type not in ('PHOTO', 'VIDEO'):
            raise ValueError('kind should be PHOTO or VIDEO')
        self.source_path = os.path.join(self.media_sources_path, 'SOURCES', self.media_type)
        self.files = []
        self.request_result = None

    def __call__(self):
        self.fill_files_from_folder()
        request_1c = CallPhotoRenaming(self.get_unique_series())
        self.fill_1c_data(request_1c.request_result)

    def fill_files_from_folder(self):
        """Заполняет таблицу."""
        for file_name in os.listdir(self.source_path):
            self.files.append(MediaFile(file_name, self.media_type))

    def get_unique_series(self):
        """Возвращает множество уникальных штрихкодов кроме пустых."""
        unique_series = {
            photo.barcode
            for photo in self.files
            if photo.barcode
        }
        return list(unique_series)

    def fill_1c_data(self, request_result):
        """Заполняет штрихкод фотографии из ответа от 1С."""
        for photo in self.files:
            photo.fill_1c_data(request_result)

    def get_articles(self):
        return {media_file.article for media_file in self.files if media_file.article}

    def get_already_existing_reprs(self, article_intersection):
        article_intersection = list(article_intersection)
        result = []
        for media_file in self.files:
            if media_file in article_intersection:
                result.append(repr(media_file))
        return result


class MediaAccept:
    media_sources_path = settings.MEDIA_SOURCES_PATH

    def __init__(self, media_type: str):
        self.kind = media_type.upper()
        if self.kind not in ('PHOTO', 'VIDEO'):
            raise ValueError('kind should be PHOTO or VIDEO')
        self.media_type = media_type
        self.source_path = os.path.join(self.media_sources_path, 'PHOTO_TEAM', self.kind)
        self.destination_path = os.path.join(self.media_sources_path, 'ACCEPTED', self.kind)
        self.media_files = []

    def __call__(self):
        self.check_folders()
        self.fill_files_from_folder()
        request_1c = CallPhotoRenaming(self.get_unique_series())
        self.fill_1c_data(request_1c.request_result)
        self.validate_files()
        self.check_article_uniqueness()
        self.move_files()

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
            self.media_files.append(MediaFile(file_name, self.media_type))

    def get_unique_series(self):
        """Возвращает множество уникальных штрихкодов кроме пустых."""
        unique_series = {
            photo.barcode
            for photo in self.media_files
            if photo.barcode
        }
        return list(unique_series)

    def fill_1c_data(self, request_result):
        """Заполняет штрихкод фотографии из ответа от 1С."""
        for photo in self.media_files:
            photo.fill_1c_data(request_result)

    def validate_files(self):
        bad_file_names = []
        bad_barcodes = []
        for photo in self.media_files:
            if not photo.barcode:
                bad_file_names.append(photo.file_name)
            if photo.barcode and not photo.series:
                bad_barcodes.append(photo.barcode)
        if bad_file_names or bad_barcodes:
            raise PhotoFileNamesError(bad_file_names, bad_barcodes)

    def check_article_uniqueness(self):
        articles = self.get_articles()
        source_articles = SourceArticles(self.media_type)
        source_articles()
        source_articles_articles = source_articles.get_articles()
        article_intersection = articles & source_articles_articles
        file_names = '\n'.join(
            [repr(media_file) for media_file in self.media_files if media_file.article in article_intersection],
        )
        source_files = source_articles.get_already_existing_reprs(article_intersection)
        source_files = '\n'.join(source_files)
        if article_intersection:
            raise ValueError(
                f'Articles {article_intersection} are already in the source folder.\nFile names:\n{file_names}\nSources:\n{source_files}',
            )

    def get_articles(self):
        return {media_file.article for media_file in self.media_files if media_file.article}

    def move_files(self):
        for media_file in self.media_files:
            src = os.path.join(
                self.source_path, media_file.file_name,
            )
            dst = os.path.join(self.destination_path, media_file.file_name)
            shutil.move(src, dst)


if __name__ == '__main__':
    MediaAccept('PHOTO')()