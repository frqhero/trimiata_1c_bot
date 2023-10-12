import os
import re
import shutil
import time
from datetime import datetime
from io import BytesIO

import requests
from dotenv import load_dotenv


class PhotoError(Exception):
    pass


def timestamp_to_datetime(timestamp):
    dt_obj = datetime.fromtimestamp(timestamp)
    formatting = '%d.%m.%Y %H:%M:%S'
    return dt_obj.strftime(formatting)


def create_files_table(src_path):
    table = []
    pattern = r'^\d+_[123]\.jpeg$'

    for file_name in os.listdir(src_path):
        if file_name == '.DS_Store':
            continue
        full_path_file_name = os.path.join(src_path, file_name)
        created_at = os.path.getctime(full_path_file_name)
        angle = None
        barcode = None

        if re.match(pattern, file_name):
            name, extension = file_name.split('.')
            barcode, angle = name.split('_')

        current_line = {
            'file_name': file_name,
            'created_at': created_at,
            'datetime': timestamp_to_datetime(created_at),
            'barcode': barcode,
            'angle': int(angle) if angle else angle,
            'aim': None,
            'series': None,
            'metal': None,
            'reason': None
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
    print(url, user, password, sep='\n')
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
        line['aim'] = found_dict['Трим_Аим']
        line['series'] = found_dict['Наименование']
        line['metal'] = found_dict['Металл']
        line['reason'] = found_dict['Диагностика']


def check_file_names(files_table, result):
    wrong_names = []
    wrong_barcodes = []
    for file_name in files_table:
        if not file_name['barcode']:
            wrong_names.append(file_name['file_name'])
        elif not file_name['series']:
            wrong_barcodes.append(file_name['file_name'])

    if wrong_names or wrong_barcodes:
        wrong_names_string = '\n'.join(wrong_names)
        wrong_barcodes_string = '\n'.join(wrong_barcodes)
        if wrong_names_string:
            result['wrong_names'] = BytesIO(wrong_names_string.encode())
        if wrong_barcodes_string:
            result['wrong_barcodes'] = BytesIO(wrong_barcodes_string.encode())
        raise PhotoError('There are photo naming issues')


def create_aim_table(files_table):
    unique_aims = {
        file_name['aim'] for file_name in files_table if file_name['aim']
    }

    aim_table = []
    for aim in unique_aims:
        new_line = {
            'aim': aim,
            'angle1': [],
            'angle2': [],
            'angle3': [],
        }
        for file_name in (
            file_name for file_name in files_table if file_name['aim'] == aim
        ):
            if file_name['angle'] == 1:
                new_line['angle1'].append(file_name)
            elif file_name['angle'] == 2:
                new_line['angle2'].append(file_name)
            elif file_name['angle'] == 3:
                new_line['angle3'].append(file_name)

        new_line['angle1'].sort(key=lambda x: x['created_at'], reverse=True)
        new_line['angle2'].sort(key=lambda x: x['created_at'], reverse=True)
        new_line['angle3'].sort(key=lambda x: x['created_at'], reverse=True)
        aim_table.append(new_line)
    return aim_table


def empty_destination(dst_path):
    for file_name in os.listdir(dst_path):
        full_path = os.path.join(dst_path, file_name)
        os.remove(full_path)


def rename(aim_table, src_path, dst_path, result):
    result['photo_number_before'] = len(os.listdir(dst_path))
    empty_destination(dst_path)
    start = time.time()
    for aim in aim_table:
        if aim['angle1']:
            photo_file = aim['angle1'][0]
            src = os.path.join(src_path, photo_file['file_name'])
            new_file_name = f'{aim["aim"]}_1.jpeg'
            dst = os.path.join(dst_path, new_file_name)
            shutil.copy2(src, dst)
        if aim['angle2']:
            photo_file = aim['angle2'][0]
            src = os.path.join(src_path, photo_file['file_name'])
            new_file_name = f'{aim["aim"]}_2.jpeg'
            dst = os.path.join(dst_path, new_file_name)
            shutil.copy2(src, dst)
        if aim['angle3']:
            photo_file = aim['angle3'][0]
            src = os.path.join(src_path, photo_file['file_name'])
            new_file_name = f'{aim["aim"]}_3.jpeg'
            dst = os.path.join(dst_path, new_file_name)
            shutil.copy2(src, dst)
    end = time.time()
    result['renaming_duration'] = f'{end - start:.0f}'
    result['photo_number_after'] = len(os.listdir(dst_path))


def provide_report(files_table):
    series_doesnt_have_aim = [
        file_name for file_name in files_table if not file_name['aim']
    ]
    return series_doesnt_have_aim


def main():
    load_dotenv()

    photo_sources_path = os.getenv('PHOTO_SOURCES_PATH')
    src_path = os.path.join(photo_sources_path, 'SOURCES/PHOTO')
    dst_path = os.path.join(photo_sources_path, 'RENAMED/PHOTO')

    result = {
        'wrong_names': None,
        'wrong_barcodes': None,
        'photo_number_before': None,
        'photo_number_after': None,
        'renaming_duration': None,
        'report': None,
        'exception': None,
    }

    try:
        files_table = create_files_table(src_path)

        request_result = make_request(files_table)
        join_1c_data(files_table, request_result)

        check_file_names(files_table, result)

        aim_table = create_aim_table(files_table)

        rename(aim_table, src_path, dst_path, result)

        result['report'] = provide_report(files_table)
        return result
    except Exception as e:
        result['exception'] = str(e)
        return result


if __name__ == '__main__':
    main()
