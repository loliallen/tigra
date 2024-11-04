
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

make_release:
    git pull
    docker-compose build web
    docker-compose stop web_run celery
    docker-compose up -d web_run celery
    make clear_space
