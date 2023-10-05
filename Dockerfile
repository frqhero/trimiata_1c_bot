from python:3.11.5-slim

workdir /code

copy requirements.txt requirements.txt
run pip install -r requirements.txt
copy .env .env
copy main.py main.py

cmd python3 main.py