import os
import re
import shutil
import time
from io import BytesIO

import requests
from telegram import Update

from env_settings import settings


class TablePhotoRename:
    url = settings.PHOTO_RENAMING_URL
    user = settings.LOGIN_1C
    password = settings.PASSWORD_1C

    columns = (
        'file_name',
        'created_at',
        'barcode',
        'angle',
        'aim',
        'series',
        'metal',
        'reason',
    )
    result_fields = (
        'wrong_file_names',
        'wrong_barcodes',
        'exception',
        'photo_number_before',
        'renaming_duration',
        'photo_number_after',
        'series_without_aim',
    )

    def __init__(self, document):
        self.document = document
        self.src_path = document.src_path
        self.dst_path = document.dst_path
        self.kind = document.kind
        self.table = []
        if self.kind == 'PHOTO':
            self.pattern = r'^\d+_[123]\.jpeg$'
            self.extension = 'jpeg'
        elif self.kind == 'VIDEO':
            self.pattern = r'^\d+_v1\.mp4$'
            self.extension = 'mp4'
        self.response_json = None
        self.wrong_file_names = None
        self.wrong_barcodes = None
        self.aim_table = []
        self.photo_number_before = 0
        self.renaming_duration = ''
        self.photo_number_after = 0

    def populate_table(self):
        for file_name in os.listdir(self.src_path):
            if file_name == '.DS_Store':
                continue

            new_row = {column: None for column in self.columns}
            new_row['file_name'] = file_name
            new_row['created_at'] = os.path.getctime(
                os.path.join(self.src_path, file_name),
            )

            if re.match(self.pattern, file_name):
                name, _extension = file_name.split('.')
                barcode, angle = name.split('_')
                angle = angle.replace('v', '')

                new_row['barcode'] = barcode
                new_row['angle'] = int(angle)

            self.table.append(new_row)

    def make_request(self):
        unique_series = {
            file_name['barcode']
            for file_name in self.table
            if file_name['barcode']
        }
        data = {'series': list(unique_series)}
        response = requests.post(self.url, json=data, auth=(self.user, self.password))
        response.raise_for_status()
        self.response_json = response.json()

    def join_response_json(self):
        for row in self.table:
            barcode = row['barcode']
            if not barcode:
                continue
            found_dict = next(
                item
                for item in self.response_json
                if item.get('ШК') == barcode
            )
            row['aim'] = found_dict['Трим_Аим']
            row['series'] = found_dict['Наименование']
            row['metal'] = found_dict['Металл']
            row['reason'] = found_dict['Диагностика']

    def validate_table(self):
        self.wrong_file_names = [
            row['file_name'] for row in self.table if not row['barcode']
        ]
        self.wrong_barcodes = [
            row['file_name']
            for row in self.table
            if row['barcode'] and not row['series']
        ]

    @property
    def has_errors(self):
        return bool(self.wrong_file_names or self.wrong_barcodes)

    def get_result(self):
        response = {field: None for field in self.result_fields}
        if self.has_errors:
            response['exception'] = True
        if self.wrong_file_names:
            response['wrong_file_names'] = ', '.join(self.wrong_file_names)
        if self.wrong_barcodes:
            response['wrong_barcodes'] = ', '.join(self.wrong_barcodes)
        if self.response_json:
            response['series_without_aim'] = [
                row for row in self.table if not row['aim']
            ]
        response['photo_number_before'] = self.photo_number_before
        response['renaming_duration'] = self.renaming_duration
        response['photo_number_after'] = self.photo_number_after

        return response

    def create_aim_table(self):
        unique_aims = {row['aim'] for row in self.table if row['aim']}

        for aim in unique_aims:
            new_row_aim = {
                'aim': aim,
                'angle1': [],
                'angle2': [],
                'angle3': [],
            }
            for file_name in self.table:
                if file_name['aim'] != aim:
                    continue
                if file_name['angle'] == 1:
                    new_row_aim['angle1'].append(file_name)
                elif file_name['angle'] == 2:
                    new_row_aim['angle2'].append(file_name)
                elif file_name['angle'] == 3:
                    new_row_aim['angle3'].append(file_name)

            new_row_aim['angle1'].sort(
                key=lambda x: x['created_at'], reverse=True,
            )
            new_row_aim['angle2'].sort(
                key=lambda x: x['created_at'], reverse=True,
            )
            new_row_aim['angle3'].sort(
                key=lambda x: x['created_at'], reverse=True,
            )
            self.aim_table.append(new_row_aim)

    def rename(self):
        self.photo_number_before = len(os.listdir(self.dst_path))
        self.empty_destination()
        start = time.time()
        for aim in self.aim_table:
            if aim['angle1']:
                photo_file = aim['angle1'][0]
                src = os.path.join(self.src_path, photo_file['file_name'])
                if self.kind == 'PHOTO':
                    new_file_name = f'{aim["aim"]}_1.{self.extension}'
                elif self.kind == 'VIDEO':
                    new_file_name = f'{aim["aim"]}_v1.{self.extension}'
                dst = os.path.join(self.dst_path, new_file_name)
                shutil.copy2(src, dst)
            if aim['angle2']:
                photo_file = aim['angle2'][0]
                src = os.path.join(self.src_path, photo_file['file_name'])
                new_file_name = f'{aim["aim"]}_2.{self.extension}'
                dst = os.path.join(self.dst_path, new_file_name)
                shutil.copy2(src, dst)
            if aim['angle3']:
                photo_file = aim['angle3'][0]
                src = os.path.join(self.src_path, photo_file['file_name'])
                new_file_name = f'{aim["aim"]}_3.{self.extension}'
                dst = os.path.join(self.dst_path, new_file_name)
                shutil.copy2(src, dst)
        end = time.time()
        self.renaming_duration = f'{end - start:.0f}'
        self.photo_number_after = len(os.listdir(self.dst_path))

    def empty_destination(self):
        for file_name in os.listdir(self.dst_path):
            full_path = os.path.join(self.dst_path, file_name)
            os.remove(full_path)


class DocumentPhotoRename:
    def __init__(self, src_path, dst_path, kind):
        self.kind = kind
        self.src_path = src_path
        self.dst_path = dst_path
        self.result = None

    def start(self):
        table = TablePhotoRename(self)
        table.populate_table()
        table.make_request()
        table.join_response_json()
        table.validate_table()
        if table.has_errors:
            self.result = table.get_result()
        table.create_aim_table()
        table.rename()
        self.result = table.get_result()


class RenamePhotos:
    """Rename telegram entry point."""
    media_sources_path = settings.MEDIA_SOURCES_PATH

    def __init__(self, update: Update, kind: str):
        self.kind = kind.upper()
        if self.kind not in ('PHOTO', 'VIDEO'):
            raise ValueError('kind should be PHOTO or VIDEO')
        self.temp_message = update.message.reply_text('Renaming started...')
        self.src_path = os.path.join(self.media_sources_path, 'SOURCES', self.kind)
        self.dst_path = os.path.join(self.media_sources_path, 'RENAMED', self.kind)
        self.result = None

    def start(self):
        document = DocumentPhotoRename(self.src_path, self.dst_path, self.kind)
        document.start()
        self.result = document.result
        if self.result['exception']:
            self.report_errors()
        else:
            self.send_result()

    def report_errors(self):
        self.temp_message.edit_text('Renaming failed.')
        if self.result['wrong_file_names']:
            self.temp_message.reply_document(
                BytesIO(self.result['wrong_file_names'].encode()),
                'wrong_file_names.txt',
            )
        if self.result['wrong_barcodes']:
            self.temp_message.reply_document(
                BytesIO(self.result['wrong_barcodes'].encode()),
                'wrong_barcodes.txt',
            )

    def send_result(self):
        self.temp_message.edit_text(
            'The renaming operation was successfully completed.\n'
            f'It took {self.result["renaming_duration"]} seconds.\n'
            f'Before the operation, the destination folder contained {self.result["photo_number_before"]} files, '
            f'and it has {self.result["photo_number_after"]} files afterward.',
        )
