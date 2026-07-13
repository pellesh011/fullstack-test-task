# Fullstack Test Task — File Processing Service

**Файлообменник с пайплайном параллельной проверки файлов на базе Celery Canvas (group/chord/chain)**

## Стек

| Frontend | Backend |
|----------|---------|
| Next.js 18 (App Router), React 18, TypeScript | Python 3.14, FastAPI, SQLAlchemy 2.0 (async) |
| React-Bootstrap 2, Bootstrap 5 | PostgreSQL (asyncpg), Redis, Celery |
| ESLint (typescript-eslint), no-restricted-imports | Pydantic v2, Alembic, pytest-asyncio |

---

## Архитектура

### Frontend — Feature-Sliced Design (FSD)

```
src/
├── app/                              # Next.js App Router entry
│   ├── layout.tsx
│   └── page.tsx
├── pages/
│   └── files-page/
│       └── ui/FilesPage.tsx          # Page composition: state + widgets
├── widgets/
│   ├── files-widget/
│   │   └── ui/FilesWidget.tsx        # Card + Header + FileTable
│   └── alerts-widget/
│       └── ui/AlertsWidget.tsx       # Card + Header + AlertTable
├── features/
│   ├── file-upload/                  # USER ACTION: upload file
│   │   ├── api/uploadFile.ts         # httpPost → /files
│   │   ├── model/useFileUpload.ts    # useState + upload logic
│   │   └── ui/UploadModal.tsx        # Modal + Form + Progress
│   ├── files-list/                   # LIST FEATURE: files list + polling
│   │   ├── api/fetchFiles.ts         # httpGet → /files + poll 5s
│   │   ├── model/useFiles.ts         # useState + useEffect
│   │   └── ui/FileTable.tsx          # Table with status badges
│   └── alerts-list/                  # LIST FEATURE: task execution issues
│       ├── api/fetchAlerts.ts        # httpGet → /task-executions/issues
│       ├── model/useAlerts.ts        # useState + useEffect
│       └── ui/AlertTable.tsx         # Table with level badges
├── entities/
│   ├── file/
│   │   ├── model/types.ts            # FileItem (SSOT для типа файла)
│   │   └── api/fileApi.ts            # getFiles(), getFile()
│   └── alert/
│       ├── model/types.ts            # AlertItem (SSOT для issue)
│       └── api/alertApi.ts           # getAlerts()
└── shared/
    ├── api/
    │   └── client.ts                 # httpGet, httpPost (infrastructure only)
    ├── config/
    │   └── api.ts                    # API_BASE from env
    ├── lib/
    │   ├── badges.ts                 # getLevelVariant(), getProcessingVariant()
    │   ├── date.ts                   # formatDate()
    │   └── filesize.ts               # formatSize()
    ├── types/
    │   └── entities.ts               # FileItem, AlertItem (shared types)
    └── ui/components/
        ├── LoadingSpinner.tsx
        ├── ErrorAlert.tsx
        └── StatusBadge.tsx
```

**Правила FSD (enforced ESLint `no-restricted-imports`):**
- `entities/*/model/types.ts` — **single source of truth** для типов сущностей
- `shared/api/client.ts` — **только инфраструктура** (`httpGet`, `httpPost`), никакой бизнес-логики
- `features/*` — **пользовательские действия** (`file-upload`) или композиция списков (`files-list`, `alerts-list`)
- `widgets/*` — композиция UI из shared UI + entities
- `pages/*` — композиция виджетов + page-level state
- `app/*` — тонкий entry point

---

### Backend — Clean Architecture

```
backend/src/
├── domain/                           # Чистые доменные модели, интерфейсы
│   ├── entities/
│   │   ├── file.py                   # File — загруженный файл
│   │   ├── processing_task.py        # ProcessingTask — пайплайн обработки
│   │   └── task_execution.py         # TaskExecution — результат одного процессора
│   ├── enums.py                      # FileStatus, ProcessingTaskStatus, ProcessorType, TaskExecutionStatus
│   ├── exceptions.py                 # DomainException, FileNotFoundError, FileEmptyError
│   └── interfaces/
│       ├── repositories.py           # FileRepository, ProcessingTaskRepository, TaskExecutionRepository
│       ├── file_storage.py           # FileStorage (port для хранилища файлов)
│       ├── task_dispatcher.py        # TaskDispatcher (port для диспатча задач)
│       └── metadata_extractor.py     # MetadataExtractor (port для извлечения метаданных)
├── application/                      # Use cases, сервисы
│   ├── services/
│   │   └── file_service.py           # upload, delete, list, get, update — orchestration
│   └── metadata/                     # Извлечение метаданных из файлов
│       ├── extractor_registry.py     # extract_metadata() — оркестратор
│       ├── default_extractor.py      # DefaultMetadataExtractor (fallback)
│       ├── text_extractor.py         # TextMetadataExtractor (text/*)
│       └── pdf_extractor.py          # PdfMetadataExtractor (application/pdf)
├── infrastructure/                   # Реализации интерфейсов
│   ├── database/
│   │   ├── models.py                 # SQLAlchemy ORM модели (File, ProcessingTask, TaskExecution)
│   │   ├── database_manager.py       # DatabaseSessionManager (lazy init, pool)
│   │   └── mappers/
│   │       ├── base.py               # Mapper[EntityT, ModelT] — абстрактный базовый
│   │       ├── file_mapper.py        # File ↔ ORM
│   │       ├── processing_task_mapper.py
│   │       └── task_execution_mapper.py
│   ├── repositories/
│   │   ├── file_repository.py        # SQLFileRepository
│   │   ├── processing_task_repository.py
│   │   └── task_execution_repository.py
│   ├── storage/
│   │   └── local_file_storage.py     # LocalFileStorage (async aiofiles)
│   └── task_dispatcher.py            # CeleryTaskDispatcher — реализация TaskDispatcher
├── presentation/                     # FastAPI слой
│   ├── routes.py                     # Все эндпоинты
│   ├── dependencies.py               # DI: get_file_service, get_task_execution_repo
│   └── main.py                       # FastAPI app, CORS, exception handlers
├── schemas.py                        # Pydantic модели response (FileItem, TaskExecutionIssue)
├── tasks.py                          # Celery tasks + Canvas workflow
├── app.py                            # FastAPI app entry point
└── core/
    └── config.py                     # Pydantic BaseSettings (env-driven)
```

**Поток зависимостей:**
```
presentation → application → domain ← infrastructure
```

---

### Celery Pipeline — Canvas Workflow

Файлы обрабатываются параллельно через **Celery Canvas** (`chord(group(...))(callback)`):

```
start_file_processing (entry point)
    │
    ▼
chord(group(
    metadata_extract,      ─┐
    size_check,             │ parallel
    extension_validator,    │
    mime_validate,          │
    antivirus_scan         ─┘
))(finalize_processing)
    │
    ▼
finalize_processing (aggregates results → sets file.status)
```

**Каждый процессор:**
1. Создаёт `TaskExecution` со статусом `RUNNING`
2. Выполняет проверку
3. Обновляет тот же `TaskExecution` финальным статусом (`SUCCESS`/`WARNING`/`FAILED`)

**`finalize_processing` (chord callback):**
- Получает список результатов от всех процессоров
- Агрегирует статусы: если хотя бы один `FAILED` → файл `FAILED`, если `WARNING` → файл `WARNING`, иначе → `OK`
- Обновляет `ProcessingTask.status` и `File.status`

**Ключевые особенности:**
- `TaskDispatcher` — port/adapter паттерн для декомпозиции application от infrastructure
- `execution_id` передаётся между вызовами `_save_task_execution` для обновления записи вместо создания новой
- `TaskExecutionMapper.to_model()` копирует `id` для корректной работы `session.merge()`

---

### Типы файлов и статусы

**`File.status`:**
| Статус | Описание |
|--------|----------|
| `new` | Файл загружен, ожидает обработки |
| `processing` | Пайплайн запущен |
| `ok` | Все проверки пройдены |
| `warning` | Есть предупреждения (размер, расширение, MIME) |
| `failed` | Есть ошибки |

**`TaskExecution.status`:**
| Статус | Описание |
|--------|----------|
| `pending` | Ожидает запуска |
| `running` | В процессе |
| `success` | Успешно завершено |
| `warning` | Завершено с предупреждениями |
| `failed` | Ошибка |
| `skipped` | Пропущено |

**`ProcessorType`:**
| Процессор | Проверка |
|-----------|----------|
| `metadata_extractor` | Извлечение метаданных (размер, тип, MIME) |
| `size_check` | Сравнение размера с `MAX_FILE_SIZE_MB` |
| `extension_validator` | Проверка расширения на `SUSPICIOUS_EXTENSIONS` |
| `mime_validator` | Сравнение client MIME vs реальный MIME |
| `antivirus_scan` | Антивирусная проверка (заглушка) |

---

## Что сделано

### Backend

| Компонент | Файлы | Ответственность |
|-----------|-------|-----------------|
| `domain` | 6 файлов | Entities, Enums, Exceptions, Interfaces |
| `application` | 5 файлов | FileService, MetadataExtractors |
| `infrastructure` | 9 файлов | SQLAlchemy repos, mappers, LocalFileStorage, CeleryTaskDispatcher |
| `presentation` | 3 файла | FastAPI routes, DI, exception handlers |
| `tasks` | 1 файл | Celery tasks + Canvas workflow |

### Frontend

| Слой | Файлы | Ответственность |
|------|-------|-----------------|
| `app` | 2 файла | Next.js entry |
| `pages` | 1 файл | Страница файлов |
| `widgets` | 2 файла | Compose UI |
| `features` | 9 файлов | Upload, files-list, alerts-list |
| `entities` | 5 файлов | Types + API |
| `shared` | 10 файлов | API client, lib, UI components |

### Исправленные баги

| Баг | Решение |
|-----|---------|
| **Дубли `TaskExecution`** | `to_model()` копирует `id`, `execution_id` передаётся между вызовами |
| **Chord callback arity** | `finalize_processing` принимает `results` как первый аргумент |
| **`apply_async()` на `AsyncResult`** | `chord(...)()` уже диспатчит, повторный вызов не нужен |
| **MIME-spoofing** | `magic.from_buffer(content, mime=True)` — определение по бинарному содержимому |
| **Integer overflow** | `BigInteger` для размера файла |
| **Sync I/O в async** | `aiofiles` для асинхронного чтения/записи |
| **DB connection при импорте** | Lazy init через `DatabaseSessionManager` |
| **Architecture violation** | `TaskDispatcher` port/adapter для декомпозиции от Celery |

---

## Запуск

```bash
# Development (hot reload)
docker compose -f docker-compose.dev.yml up

# Миграции (выполняются автоматически через entrypoint.sh)
docker exec -it backend alembic upgrade head

# Frontend: http://localhost:3000
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

REDIS_URL=redis://redis:63379/0

CORS_ORIGINS=http://localhost:3000
MAX_FILE_SIZE_MB=50
SUSPICIOUS_EXTENSIONS=.exe,.bat,.cmd,.sh,.js,.vbs,.ps1,.jar,.scr,.com,.pif,.msi,.dll,.sys,.apk,.ipa,.deb,.rpm,.appimage

STORAGE_PATH=/app/storage/files
```

### Переменные окружения (frontend)

```env
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Команды разработки

```bash
# Frontend
cd frontend
npm run dev            # Dev server
npm run build          # Production build
npm run lint           # ESLint (FSD rules enforced)

# Backend
cd backend
python -m pytest -v    # Run tests (23 tests)
alembic upgrade head   # Run migrations
alembic revision --autogenerate -m "message"  # Create migration
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/files` | Список файлов |
| `POST` | `/files` | Загрузка файла (multipart form) |
| `GET` | `/files/{id}` | Получить файл |
| `PATCH` | `/files/{id}` | Обновить название |
| `DELETE` | `/files/{id}` | Удалить файл |
| `GET` | `/files/{id}/download` | Скачать файл |
| `GET` | `/task-executions/issues` | Проблемные проверки (не success) |
| `GET` | `/health` | Health check |
