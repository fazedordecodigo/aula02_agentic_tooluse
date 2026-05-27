.PHONY: up down logs ingest test compile

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api

ingest:
	curl -X POST http://localhost:8000/ingest -H 'Content-Type: application/json' -d '{"load_seed": true}'

test:
	python -m pytest -q

compile:
	python -m compileall app tests scripts boilerplate
