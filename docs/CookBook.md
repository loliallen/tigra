# Локальное разворачивание 
1) Установить зависимости (python 3.8)
```bash
pip install requirements.txt
```
2) Cоздать в корне `.env` файл на основе `.env.example`
3) Cоздать в корне `creds.json` (доступы в firebase,
генерируются в [консоли firebase](https://console.firebase.google.com)
в разделе `Project Settings` -> `Service Account` -> `Generate 
new private key`)
4) Развернуть локально базу:
```bash
docker-compose up -d db
```
5) Накатить миграции
```bash
python manage.py migrate
```
6) Запустить:
```bash
python manage.py runserver 0.0.0.0:8000
```

# Первый запуск на сервере
1) Спулить репозиторий
```bash
git clone ...
```
2) Cоздать в корне `.env` файл на основе `.env.example` 
и придумать стойкие пароли и секретные ключи
3) Cоздать в корне `creds.json` - доступы в firebase,
генерируются в [консоли firebase](https://console.firebase.google.com)
в разделе `Project Settings` -> `Service Account` -> `Generate 
new private key`
4) Собрать билд
```bash
docker-compose build web
```
5) Развернуть локально базу:
```bash
docker-compose up -d db
```
6) Накатить миграции
```bash
docker-compose up web_migrate
```
7) Запустить
```bash
docker-compose up -d web_run
```
## Обновить версию на сервере
1) Спулить последние изменения
```bash
git pull
```
2) Собрать новый билд
```bash
docker-compose build web
```
3) Остновить сервер
```bash
docker-compose stop web_run
```
4) Накатить миграции если надо
```bash
docker-compose up web_migrate
```
5) Запустить сервер
```bash
docker-compose up -d web_run
```
