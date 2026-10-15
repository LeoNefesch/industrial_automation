# industrial_automation

Pet-проект по теме «Python в промышленной автоматизации». Демонстрирует чистую архитектуру, работу с временными рядами в TimescaleDB, асинхронные протоколы промышленной автоматизации и визуализацию на Python-стеке.

---

## Что делает проект

1. **Генерирует поток измерений** — фоновый цикл раз в 5 секунд создаёт по одному случайному значению для каждого датчика из списка `["temperature", "pressure", "flow_rate"]`.
2. **Пишет их в TimescaleDB** — измерения сохраняются в гипертаблицу `measurements`, партиционированную по колонке `time`. TimescaleDB автоматически создаёт чанки по времени и позволяет эффективно запрашивать диапазоны.
3. **Отдаёт веб-страницу с графиками** — по адресу `http://localhost:8000` отображаются тренды всех датчиков за последний час, построенные через Plotly.
4. **Демонстрирует архитектурные слои**: DAO (абстракция + реализация), services, usecases, Unit of Work, settings через `pydantic-settings`, миграции через Alembic.
5. **Содержит заготовки** для чтения с реальных протоколов: `pymodbus` для Modbus TCP и `asyncua` для OPC UA. В текущей версии поток данных идёт от `RandomSimulator`, а не от этих клиентов — они оставлены в `protocols/` как отправная точка для следующего шага.

---

## Стек

| Слой | Технология |
|---|---|
| ASGI-сервер | Granian |
| Веб-фреймворк | Starlette |
| БД | PostgreSQL + TimescaleDB (образ `timescale/timescaledb:latest-pg16`) |
| Драйвер БД | `asyncpg` через SQLAlchemy 2.x (async) |
| Миграции | Alembic (async-шаблон) |
| Настройки | `pydantic-settings` |
| Визуализация | Plotly (интерактивная), Matplotlib (статические отчёты) |
| Промышленные протоколы | `pymodbus` (Modbus TCP), `asyncua` (OPC UA) |
| Управление зависимостями | uv |
| Контейнеризация | Docker + docker-compose |

---

## Структура

```
industrial_automation/
├── core/settings.py                 # Глобальный экземпляр Settings
├── db/
│   ├── models.py                    # SQLAlchemy-модель Measurement
│   └── session.py                   # async engine + session factory
├── dao/
│   ├── base.py                      # ABC MeasurementDAO
│   └── measurement.py               # Реализация
├── services/measurement_service.py  # Сервисный слой
├── usecases/generate_and_store.py   # Сценарий: сгенерировать + сохранить
├── dependencies/uow.py              # Unit of Work с автокоммитом
├── simulator/random_simulator.py    # Источник случайных значений
├── protocols/
│   ├── modbus_client.py             # Заготовка pymodbus (async)
│   └── opcua_client.py              # Заготовка asyncua
├── visual/dashboard.py              # Plotly + Matplotlib
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
| `timescaledb` | Хранилище временных рядов | 5432 |
| `app` | ASGI-приложение с генератором и веб-интерфейсом | 8000 |
| `modbus-sim` | Modbus TCP симулятор (в текущей версии не используется) | 5020 |
| `opcua-sim` | OPC UA симулятор (в текущей версии не используется) | 4840 |

`app` стартует после того, как `timescaledb` пройдёт healthcheck.

### 3. Применение миграций

При первом запуске схема БД ещё не создана. Примените миграции:

```bash
docker compose exec app alembic upgrade head
```

Или, если предпочитаете запускать Alembic с хоста:

```bash
uv run alembic upgrade head
```

Проверить, что таблица и гипертаблица созданы:

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
