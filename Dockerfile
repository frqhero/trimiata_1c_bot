FROM python:3.11.5-slim

WORKDIR /opt/code

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD python main.py
