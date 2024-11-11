
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

release:
	git pull
	docker-compose build web
	docker-compose stop web_run celery
	docker-compose up -d web_run celery
	make clear_space

dump:
	docker exec -it tigra_db_1 sh -c "pg_dump db > dump.sql"
	docker cp tigra_db_1:/dump.sql media/dump.sql

load_dump:
    docker cp ~/dump.sql tigra_db_1:/dump.sql
    docker exec -it tigra_db_1 sh -c "psql db < dump.sql"

rm_dump:
	rm media/dump.sql