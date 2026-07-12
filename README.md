# Fullstack Test Task — File Sharing Service

**MVP файлообменника с проверкой файлов на подозрительный контент и системой алертов**

## Стек

| Frontend | Backend |
|----------|---------|
| Next.js 15 (Turbopack), React 18, TypeScript | Python 3.12, FastAPI, SQLAlchemy 2.0 (async) |
| React-Bootstrap 2, Bootstrap 5 | PostgreSQL (asyncpg), Redis, Celery |
| ESLint (typescript-eslint), no-restricted-imports | Pydantic Settings, Alembic, pytest-asyncio |

---

## Архитектура

### Frontend — Feature-Sliced Design (FSD)

```
src/
├── app/                          # Next.js App Router entry
│   └── page.tsx                  # Thin entry → imports FilesPage
├── pages/
│   └── files-page/
│       └── ui/FilesPage.tsx      # Page composition: state + widgets
├── widgets/
│   ├── files-widget/
│   │   ├── ui/FilesWidget.tsx    # Card + Header + FileTable
│   │   └── ui/FileTable.tsx      # Table with UploadModal + AlertBadge
│   └── alerts-widget/
│       ├── ui/AlertsWidget.tsx
│       └── ui/AlertTable.tsx
├── features/
│   ├── file-upload/              # USER ACTION: upload file
│   │   ├── api/uploadFile.ts     # httpPost → /files/upload
│   │   ├── model/useFileUpload.ts# useState + upload logic
│   │   └── ui/UploadModal.tsx    # Modal + Form + Progress
│   ├── files-list/               # LIST FEATURE: files list + polling
│   │   ├── api/useFiles.ts       # httpGet → /files + poll 5s
│   │   └── model/useFiles.ts     # useState + useEffect
│   └── alerts-list/              # LIST FEATURE: alerts list + polling
│       ├── api/useAlerts.ts
│       └── model/useAlerts.ts
├── entities/
│   ├── file/
│   │   ├── model/types.ts        # FileItem (SSOT для типа файла)
│   │   └── api/fileApi.ts        # getFiles(), getFile() — entity API
│   └── alert/
│       ├── model/types.ts        # AlertItem (SSOT для алерта)
│       └── api/alertApi.ts       # getAlerts()
└── shared/
    ├── api/
    │   ├── client.ts             # httpGet, httpPost (infrastructure only)
    │   └── config/api.ts         # API_BASE from env
    ├── ui/                       # Button, Card, Table, Modal, Badge, Spinner
    ├── config/env.ts             # Env validation
    └── lib/utils.ts              # cn(), formatBytes(), formatDate()
```

**Правила FSD (enforced ESLint `no-restricted-imports`):**
- `entities/*/model/types.ts` — **single source of truth** для типов сущностей
- `shared/api/client.ts` — **только инфраструктура** (`httpGet`, `httpPost`), никакой бизнес-логики
- `features/*` — только **пользовательские действия** (`file-upload`) или композиция списков (`files-list`, `alerts-list`)
- `widgets/*` — композиция UI из shared UI + entities
- `pages/*` — композиция виджетов + page-level state
- `app/*` — тонкий entry point

---

### Backend — Clean Architecture

```
backend/src/
├── domain/                       # Чистая доменные модели, интерфейсы
│   ├── entities/                 # StoredFile, Alert, ScanResult (domain entities)
│   ├── interfaces/
│   │   ├── repositories.py       # FileRepository, AlertRepository, ScanResultRepository
│   │   ├── storage.py            # FileStorage
│   │   └── scanner.py            # ScanCheck (strategy)
│   └── value_objects.py          # FileId, MimeType, FileSize
├── application/                  # Use cases, сервисы, DTO
│   ├── services/
│   │   ├── file_service.py       # upload, delete, list, get — orchestration
│   │   ├── alert_service.py      # create alerts from scan results
│   │   └── scanner/
│   │       ├── checks/           # 8 проверок (extension, size, mime, magic, pdf, text, executable, archive)
│   │       ├── orchestrator.py   # последовательный запуск чеков
│   │       └── service.py        # ScannerService
│   └── dto.py                    # FileCreate, FileUpdate, AlertCreate, ScanResultCreate
├── infrastructure/               # Реализации интерфейсов
│   ├── database/
│   │   ├── models/               # SQLAlchemy ORM модели (table definitions)
│   │   ├── mappers/              # Domain↔ORM мапперы (FileMapper, AlertMapper, ScanResultMapper)
│   │   ├── session.py            # DatabaseSessionManager (lazy init, pool)
│   │   └── repositories/         # SQLFileRepository, SQLAlertRepository, SQLScanResultRepository
│   ├── storage/
│   │   └── local_storage.py      # LocalFileStorage (atomic write, safe delete)
│   ├── scanner/checks/           # Реализации ScanCheck
│   └── celery/                   # Celery app, tasks, worker loop
├── presentation/                 # FastAPI слой
│   ├── api/
│   │   ├── routes/
│   │   │   ├── files.py          # POST/GET/DELETE /files, POST /files/upload
│   │   │   ├── alerts.py         # GET /alerts
│   │   │   └── scan_results.py   # GET /files/{id}/scan-results
│   │   ├── schemas.py            # Pydantic модели request/response
│   │   └── dependencies.py       # get_file_service, get_alert_service, get_scanner_service
│   └── main.py                   # FastAPI app, lifespan, CORS, exception handlers
├── core/
│   └── config.py                 # Pydantic BaseSettings (env-driven)
```

**Поток зависимостей:**
```
presentation → application → domain ← infrastructure
```

---

## Что сделано — Frontend

| Было | Стало |
|------|-------|
| 2 файла: `page.tsx` (600+ строк) + `api.ts` | FSD слои: `app/pages/widgets/features/entities/shared` |
| Все типы в `shared/types/entities.ts` | Типы в `entities/*/model/types.ts` (SSOT) |
| `shared/api/files.ts` с бизнес-логикой | `shared/api/client.ts` — только `httpGet`/`httpPost` |
| Хуки в компонентах | Хуки вынесены в `features/*/model/` |
| Прямые импорты куда угодно | ESLint `no-restricted-imports` блокирует нарушения слоёв |
| `useState`/`useEffect` в компонентах | Сохранено (по требованию) |
| React-Bootstrap | Сохранено (по требованию) |

**Ключевые файлы:**
- `eslint.config.mjs` — правила FSD границ
- `tsconfig.json` — `@/*` алиасы, `strictNullChecks: true`
- `package.json` — добавлен `lint` скрипт

---

## Что сделано — Backend

### Архитектурный рефакторинг

| Слой | Файлы | Ответственность |
|------|-------|-----------------|
| `domain` | 8 файлов | Entities, Value Objects, Repository interfaces |
| `application` | 15+ файлов | Services, Use Cases, DTO, Scanner (8 checks + orchestrator) |
| `infrastructure` | 12+ файлов | SQLAlchemy repos, LocalFileStorage, Celery tasks |
| `presentation` | 8 файлов | FastAPI routes, Pydantic schemas, DI, exception handlers |

### Исправленные баги

| Баг | Было | Стало |
|-----|------|-------|
| **Потеря данных при удалении** | `unlink()` → `delete()` → `commit()` — если commit упадёт, файл потерян | `flush()` → `unlink()` → при ошибке `rollback()` → `commit()` только при успехе |
| **MIME-spoofing** | `upload_file.content_type` (клиент врал) | `magic.from_buffer(content, mime=True)` — определение по бинарному содержимому |
| **`scan_details` — плоская строка** | Одна строка на 500 символов, обрезалась | Таблица `scan_results` — каждая проверка отдельная строка в `Text` |
| **Integer overflow для размера** | `Integer` (max ~2.1 GB) | `BigInteger` (max ~9.2 EB) |
| **`scan_details` не существует** | Код писал в `scan_details`, но поле удалено | Пишет в `ScanResult` с `check_name="metadata_extraction"` |
| **Sync I/O в async** | `Path.read_bytes()`, `write_bytes()` блокируют event loop | `aiofiles` для асинхронного чтения/записи |
| **Небезопасное удаление** | `unlink()` без проверки владельца, race condition | Проверка `stored_name` + атомарная транзакция |
| **Небезопасные tmp директории** | `tempfile.gettempdir()` (world-writable) | `tempfile.mkdtemp(dir=secure_dir, prefix=...)` |
| **Нет обработки ошибок сканера** | Ошибка сканера крашит задачу Celery | Try/except в каждом чеке, статус `failed`, алерт `critical` |
| **DB connection при импорте** | Создаётся при импорте модуля, крашится без env | Lazy init через `DatabaseSessionManager.dispose()` |
| **Redis без reconnection** | Прямой `.delay()` без обработки ошибок | Celery task retry + брокер управляет соединением |
| **CORS хардкод** | `localhost:3000` | `CORS_ORIGINS` env var |

### Безопасность

- **MIME validation**: 80+ расширений в `KNOWN_MIME_TYPES` + сравнение `original_mime_type` (от клиента) vs реальный MIME
- **Подозрительные расширения**: `SUSPICIOUS_EXTENSIONS` env var (было 5 захардкоженных)
- **Max file size**: `MAX_FILE_SIZE_MB` env var (было `10 * 1024 * 1024` в коде)

### Новые фичи

- `GET /files/{id}/scan-results` — детальные результаты сканирования
- `original_mime_type` — аудит client MIME vs реальный MIME
- Alembic миграции (4 версии: init, scan_results, alerts, drop unique constraint)
- `AlertService` с детальными сообщениями из scan results

### Тесты

~1500 строк тестов, 6 файлов: `test_service.py`, `test_repositories.py`, `test_scanner.py`, `test_schemas.py`, `test_storage.py`, `test_config.py` (pytest-asyncio)

---

## Запуск

```bash
# Development (hot reload)
docker compose -f docker-compose.dev.yml up

# Миграции
docker exec -it backend alembic upgrade head

# Frontend: http://localhost:3000/test
# Backend API: http://localhost:8000/docs
```

### Переменные окружения (backend)

```env
# .env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_DB=fileshare
PGPORT=5432

REDIS_URL=redis://redis:6379/0

CORS_ORIGINS=http://localhost:3000
MAX_FILE_SIZE_MB=50
SUSPICIOUS_EXTENSIONS=.exe,.bat,.cmd,.sh,.js,.vbs,.ps1,.jar,.scr,.com,.pif,.msi,.dll,.sys,.apk,.ipa,.deb,.rpm,.appimage
KNOWN_MIME_TYPES=... (80+ типов)

STORAGE_PATH=/app/storage/files
SCANNER_DELAY_SECONDS=2
```

### Переменные окружения (frontend)

```env
# frontend/.env.local
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

## Команды разработки

```bash
# Frontend
cd frontend
npm run dev        # Turbopack dev server
npm run build      # Production build
npm run lint       # ESLint (FSD rules enforced)

# Backend
cd backend
pytest -v          # Run tests
alembic upgrade head
alembic revision --autogenerate -m "message"
```

---

## Git History (key commits)

```
frontend-fds-layers:
  681f46f - FSD restructuring: app/pages/widgets/features/entities/shared
  (ESLint no-restricted-imports, types in entities/*/model/types.ts)

clean-architecture (backend):
  - Clean Architecture restructure (domain/app/infra/presentation)
  - 12+ bug fixes (MIME spoofing, sync I/O, atomic delete, scan_results table)
  - Security hardening (env-driven config, magic MIME detection)
  - ~1500 lines tests

clean-architecture-models:
  - Moved ORM models from src/models.py → src/infrastructure/database/models/
  - Domain entities separate from SQLAlchemy models
  - Removed unique constraint on scan_results (file_id, check_name) — multiple results per check allowed
  - 113 tests pass

celery-task-queue:
  - Removed custom Redis pub/sub event bus (redis_event_bus.py, subscriber.py)
  - Direct Celery task invocation: FileService → scan_file_for_threats.delay()
  - Celery handles broker abstraction (Redis/RabbitMQ via CELERY_BROKER_URL)
  - 175 lines removed, 113 tests pass
```

---

## Полезные ссылки

- [FSD Methodology](https://feature-sliced.design/)
- [Clean Architecture (Python)](https://github.com/cosmic-python/code)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)