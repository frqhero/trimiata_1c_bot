FROM python:3.11.5-slim

WORKDIR /code

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY main.py main.py
COPY photo_renaming.py photo_renaming.py
COPY find_photos_with_same_article.py find_photos_with_same_article.py

CMD python main.py
