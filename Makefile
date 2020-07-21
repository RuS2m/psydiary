init:
	pip3 install -r requirements.txt

db:
	@echo shutting down docker with database if exists
	docker-compose down
	sleep 3
	@echo raising up docker with database
	docker-compose up -d
	sleep 5
	@echo applying data from dump
	psql -h localhost -d db -U admin -q < init.sql

start:
	make init
	make db
	@echo starting service...
	python3 bot.py

restart:
	python3 bot.py

help:
	@echo "Available targets:"
	@echo "- init       Install all required for project libraries"
	@echo "- db         Init database with data from dump"
	@echo "- start      Start service"
	@echo "- restart    Restart service"
