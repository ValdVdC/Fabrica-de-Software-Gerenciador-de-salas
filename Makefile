.PHONY: help sigaas backend db down reset

# Default target when running just 'make'
help:
	@echo "SIGAAS Docker Management Shortcuts:"
	@echo "  make sigaas   - Start the entire stack (DB, Backend, Frontend, Cron) in the background"
	@echo "  make backend  - Start only the Backend and Database"
	@echo "  make db       - Start only the Database"
	@echo "  make down     - Stop and remove all containers"
	@echo "  make reset    - Reset the environment (stop containers, delete volumes/database data, and restart all)"

sigaas:
	docker compose up -d

backend:
	docker compose up -d backend

db:
	docker compose up -d db

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up -d
