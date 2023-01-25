FROM arm32v7/python:3.8-buster

WORKDIR /home

ENV TZ=Europe/Moscow

RUN apt-get update
RUN pip install --upgrade pip
COPY requirements.txt .
# RUN pip install -r requirements.txt

COPY *.py ./
COPY *.env ./
RUN touch db/database.db
RUN pip install aiogram==2.24
RUN pip install aiohttp==3.8.3
RUN pip install aiosignal==1.3.1
RUN pip install async-timeout==4.0.2
RUN pip install attrs==22.2.0
RUN pip install Babel==2.9.1
RUN pip install certifi==2022.12.7
RUN pip install charset-normalizer==2.1.1
RUN pip install frozenlist==1.3.3
RUN pip install greenlet==2.0.1
RUN pip install idna==3.4
RUN pip install importlib-metadata==6.0.0
RUN pip install importlib-resources==5.10.2
RUN pip install magic-filter==1.0.9
RUN pip install Mako==1.2.4
RUN pip install MarkupSafe==2.1.2
RUN pip install multidict==6.0.4
RUN pip install psycopg2==2.9.5
RUN pip install pytz==2022.7.1
RUN pip install SQLAlchemy==1.4.46
RUN pip install yarl==1.8.2
RUN pip install zipp==3.11.0
CMD [ "python", "main.py" ]