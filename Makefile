.PHONY: help setup sigaas backend db ps migrate seed down reset

# Default target when running just 'make'
help:
	@echo "SIGAAS Docker Management Shortcuts:"
	@echo "  make setup    - Iniciar stack, aplicar migracoes e popular banco de dados"
	@echo "  make sigaas   - Iniciar toda a stack (DB, Backend, Frontend, Cron) em segundo plano"
	@echo "  make backend  - Iniciar apenas o Backend e Banco de Dados"
	@echo "  make db       - Iniciar apenas o Banco de Dados"
	@echo "  make ps       - Listar status dos containers"
	@echo "  make migrate  - Executar as migracoes do banco de dados (Alembic)"
	@echo "  make seed     - Executar script de povoamento inicial de dados (idempotente)"
	@echo "  make down     - Parar e remover todos os containers"
	@echo "  make reset    - Resetar ambiente (remove dados/volumes do banco e reinicia a stack)"

setup:
	docker compose up -d
	docker compose exec -T backend alembic upgrade head
	docker compose exec -T backend python /scripts/seed_db.py

sigaas:
	docker compose up -d

backend:
	docker compose up -d backend

db:
	docker compose up -d db

ps:
	docker compose ps

migrate:
	docker compose exec -T backend alembic upgrade head

seed:
	docker compose exec -T backend python /scripts/seed_db.py

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up -d
