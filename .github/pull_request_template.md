### Что сделано
- 

### Как запустить
- Dev: `docker compose up -d --build`
- Staging: `docker compose -f docker-compose.staging.yml up -d --build`
- Prod: `docker compose -f docker-compose.prod.yml up -d --build`

### Как проверить
- Health: `GET /healthz` (dev), `GET /readyz` (staging/prod)
- Swagger: `GET /api/docs/`
- Celery: `docker compose logs -f celery-worker`

### Скриншоты/логи (по возможности)
- 

### Чек‑лист
- [ ] В коммит не попал `.env` и другие игнорируемые файлы
- [ ] Обновлён `README.md` при изменениях запуска/переменных окружения
- [ ] Локально собралось и поднялось через `docker compose`
- [ ] CI зелёный: lint, tests, smoke
- [ ] Для прод‑изменений: создан бэкап БД (при необходимости) и описана процедура проверки
