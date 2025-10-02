.PHONY: up down run test

up: 
	docker compose -f docker/docker-compose.yml up -d --build

down: 
	docker compose -f docker/docker-compose.yml down -v

run: 
	uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8080

test: 
	pytest -q