up:
	docker compose -f infra/docker-compose.yaml -p trimiata_1c_bot up --build
down:
	docker compose -f infra/docker-compose.yaml -p trimiata_1c_bot down
upd:
	docker compose -f infra/docker-compose.yaml -p trimiata_1c_bot up --build -d
