import os.path
import re
from io import BytesIO

import requests
from dotenv import load_dotenv


class PhotoError(Exception):
    pass


def create_table(path):
    table = []
    photo_pattern = r'^\d+_[123]\.jpeg$'
    video_pattern = r'^\d+_v1\.mp4$'
    for file_name in os.listdir(path):
        barcode = None
        kind = None

        if re.match(photo_pattern, file_name):
            kind = 'photo'
            name, extension = file_name.split('.')
            barcode, angle = name.split('_')
        elif re.match(video_pattern, file_name):
            kind = 'video'
            barcode = file_name.split('_v1.mp4')[0]

        temp_dict = {
            'src_file_name': file_name,
            'src_kind': kind,
            'src_barcode': barcode,
            'src_correct_file_name': bool(barcode),
            'oc_aim': None,
            'oc_article': None,
            'oc_barcode_exists': False,
            'oc_reason': None,
        }
        table.append(temp_dict)
    return table


def make_request(table):
    unique_series = {
        file['src_barcode'] for file in table if file['src_barcode']
    }
    url = os.getenv('PHOTO_RENAMING_URL')
    user = os.getenv('1C_LOGIN')
    password = os.getenv('1C_PASSWORD')
    data = {'series': list(unique_series)}
    response = requests.post(url, json=data, auth=(user, password))
    response.raise_for_status()
    return response.json()


def join_1c_data(table, response_from_1c):
    for table_row in table:
        barcode = table_row['src_barcode']
        if not barcode:
            continue
        response_row = next(
            response_row
            for response_row in response_from_1c
            if response_row.get('ШК') == barcode
        )
        table_row['oc_aim'] = response_row['Трим_Аим']
        table_row['oc_article'] = response_row['Артикул']
        table_row['oc_barcode_exists'] = bool(response_row['Наименование'])
        table_row['oc_reason'] = response_row['Диагностика']


def check_table(table, result):
    wrong_names = []
    wrong_barcodes = []
    for row in table:
        if row['src_file_name'] == '.DS_Store':
            continue
        if not row['src_correct_file_name']:
            wrong_names.append(row['src_file_name'])
        elif not row['oc_barcode_exists']:
            wrong_barcodes.append(row['src_file_name'])

    if wrong_names or wrong_barcodes:
        wrong_names_string = '\n'.join(wrong_names)
        wrong_barcodes_string = '\n'.join(wrong_barcodes)
        if wrong_names_string:
            result['wrong_names'] = BytesIO(wrong_names_string.encode())
        if wrong_barcodes_string:
            result['wrong_barcodes'] = BytesIO(wrong_barcodes_string.encode())
        raise PhotoError('There are photo naming issues')

def get_files_table_from_path(path, result):
    table = create_table(path)
    response_from_1c = make_request(table)
    join_1c_data(table, response_from_1c)
    check_table(table, result)
    return table


def main():
    load_dotenv()

    result = {
        'wrong_names': None,
        'wrong_barcodes': None,
    }

    photo_folder_path = r'PHOTO_SOURCES/SOURCES/PHOTO'
    files_table = get_files_table_from_path(photo_folder_path, result)


if __name__ == '__main__':
    main()
