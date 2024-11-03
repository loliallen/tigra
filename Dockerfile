FROM python:3.8-slim-buster

## install dependencies for psycopg2
RUN apt-get update \
    && apt-get -y install libpq-dev gcc make\
    && pip install psycopg2

RUN mkdir /code
WORKDIR /code
COPY requirements.txt Makefile /code/
RUN pip install pip-tools
RUN make install-prod

COPY . /code/
RUN python manage.py collectstatic
