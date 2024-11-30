# Локальное разворачивание 
1) Установить зависимости (python 3.8)
```bash
pip install pip-tools
make install-dev
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
4) Собрать билд и запустить все сервисы
```bash
make release
```

## Обновить версию на сервере
```bash
make release
```

## Если заканчивается место
- проверить сколько места осталось `df -h`
- список всех image `docker images ls`
- удалить конкретный image `docker rmi <id>`
- удалить все остановленные контейнеры `docker container prune`
- удалить все неиспользуемые контейнеры, имаджи, сети и тд `docker system prune`