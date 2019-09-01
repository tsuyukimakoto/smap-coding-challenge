clean:
	rm -r -f ../.tmp/*

migrate:
	python manage.py migrate --database=default

loaddata:
	python manage.py loaddata area.yaml
	python manage.py loaddata tariff.yaml

install_dependancies:
	pip install -r ../requirements.txt

init: clean install_dependancies migrate loaddata

build_messages:
	python manage.py compilemessages --locale ja

build: build_messages

all: build