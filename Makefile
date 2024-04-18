up:
	docker compose -f infra/docker-compose.yaml -p trimiata_1c_bot up --build
down:
	docker compose -f infra/docker-compose.yaml -p trimiata_1c_bot down
upd:
	docker compose -f infra/docker-compose.yaml -p trimiata_1c_bot up --build -d
lint: ## Проверяет линтером код в репозитории
	docker compose -f .linters/docker-compose.yaml run -T --rm linters flake8 /src/