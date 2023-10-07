import os

import requests
from dotenv import load_dotenv


def main():
    load_dotenv()
    url = os.getenv('PHOTO_RENAMING_URL')
    user = os.getenv('1C_LOGIN')
    password = os.getenv('1C_PASSWORD')
    print(url, user, password, sep='\n')
    data = {'series': ['509657']}
    response = requests.post(url, json=data, auth=(user, password))
    response.raise_for_status()


if __name__ == '__main__':
    main()
