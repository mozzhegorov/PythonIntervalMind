FROM arm32v7/python:3.8-buster

WORKDIR /home

ENV TZ=Europe/Moscow

RUN apt-get update
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py ./
COPY *.env ./
RUN touch db/database.db

CMD [ "python", "main.py" ]