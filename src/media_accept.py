import os
import re
import shutil

import requests

from env_settings import settings
from pydantic_models import PhotoRenamingResponse


class ValidationError(Exception):
    def __init__(self, errors):
        message = '\n'.join(errors)
        if isinstance(errors, str):
            message = errors
        super().__init__(message)


class MediaFile:
    photo_pattern = r'^\d+_[123]\.jpeg$'
    video_pattern = r'^\d+_v1\.mp4$'

    def __init__(self, parent, file_name: str):
        self.parent = parent
        self.file_name = file_name
        self.barcode = file_name.split('_')[0]

    def __eq__(self, other):
        if isinstance(other, str):
            return self.file_name == other
        raise NotImplemented

    def __hash__(self):
        return hash(self.file_name)

    def __str__(self):
        return self.file_name

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.parent)}, {repr(self.file_name)})'

    @property
    def is_pattern_correct(self):
        return re.match(self.photo_pattern, self.file_name) or re.match(self.video_pattern, self.file_name)

    def report_wrong_pattern(self):
        return f'The filename {self.file_name} doesn\'t match the allowed patterns'

    def report_incorrect_barcode(self):
        return f'The barcode {repr(self.barcode)} from {repr(self.file_name)} doesn\'t exist in 1C'

    def move(self, src_path, dst_path):
        src = os.path.join(src_path, self.file_name)
        dst = os.path.join(dst_path, self.file_name)
        shutil.move(src, dst)

class AcceptMedia:
    def __init__(self):
        self.media_sources_path = settings.MEDIA_SOURCES_PATH
        self.url = settings.PHOTO_RENAMING_URL
        self.login = settings.LOGIN_1C
        self.password = settings.PASSWORD_1C
        self.src_photo_path = os.path.join(settings.MEDIA_SOURCES_PATH, 'PHOTO_TEAM', 'PHOTO')
        self.src_video_path = os.path.join(settings.MEDIA_SOURCES_PATH, 'PHOTO_TEAM', 'VIDEO')
        self.dst_photo_path = os.path.join(settings.MEDIA_SOURCES_PATH, 'SOURCES', 'PHOTO')
        self.dst_video_path = os.path.join(settings.MEDIA_SOURCES_PATH, 'SOURCES', 'VIDEO')
        self.photo_files = []
        self.video_files = []
        self.errors = []

    def __call__(self, *args, **kwargs):
        self.populate_photos()
        self.populate_videos()
        if not self.photo_files and not self.video_files:
            raise ValidationError('No new files to accept')
        # validate
        self.new_files_arent_existing_names()
        self.check_file_name_patterns()
        self.check_barcodes_exist()

        self.raise_for_errors()
        self.move_files()

    def populate_photos(self):
        self.photo_files = [MediaFile(self, file_name) for file_name in os.listdir(self.src_photo_path)]

    def populate_videos(self):
        self.video_files = [MediaFile(self, file_name) for file_name in os.listdir(self.src_video_path)]

    def new_files_arent_existing_names(self):
        existing_filenames = os.listdir(self.dst_photo_path)
        existing_filenames += os.listdir(self.dst_video_path)
        for media_file in self.photo_files + self.video_files:
            if media_file in existing_filenames:
                self.errors.append(f'The file name {repr(str(media_file))} already exists in the source folder')

    def check_file_name_patterns(self):
        for media_file in self.photo_files + self.video_files:
            if not media_file.is_pattern_correct:
                self.errors.append(media_file.report_wrong_pattern())

    def check_barcodes_exist(self):
        barcodes = set([media_file.barcode for media_file in self.photo_files + self.video_files])
        data = {'series': list(barcodes)}
        response = requests.post(self.url, json=data, auth=(self.login, self.password))
        response.raise_for_status()
        request_result = PhotoRenamingResponse(response=response.json()).response
        existing_barcodes = set([row.name for row in request_result if row.name])
        for media_file in self.photo_files + self.video_files:
            if media_file.barcode not in existing_barcodes:
                self.errors.append(media_file.report_incorrect_barcode())

    def raise_for_errors(self):
        if self.errors:
            raise ValidationError(self.errors)

    def move_files(self):
        for photo_file in self.photo_files:
            photo_file.move(self.src_photo_path, self.dst_photo_path)

        for video_file in self.video_files:
            video_file.move(self.src_video_path, self.dst_video_path)


if __name__ == '__main__':
    a = AcceptMedia()()
