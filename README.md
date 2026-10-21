# industrial_automation — мини-SCADA на Python

Pet-проект по теме «Python в промышленной автоматизации»: упрощённая SCADA-система для одного датчика.
Демонстрирует сбор данных по Modbus TCP, хранение временных рядов в TimescaleDB, систему алармов с гистерезисом и квитированием,
планировщик задач на APScheduler и веб-панель с трендами.

---

## Что делает проект

1. **Собирает измерения с Modbus TCP-устройства** (симулятор на `pymodbus`) и сохраняет их в TimescaleDB.
2. **Проверяет уставки алармов** на каждом новом измерении. Аларм имеет состояние (`NORMAL`, `ACTIVE_UNACK`, `ACTIVE_ACK`), приоритет и гистерезис (deadband), чтобы не «дребезжать» около порога.
3. **Позволяет квитировать алармы** через REST API (`POST /api/alarms/{sensor_id}/ack`). Квитирование фиксирует пользователя и время — как в настоящей SCADA.
4. **Планирует сбор данных через APScheduler**, а не через ручной `asyncio.sleep`. Интервал и расписание можно менять без правки бизнес-логики.
5. **Отображает тренды в Bokeh** и обновляет их в реальном времени через `dashboard.push(...)`.
6. **Демонстрирует архитектурные слои**: DAO, services, usecases, Unit of Work, настройки через `pydantic-settings`, миграции Alembic.

---

## Стек

| Слой | Технология |
|---|---|
| ASGI-сервер | Granian |
| Веб-фреймворк | FastAPI |
| Планировщик | APScheduler (`AsyncIOScheduler`) |
| БД | PostgreSQL + TimescaleDB |
| Драйвер БД | `asyncpg` + SQLAlchemy 2.x (async) |
| Миграции | Alembic (async) |
| Настройки | `pydantic-settings` |
| Визуализация | Bokeh |
| Промышленный протокол | `pymodbus` (Modbus TCP) |
| Управление зависимостями | uv |
| Контейнеризация | Docker + docker-compose |

---

## Архитектура

┌─────────────┐ Modbus TCP ┌──────────────────┐
│ modbus-sim │ ◄────────────────── │ ModbusDataSource │
└─────────────┘ └────────┬─────────┘
│ read_all()
▼
┌─────────────────────┐
│ CollectAndStoreUseCase│
└──────────┬──────────┘
│
┌───────────────────────┼───────────────────────┐
▼ ▼ ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ MeasurementService│ │ AlarmManager │ │ BokehDashboard │
│ (historian) │ │ (alarms/events) │ │ (HMI/trends) │
└────────┬──────────┘ └────────┬─────────┘ └─────────────────┘
│ │
▼ ▼
┌─────────────────┐ ┌─────────────────┐
│ TimescaleDB │ │ alarm_events │
│ (measurements) │ │ (event log) │
└─────────────────┘ └─────────────────┘

**Ключевые компоненты:**

- **`AlarmManager`** — конечный автомат алармов. Хранит активные алармы в памяти, пишет события в журнал.
- **`APScheduler`** — запускает `collect_and_check` каждые `INTERVAL_SECONDS`. Позже сюда добавляются retention-задачи и cron-агрегаты.
- **`BokehDashboard`** — HMI с трендами. Для реального времени использует `push()`; альтернатива — WebSocket.
- **TimescaleDB** — historian: гипертаблица `measurements` с партиционированием по времени.

---

## Структура

```
industrial_automation/
├── alarms/
│ ├── models.py # Alarm, AlarmState
│ ├── manager.py # AlarmManager: process(), acknowledge()
│ └── config.py # Уставки алармов
├── api/
│ └── alarms.py # REST для списка и квитирования
├── core/
│ ├── constants.py
│ ├── data_source.py                 # Protocol SensorDataSource
│ ├── logger.py
│ └── settings.py                    # Глобальный экземпляр Settings
├── db/
│   ├── models.py                    # SQLAlchemy-модель Measurement
│   └── session.py                   # async engine + session factory
├── dao/
│   ├── base.py                      # ABC MeasurementDAO
│   └── measurement.py               # Реализация
├── services/measurement_service.py  # Сервисный слой
├── usecases/collect_and_store.py
├── dependencies/uow.py              # Unit of Work с автокоммитом
├── protocols/
│   ├── modbus_client.py             # Заготовка pymodbus (async)
│   └── opcua_client.py              # Заготовка asyncua
├── visual/bokeh_app.py              # Bokeh
├── migrations/                      # Alembic (async)
├── main.py                          # Starlette app + фоновая задача
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
└── .env.example
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
docker compose up --build
```

Поднимутся четыре контейнера:

| Сервис | Назначение | Порт |
|---|---|---|
| `timescaledb` | Historian (TimescaleDB) | 5432 |
| `app` | ASGI-приложение с генератором и веб-интерфейсом | 8000 |
| `modbus-sim` | Modbus TCP симулятор (в текущей версии не используется) | 5020 |
| `opcua-sim` | OPC UA симулятор (в текущей версии не используется) | 4840 |

### 3. Применение миграций

Миграции применяются в скрипте [apply_migrations.sh](scripts/apply_migrations.sh)

Проверка гипертаблицы:

```bash
docker compose exec timescaledb psql -U postgres -d industrial -c \
  "SELECT hypertable_name FROM timescaledb_information.hypertables;"
```

Ожидаемый вывод:

```
 hypertable_name
-----------------
 measurements
```

### 4. Остановка

```bash
docker compose down          # остановить контейнеры
docker compose down -v       # остановить и удалить том с данными
```

---

## Что и где наблюдать

### Веб-интерфейс — `http://localhost:8000`

Одна страница с тремя графиками Plotly (по одному на датчик): `temperature`, `pressure`, `flow_rate`. Данные за последний час.

При первом заходе сразу после старта может показаться «Нет данных» — фоновый генератор пишет первую партию через ~1 секунду после запуска. Обновите страницу.

### Логи генератора

```bash
docker compose logs -f app
```

### Данные в БД

Подключение извне (DBeaver, psql):

- host: `localhost`
- port: `5432`
- database: `industrial`
- user: `postgres`
- password: `postgres`

Проверка количества строк:

```bash
docker compose exec timescaledb psql -U postgres -d industrial \
  -c "SELECT sensor_id, count(*), max(time) FROM measurements GROUP BY sensor_id;"
```

Список чанков гипертаблицы:

```bash
docker compose exec timescaledb psql -U postgres -d industrial \
  -c "SELECT chunk_name, range_start, range_end FROM timescaledb_information.chunks;"
```

---

## Разработка

### Установка окружения

```bash
uv sync
```

### Генерация новой миграции

```bash
uv run alembic revision --autogenerate -m "описание"
```

После автогенерации **обязательно просмотрите файл вручную** — Alembic не понимает `create_hypertable` и не умеет отслеживать изменения гипертаблиц. Если миграция создаёт новую таблицу для временных рядов, добавьте в `upgrade()`:

```python
op.execute(
    "SELECT create_hypertable('<table>', '<time-column>', if_not_exists => TRUE)"
)
```

### Форматирование и типы

```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
```

### Тесты

Пока отсутствуют. Моковые тесты для DAO и сервисов — в TODO.

---

## Конфигурация

Все настройки читаются из `.env` через `pydantic-settings`. Префиксы:

- `DB_*` — подключение к БД
- `MODBUS_*` — параметры Modbus-клиента
- `OPCUA_*` — параметры OPC UA-клиента

Значения по умолчанию заданы в `core/settings.py` и подходят для запуска через `docker-compose.yml` без `.env`.

---

## TODO

### Реальный сбор данных

- [ ] Переключить `GenerateAndStoreUseCase` на `CollectAndStoreUseCase`, который читает с Modbus и OPC UA.
- [ ] Заменить тестовые симуляторы в `docker-compose.yml` на рабочие образы: сейчас `oitc/modbus-server` слушает порт 5020, а не 502; `intel/ia-opcua-server` ждёт отсутствующий сервис. Подобрать альтернативы или поднять локальные симуляторы на `pymodbus`/`asyncua`.
- [ ] Реализовать ретраи и таймауты при обрыве соединения с устройствами.
- [ ] Поддержать чтение с физического датчика (например, через Modbus RTU / USB-RS485).

### Веб-интерфейс

- [ ] Диапазон времени настраивать через query-параметры: `?start=...&end=...`.
- [ ] Отдельная страница с детальным графиком одного датчика.
- [ ] Кнопка «Экспорт в CSV / XLSX».

### Данные и аналитика

- [ ] Непрерывные агрегаты TimescaleDB: средние/мин/макс за минуту, час, сутки.
- [ ] Политика сжатия и retention policy для старых чанков.
- [ ] Алерты: уведомление при выходе значения за пределы диапазона.
- [ ] Таблица `sensors` со справочником датчиков (единицы измерения, границы, описание).

### Качество

- [ ] Тесты: unit для DAO/сервисов, integration через `testcontainers` или in-memory SQLite.
- [ ] Структурированное логирование через `structlog`.
- [ ] Метрики Prometheus (счётчик записанных измерений, латентность запросов).
- [ ] CI на GitHub Actions: `ruff` + `mypy` + `pytest`.
- [ ] Healthcheck-endpoint `/healthz`.

### Архитектура

- [ ] Поддержка нескольких источников данных с общим интерфейсом `DataSource` (Modbus, OPC UA, MQTT).
- [ ] Plugin-механизм для подключения новых протоколов без изменения ядра.
