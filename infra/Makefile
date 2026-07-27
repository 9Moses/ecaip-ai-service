.PHONY: up down logs ps restart-api

up:
	docker compose --env-file .env -f docker-compose.yml up -d --build

down:
	docker compose -f docker-compose.yml down

logs:
	docker compose -f docker-compose.yml logs -f

ps:
	docker compose -f docker-compose.yml ps

restart-api:
	docker compose -f docker-compose.yml restart api