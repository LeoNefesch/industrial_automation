# industrial_automation — мини-SCADA на Python

Pet-проект по теме «Python в промышленной автоматизации»: упрощённая SCADA-система для сбора данных с промышленного оборудования.
Демонстрирует сбор данных по Modbus TCP, хранение временных рядов в TimescaleDB, систему алармов с гистерезисом и квитированием, а также веб-панель (HMI) с трендами на Bokeh. Архитектура разделена на независимые сервисы сбора данных и визуализации.

---

## Что делает проект

1. **Собирает измерения с Modbus TCP-устройства** (симулятор на `pymodbus`) и сохраняет их в TimescaleDB. Этим занимается отдельный сервис `worker`.
2. **Проверяет уставки алармов** на каждом новом измерении. Аларм имеет состояние (`NORMAL`, `ACTIVE_UNACK`, `ACTIVE_ACK`), приоритет и гистерезис (deadband), чтобы не «дребезжать» около порога.
3. **Ведёт журнал событий (Event Log)**: все переходы состояний алармов сохраняются в таблицу `alarm_events` в базе данных.
4. **Позволяет квитировать алармы** через REST API (`POST /api/alarms/{sensor_id}/ack`). Квитирование фиксирует пользователя и время — как в настоящей SCADA.
5. **Планирует сбор данных через APScheduler** внутри воркера. Задачи изолированы от веб-сервера, что исключает их дублирование при масштабировании.
6. **Отображает тренды в Bokeh**. Веб-сервис (`web`) раз в 2 секунды опрашивает БД на предмет новых данных и обновляет графики без перезагрузки страницы.
7. **Демонстрирует архитектурные слои**: DAO, services, usecases, Unit of Work, настройки через `pydantic-settings`, миграции Alembic.

---

## Стек

| Слой | Технология |
|---|---|
| ASGI-сервер | Granian |
| Веб-фреймворк | FastAPI |
| Планировщик | APScheduler (`AsyncIOScheduler`) |
| БД | PostgreSQL 18 + TimescaleDB |
| Драйвер БД | `asyncpg` + SQLAlchemy 2.x (async) |
| Миграции | Alembic (async) |
| Настройки | `pydantic-settings` |
| Визуализация | Bokeh |
| Промышленный протокол | `pymodbus` (Modbus TCP) |
| Управление зависимостями | uv |
| Контейнеризация | Docker + docker-compose |

---

## Архитектура

Проект разделён на два независимых процесса, использующих общую базу данных и один Docker-образ.

```text
┌──────────────────────────────────────────────────────────────┐
│                         worker (APScheduler)                 │
│  ModbusDataSource ──► CollectAndStoreUseCase ──► TimescaleDB │
│                            │                                 │
│                            ▼                                 │
│                       AlarmManager ───────────► alarm_events │
└──────────────────────────────────────────────────────────────┘
                                │
                         (Единая БД)
                                │
┌──────────────────────────────────────────────────────────────┐
│                         web (FastAPI + Bokeh)                │
│                                                              │
│  GET /api/alarms ──────► Список алармов                      │
│  POST /api/alarms/{id}/ack ──► Квитирование                  │
│                                                              │
│  _poll_and_push() ──► SELECT из TimescaleDB ──► Bokeh HMI    │
└──────────────────────────────────────────────────────────────┘
```

**Ключевые компоненты:**

- **`worker`** — автономный процесс. Раз в `INTERVAL_SECONDS` читает регистры Modbus, сохраняет данные в БД, прогоняет их через `AlarmManager` и записывает возникшие события алармов в `alarm_events`.
- **`web`** — FastAPI-приложение. Содержит эндпойнты для работы с алармами и веб-сервер Bokeh. В фоне работает корутина `_poll_and_push`, которая забирает свежие данные из БД и обновляет графики в активных сессиях браузера.
- **TimescaleDB** — historian: гипертаблица `measurements` (для метрик) и таблица `alarm_events` (для журнала событий). В качестве первичного ключа в `alarm_events` используется нативный `uuidv7()` (доступен в PostgreSQL 18), что обеспечивает монотонность и быструю вставку.

---

## Структура проекта

```text
industrial_automation/
├── alarms/                      # Домен алармов
│   ├── config.py                # Уставки (high, low, deadband)
│   ├── manager.py               # Конечный автомат, обработка гистерезиса
│   └── models.py                # Alarm, AlarmState, AlarmEventRecord
├── api/                         # REST API (FastAPI роутеры)
│   ├── alarms.py                # Эндпойнты алармов
│   ├── bokeh.py                 # Монтирование Bokeh ASGI и редирект
│   └── __init__.py              # Сборка всех роутеров
├── core/                        # Ядро и конфигурация
│   ├── constants.py
│   ├── data_source.py           # Protocol SensorDataSource
│   ├── logger.py
│   └── settings.py              # pydantic-settings
├── dao/                         # Data Access Objects
│   ├── base.py                  # ABC для DAO
│   ├── measurement.py           # Работа с measurements
│   └── alarm_event.py           # Работа с alarm_events
├── db/                          # Слой базы данных
│   ├── models.py                # SQLAlchemy модели
│   └── session.py               # async engine + session factory
├── dependencies/
│   └── uow.py                   # Unit of Work
├── migrations/                  # Alembic (async)
├── protocols/                   # Промышленные протоколы
│   ├── modbus_client.py         # Реализация Modbus TCP
│   └── opcua_client.py          # Заготовка для OPC UA
├── scripts/
│   ├── apply_migrations.sh      # Миграции при старте
│   └── modbus_sim.py            # Симулятор Modbus-устройства
├── services/                    # Сервисный слой
│   ├── measurement_service.py
│   └── alarm_event_service.py
├── usecases/                    # Сценарии использования (Use Cases)
│   ├── collect_and_store.py     # Сбор и сохранение данных
│   └── save_alarm_events.py     # Сохранение событий алармов
├── visual/
│   └── bokeh_app.py             # HMI: создание графиков и BokehASGI
├── main.py                      # Точка входа FastAPI (web)
├── worker.py                    # Точка входа воркера (сбор данных)
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── alembic.ini
```

---

## Запуск

### 1. Подготовка

Требуется установленный Docker и Docker Compose v2.

```bash
git clone <repo-url> industrial_automation
cd industrial_automation
cp .env.example .env
```

### 2. Запуск в Docker

```bash
docker compose up --build -d
```

Поднимутся следующие сервисы:

| Сервис | Назначение | Порт |
|---|---|---|
| `timescaledb` | Historian (PostgreSQL 18 + TimescaleDB) | 5432 |
| `web` | FastAPI + HMI (Bokeh) | 8000 |
| `worker` | Фоновый сбор данных и проверка алармов | — |
| `modbus-sim` | Симулятор датчиков (Modbus TCP) | 502 |
| `opcua-sim` | Заготовка OPC UA-сервера | 4840 |

> **Важно:** проект использует PostgreSQL 18 (образ `timescale/timescaledb:latest-pg18-oss`). Том с данными монтируется в `/var/lib/postgresql` (а не `.../data`), так как с 18-й версии изменилась структура каталогов. Это позволяет использовать функцию `uuidv7()` для генерации ID событий.

### 3. Создание и применение миграций

Миграции применяются автоматически при старте контейнера `web` через скрипт `apply_migrations.sh`.

Если вы изменили модели SQLAlchemy, создайте новую миграцию, выполнив команду в работающем контейнере:
```bash
docker compose exec web alembic revision --autogenerate -m "описание изменений"
```
Или в одноразовом (чтобы не зависеть от состояния основного):
```bash
docker compose run --rm --entrypoint="" web alembic revision --autogenerate -m "описание"
```

После создания миграции перезапустите `web` (или выполните `alembic upgrade head`), чтобы применить её.

### 4. Остановка

```bash
docker compose down          # остановить контейнеры
docker compose down -v       # остановить и удалить том с данными
```

---

## Что и где наблюдать

### Веб-интерфейс (HMI) — `http://localhost:8000`

Автоматический редирект на `/bokeh/plot`. Вы увидите два графика (температура и влажность), обновляющихся в реальном времени по мере поступления данных из БД.

### API Алармов

- **Получить статус всех алармов:**
  `GET http://localhost:8000/api/alarms`
- **Квитировать аларм (Acknowledge):**
  `POST http://localhost:8000/api/alarms/temperature/ack?user=operator`
  *Если аларм активен и ещё не квитирован, вернёт `{"ok": true}`.*

### Логи

```bash
docker compose logs -f worker  # Логи сбора данных и алармов
docker compose logs -f web     # Логи FastAPI и Bokeh
```

### Данные в БД

Подключение извне (DBeaver, psql):
- host: `localhost`, port: `5432`
- database: `industrial`, user: `postgres`, password: `postgres`

Проверка журнала алармов:
```bash
docker compose exec timescaledb psql -U postgres -d industrial \
  -c "SELECT time, sensor_id, event, value FROM alarm_events ORDER BY time DESC LIMIT 10;"
```

---

## Разработка

### Установка окружения (без Docker)
```bash
uv sync
```

### Форматирование и проверка типов
```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
```

---

## TODO

### Реальный сбор данных и протоколы
- [ ] Реализовать интеграцию по протоколу **OPC UA** с использованием `asyncua` (сейчас есть только клиент-заготовка).
- [ ] Реализовать логику ретраев (retry) и таймаутов при обрыве соединения с физическим оборудованием.
- [ ] Поддержать чтение с реального устройства (Modbus RTU / USB-RS485).

### Визуализация (HMI)
- [ ] **Мнемосхема оборудования**: реализовать визуализацию технологического процесса (как в настоящей SCADA) с использованием библиотек вроде `pyscada` (или Drawflow/GoJS для фронтенда).
- [ ] Настройка диапазона времени на графиках через query-параметры: `?start=...&end=...`.
- [ ] Отображение списка активных алармов и журнала событий прямо на веб-странице (вместо чтения логов).

### Данные и аналитика
- [ ] Непрерывные агрегаты TimescaleDB: средние/мин/макс за минуту, час, сутки для ускорения загрузки графиков.
- [ ] Политика сжатия (compression) и удаления (retention policy) старых чанков.
- [ ] Интеграция уведомлений во внешние системы (Telegram, Email) при `ACTIVE_UNACK` дольше N минут.

### Качество
- [ ] Тесты: unit для `AlarmManager` (граничные случаи гистерезиса), integration через `testcontainers`.
- [ ] Метрики Prometheus (счётчик записанных измерений, латентность).
- [ ] CI на GitHub Actions: `ruff` + `mypy` + `pytest`.
- [ ] Healthcheck-endpoint `/healthz` (проверка БД и Modbus).

### Архитектура
- [ ] Поддержка нескольких источников данных с общим интерфейсом `DataSource` (Modbus + OPC UA + MQTT).
- [ ] Plugin-механизм для подключения новых протоколов без изменения ядра.
