SHELL := /bin/sh

.PHONY: up up-dev up-prod up-staging down down-prod ps logs restart-worker restart-beat migrate shell createsuperuser test lint backup-db restore-db restore-drill smoke

up:
	docker compose up -d --build

up-dev:
	docker compose --profile dev up -d --build

up-prod:
	docker compose -f docker-compose.prod.yml up -d --build

up-staging:
	docker compose -f docker-compose.staging.yml up -d --build

down:
	docker compose down

down-prod:
	docker compose -f docker-compose.prod.yml down

ps:
	docker compose ps

logs:
	@if [ -z "$(s)" ]; then \
		echo "Usage: make logs s=<service> (e.g., s=web)"; \
	else \
		docker compose logs -f $(s); \
	fi

restart-worker:
	docker compose restart celery-worker

restart-beat:
	docker compose restart celery-beat

migrate:
	docker compose exec web python manage.py migrate --noinput

shell:
	docker compose exec web python manage.py shell

createsuperuser:
	docker compose exec web python manage.py createsuperuser

test:
	DB_ENGINE=sqlite python -m pytest -v

lint:
	ruff check . && black --check . && isort --profile black --check-only .

backup-db:
	@mkdir -p backups
	@echo "Creating PostgreSQL custom-format dump into backups/ ..."
	@docker compose exec -T db sh -lc 'pg_dump -U "$POSTGRES_USER" -Fc -Z 9 "$POSTGRES_DB"' > backups/backup_`date +%Y%m%d_%H%M%S`.dump
	@echo "Done. Files in ./backups:"
	@ls -1 backups | tail -n 5


restore-db:
	@if [ -z "$(f)" ]; then \
		echo "Usage: make restore-db f=backups/<file>.dump"; \
		exit 1; \
		fi
	@echo "Restoring PostgreSQL (drop/create schema) from $(f) ..."
	@cat $(f) | docker compose exec -T db sh -lc 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists -v'
	@echo "Restore completed."

smoke:
	@if [ -z "$(url)" ]; then \
		bin="scripts/smoke.sh"; \
		chmod +x $$bin 2>/dev/null || true; \
		$$bin http://localhost:8000; \
	else \
		bin="scripts/smoke.sh"; \
		chmod +x $$bin 2>/dev/null || true; \
		$$bin $(url); \
	fi

# Restore drill: verify a dump by restoring into a temporary database inside the db container
restore-drill:
	@set -e; \
	TMP_DB="restore_drill_`date +%Y%m%d_%H%M%S`"; \
	echo "[restore-drill] Temporary DB: $$TMP_DB"; \
	if [ -z "$(f)" ]; then \
		LATEST=$$(ls -1t backups/*.dump 2>/dev/null | head -n1); \
		if [ -z "$$LATEST" ]; then echo "No dump file found in backups/. Provide f=backups/<file>.dump"; exit 1; fi; \
		DUMP_FILE="$$LATEST"; \
	else \
		DUMP_FILE="$(f)"; \
		if [ ! -f "$$DUMP_FILE" ]; then echo "Dump file not found: $$DUMP_FILE"; exit 1; fi; \
	fi; \
	echo "[restore-drill] Using dump: $$DUMP_FILE"; \
	echo "[restore-drill] Creating database ..."; \
	docker compose exec -T db sh -lc 'createdb -U "$POSTGRES_USER" "$TMP_DB"' || { echo "Failed to create DB"; exit 1; }; \
	echo "[restore-drill] Restoring dump into $$TMP_DB ... this may take a while"; \
	cat "$$DUMP_FILE" | docker compose exec -T db sh -lc 'pg_restore -U "$POSTGRES_USER" -d "$$TMP_DB" --clean --if-exists -v' || { echo "Restore failed"; docker compose exec -T db sh -lc 'dropdb -U "$POSTGRES_USER" "$$TMP_DB"' || true; exit 1; }; \
	echo "[restore-drill] Basic checks ..."; \
	docker compose exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$$TMP_DB" -c "SELECT 1;"' || { echo "SELECT 1 failed"; }; \
	# Try to count migrations table if present
	docker compose exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$$TMP_DB" -c "SELECT count(*) AS django_migrations FROM django_migrations;"' || echo "[restore-drill] Table django_migrations not found (ok if dump is app-specific)"; \
	echo "[restore-drill] Dropping temporary database ..."; \
	docker compose exec -T db sh -lc 'dropdb -U "$POSTGRES_USER" "$$TMP_DB"' || { echo "Failed to drop temporary DB $$TMP_DB"; exit 1; }; \
	echo "[restore-drill] OK"
