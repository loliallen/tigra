
lock:
	pip-compile --generate-hashes --no-emit-index-url --allow-unsafe

lock-dev:
	pip-compile --generate-hashes --no-emit-index-url --allow-unsafe requirements_dev.in

install-dev:
	pip-sync requirements.txt requirements_dev.txt --pip-args '--no-deps'

install-prod:
	pip-sync requirements.txt --pip-args '--no-deps'

clear_space:
	docker image prune -f
	docker container prune -f

build:
	git pull
	docker compose build web

release:
	make build
	docker compose stop web_run celery celery_beat
	make clear_space
	docker compose up -d web_run celery celery_beat

release_bot:
	make build
	docker compose stop telegram_bot_run
	make clear_space
	docker compose up -d telegram_bot_run

dump:
	docker exec -it tigra-db-1 sh -c "pg_dump db > dump.sql"
	docker cp tigra-db-1:/dump.sql dump.sql
	curl -X POST "https://api.telegram.org/7045683304:AAH8Ur-lA8BAW48DCUrveoYc0QLUrNxfnxk/sendDocument?chat_id=-4597530598" --form "document=@dump.sql;type=text/csv" -H "Content-Type: multipart/form-data"

load_dump:
	docker cp ~/dump.sql tigra-db-1:/dump.sql
	docker exec -it tigra-db-1 sh -c "psql db < dump.sql"

rm_dump:
	rm media/dump.sql