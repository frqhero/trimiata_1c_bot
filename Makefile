up:
	docker compose -f infra/docker-compose.yaml up --build
down:
	docker compose -f infra/docker-compose.yaml down
upd:
	docker compose -f infra/docker-compose.yaml up --build -d