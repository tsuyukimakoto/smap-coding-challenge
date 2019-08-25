clean:
	rm -r -f ../.tmp/*

migrate:
	python manage.py migrate --database=default

install_dependancies:
	pip install -r ../requirements.txt

init: clean install_dependancies migrate

build_messages:
	python manage.py compilemessages --locale ja

build: build_messages

all: build