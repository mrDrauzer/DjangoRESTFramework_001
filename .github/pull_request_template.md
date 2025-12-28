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

### Данные деплоя
- Хост/домен: `http(s)://<host>`
- Health-check prod: `http(s)://<host>/readyz` (ожидается HTTP 200)

### Скриншоты/логи (по возможности)
- 

### Чек‑лист
- [ ] В коммит не попал `.env` и другие игнорируемые файлы
- [ ] Обновлён `README.md` при изменениях запуска/переменных окружения
- [ ] Локально собралось и поднялось через `docker compose`
- [ ] CI зелёный: lint, tests, smoke
- [ ] Для прод‑изменений: создан бэкап БД (при необходимости) и описана процедура проверки
 - [ ] Секреты в GitHub Actions: `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `APP_DIR` (опц. `SSH_PORT`, `DEPLOY_PRUNE`)
 - [ ] В Actions прошли `tests` и выполнился `deploy` только после тестов
 - [ ] После деплоя `/readyz` возвращает 200; проверены логи `web`/`nginx` (и `celery-*` при наличии)
