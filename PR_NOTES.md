### Pull Request: Docker Compose orchestration, env handling, healthchecks, and docs

#### Summary of changes
- Single primary orchestration file `docker-compose.yaml` (dev). Staging/Prod extend from it.
- Unified health endpoints: dev → `GET /healthz`; staging/prod → `GET /readyz` (DB check).
- Fixed DB env priority in `config/settings.py`: `POSTGRES_*` > `DB_*` to prevent `127.0.0.1` in containers.
- Dev Postgres external port changed to `15432:5432` to avoid host conflicts with local PostgreSQL.
- Added `db-backup` sidecar (profile `ops`) for automated Postgres dumps to `./backups`.
- Celery worker healthcheck made portable (Python ping instead of grep).
- README significantly expanded: quick start, Windows/PowerShell guidance to avoid "hanging" terminals, smoke/backup/restore notes.

#### How to run (detached; all commands finish automatically)

Dev:
```
docker compose up -d --build
docker compose ps
# Liveness check
Invoke-WebRequest http://localhost:8000/healthz | % { $_.StatusCode, $_.Content }
```

Staging (close to prod):
```
docker compose -f docker-compose.staging.yml up -d --build --wait
docker compose -f docker-compose.staging.yml ps
# Readiness (checks DB)
Invoke-WebRequest http://localhost:8000/readyz | % { $_.StatusCode, $_.Content }
```

Prod:
```
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

Migrations (one-off command):
```
docker compose run --rm web python manage.py migrate --noinput
```

Logs (short):
```
docker compose logs --tail 100 web
docker compose logs --tail 100 db
```

Smoke and docs:
```
scripts/smoke.ps1 -Url http://localhost:8000
Start-Process http://localhost:8000/api/docs/
```

#### Services and ports
- Backend: 8000 (dev/staging)
- Postgres inside Docker: 5432 always; dev external port: `localhost:15432` → container `5432`
- Redis: 6379
- pgAdmin (dev, profile dev): 5050 → http://localhost:5050
- Flower (dev, profile dev): 5555 → http://localhost:5555

#### Health endpoints
- Dev: `GET /healthz` (simple liveness)
- Staging/Prod: `GET /readyz` (executes `SELECT 1;` against DB)

#### Environment variables
- By default DB engine is Postgres. To force SQLite locally: `DB_ENGINE=sqlite`.
- In Docker use `POSTGRES_*` variables; for native local Postgres use `DB_*`.
- Priority in code: `POSTGRES_*` override `DB_*` inside containers.
- `.env.example` contains all required variables; `.env` is ignored by Git.

#### Backup sidecar (optional)
- Enable automated Postgres dumps:
```
docker compose --profile ops up -d db-backup
docker compose logs -f db-backup
```
- Files appear in `./backups` (gitignored). Keep days/schedule configurable via `.env` (`DB_BACKUP_KEEP_DAYS`, `DB_BACKUP_SCHEDULE`).

#### Mentor checklist
- [ ] `docker-compose.yaml` present in repo root; services: web, db, redis, celery-worker, celery-beat (plus optional pgAdmin/Flower via profile `dev`).
- [ ] Staging/Prod compose files extend the primary; healthchecks: dev→`/healthz`, staging/prod→`/readyz`.
- [ ] `.env.example` is complete; `.env` is ignored (check `.gitignore`).
- [ ] README: clear steps to run via Docker Compose; how to verify each service; port notes.
- [ ] PR description includes commands above, health endpoints, and port notes.

#### Notes for reviewers
- Windows users: use detached `up -d` and one-off `run --rm` to avoid long-running terminal sessions.
- Local Postgres on port 5432 will not conflict; the dev DB is exposed on 15432 instead.
