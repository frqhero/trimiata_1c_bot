from io import BytesIO


def check_file_names(files_table):
    result = {
        'wrong_names': None,
        'wrong_barcodes': None,
    }

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

    return result
