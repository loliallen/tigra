FROM python:3.8.20-alpine3.20

## install dependencies for psycopg2
RUN apk update \
    && apk add libpq-dev gcc make\
    && pip install psycopg2

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install pip-tools
COPY Makefile /code/
RUN make install-prod

COPY . /code/
RUN python manage.py collectstatic
