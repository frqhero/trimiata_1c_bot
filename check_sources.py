import os
import re

import requests
from dotenv import load_dotenv

from auxiliary_tools import check_file_names


def create_files_table(src_path, kind):
    table = []
    if kind == 'PHOTO':
        pattern = r'^\d+_[123]\.jpeg$'
    else:
        pattern = r'^\d+_v1.mp4$'

    for file_name in os.listdir(src_path):
        if file_name == '.DS_Store':
            continue

        barcode = None

        if re.match(pattern, file_name):
            name, extension = file_name.split('.')
            barcode, angle = name.split('_')

        current_line = {
            'file_name': file_name,
            'barcode': barcode,
            'series': None,
        }
        table.append(current_line)
    return table


def make_request(files_table):
    unique_series = {
        file_name['barcode']
        for file_name in files_table
        if file_name['barcode']
    }
    url = os.getenv('PHOTO_RENAMING_URL')
    user = os.getenv('1C_LOGIN')
    password = os.getenv('1C_PASSWORD')
    data = {'series': list(unique_series)}
    response = requests.post(url, json=data, auth=(user, password))
    response.raise_for_status()
    return response.json()


def join_1c_data(files_table, request_result):
    for line in files_table:
        barcode = line['barcode']
        if not barcode:
            continue
        found_dict = next(
            item for item in request_result if item.get('ШК') == barcode
        )
        line['series'] = found_dict['Наименование']


def main():
    load_dotenv()

    result = {
        'PHOTO': None,
        'VIDEO': None,
    }

    photo_sources_path = os.getenv('PHOTO_SOURCES_PATH')
    photo_path = os.path.join(photo_sources_path, 'SOURCES/PHOTO')
    video_path = os.path.join(photo_sources_path, 'SOURCES/VIDEO')

    photo_files_table = create_files_table(photo_path, 'PHOTO')
    request_result = make_request(photo_files_table)
    join_1c_data(photo_files_table, request_result)
    result['PHOTO'] = check_file_names(photo_files_table)

    video_files_table = create_files_table(video_path, 'VIDEO')
    request_result = make_request(video_files_table)
    join_1c_data(video_files_table, request_result)
    result['VIDEO'] = check_file_names(photo_files_table)

    return result


if __name__ == '__main__':
    main()
