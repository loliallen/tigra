FROM python:3.8-slim-buster

## install dependencies for psycopg2
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
