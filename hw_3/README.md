# Домашнее задание 3-4: API-сервис сокращения ссылок

![Python](https://img.shields.io/badge/python-v3.12-blue.svg)

## Оглавление

- [Описание](#описание)
- [Структура проекта](#структура-проекта)
- [Структура БД](#структура-бд)
  - [Таблица links](#таблица-links)
  - [Таблица redirects](#таблица-redirects)
- [Запуск проекта](#запуск-проекта)
- [Методы API](#методы-api)
  - [1. Root](#1-root)
    - [1.1. GET /](#11-get-)
  - [2. Auth](#2-auth)
    - [2.1. POST /auth/register](#21-post-authregister)
    - [2.2. POST /auth/jwt/login](#22-post-authjwtlogin)
    - [2.3. POST /auth/jwt/logout](#23-post-authjwtlogout)
  - [3. Links](#3-links)
    - [3.1. POST /links/shorten](#31-post-linksshorten)
    - [3.2. GET /links/search?original_url={original_url}](#32-get-linkssearchoriginal_urloriginal_url)
    - [3.3. GET /links/user](#33-get-linksuser)
    - [3.4. GET /links/{short_code}](#34-get-linksshort_code)
    - [3.5. GET /links/{short_code}/stats](#35-get-linksshort_codestats)
    - [3.6. PUT /links/{short_code}](#36-put-linksshort_code)
    - [3.7. DELETE /links/{short_code}](#37-delete-linksshort_code)
- [Тестирование API-сервиса](#тестирование-апи-сервиса)
  - [Юнит-тесты](#юнит-тесты)
  - [Функциональные тесты](#функциональные-тесты)
  - [Нагрузочное тестирование](#нагрузочное-тестирование)
- [Инструкция по запуску тестов](#инструкция-по-запуску-тестов)
- [Зависимости](#зависимости)

## Описание

Данный проект представляет собой FastAPI-сервис для сокращения длинных URL с целью быстрого доступа.  
Основные функции сервиса:
- **Создание** короткой ссылки из длинного URL (с возможностью указания кастомного alias и времени жизни).
- **Редирект**: перенаправление по короткому URL на оригинальный.
- **Изменение**: обновление оригинального URL, alias или срока жизни ссылки.
- **Удаление**: удаление короткой ссылки.
- **Получение статистики**: вывод информации о переходах (количество, даты создания и последнего перехода).
- **Поиск**: поиск ссылок по оригинальному URL.

Дополнительно реализованы:
- **Регистрация пользователей** и привязка ссылок к аккаунту (изменение и удаление доступны только владельцу).
- **Кэширование** популярных ссылок в Redis с автоматической очисткой при обновлении или удалении.
- Контейнеризация всего приложения с использованием Docker Compose.

## Структура проекта

- `task3.ipynb` — Jupyter-ноутбук с описанием требований к ДЗ 3;
- `task4.ipynb` — Jupyter-ноутбук с описанием требований к ДЗ 4;
- `README.md` — Markdown-файл с документацией приложения ***(данный файл)***;
- `Dockerfile` — Инструкция по сборке Docker-образа;
- `docker-compose.yml` — Описание контейнеров (API, PostgreSQL, Redis);
- `requirements.txt` — Зависимости проекта (с версиями);
- `url_shortener/` — Корневая директория проекта:
  - `app/` — Модуль с кодом приложения:
    - `__init__.py`
    - `main.py` — Точка входа в приложение;
    - `api/` — Эндпоинты и зависимости API:
      - `__init__.py`
      - `dependencies.py` — Общие зависимости (подключение к БД, Redis, авторизация);
      - `routers/` — Роутеры для различных функциональных блоков:
        - `__init__.py`
        - `auth.py` — Эндпоинты для регистрации и логина;
        - `links.py` — Эндпоинты для работы с короткими ссылками (CRUD, редирект, статистика);
    - `core/` — Конфигурационные файлы:
      - `__init__.py`
      - `config.py` — Настройки приложения (подключение к БД, Redis, параметры JWT);
    - `db/` — Модуль для работы с базой данных:
      - `__init__.py`
      - `models.py` — Модели SQLAlchemy (User, Link и т.д.);
      - `session.py` — Фабрика сессий для подключения к БД;
    - `schemas/` — Схемы Pydantic для валидации и сериализации данных:
      - `__init__.py`
      - `user.py` — Схемы для пользователей;
      - `link.py` — Схемы для ссылок;
    - `utils/` — Вспомогательные утилиты:
      - `__init__.py`
      - `security.py` — Функции безопасности (хеширование, JWT);
      - `shortener.py` — Функция генерации уникальных коротких кодов;
  - `migrations/` — Миграции базы данных (с использованием Alembic);
- `tests/` — Тесты проекта:
  - `__init__.py`
  - `test_unit.py` — Юнит-тесты отдельных функций (например, генерация кода);
  - `test_api.py` — Функциональные тесты API через TestClient;
  - `locustfile.py` — Сценарий нагрузочного тестирования (Locust).
    -


## Структура БД

Проект использует PostgreSQL для хранения данных о ссылках и пользователях.

### Таблица links

|     Поле     |        Тип данных        | Обязательное | Уникальное |   По умолчанию    |                  Описание                   |
|:------------:|:------------------------:|:------------:|:----------:|:-----------------:|:-------------------------------------------:|
| id           | Integer                  | Да (PK)      | Да         | -                 | Первичный ключ                            |
| user_id      | Integer                  | Нет          | Нет        | -                 | Идентификатор пользователя (FK)           |
| short_code   | String                   | Да           | Да         | -                 | Короткий код (alias) для ссылки             |
| original_url | String                   | Да           | Нет        | -                 | Оригинальный длинный URL                    |
| created_at   | TIMESTAMP(timezone=True) | Да           | Нет        | CURRENT_TIMESTAMP | Дата и время создания ссылки                |
| expires_at   | TIMESTAMP(timezone=True) | Нет          | Нет        | -                 | Срок жизни ссылки (если указан)             |
| click_count  | Integer                  | Да           | Нет        | 0                 | Количество переходов по ссылке              |
| last_click_at| TIMESTAMP(timezone=True) | Нет          | Нет        | -                 | Дата последнего перехода                    |

### Таблица redirects

|    Поле    |        Тип данных        | Обязательное | Уникальное |   По умолчанию    |       Описание        |
|:----------:|:------------------------:|:------------:|:----------:|:-----------------:|:---------------------:|
| id         | Integer                  | Да (PK)      | Да         | -                 | Первичный ключ      |
| link_id    | Integer                  | Да (FK)      | Нет        | -                 | Идентификатор ссылки (FK) |
| timestamp  | TIMESTAMP(timezone=True) | Да           | Нет        | CURRENT_TIMESTAMP | Время перенаправления |

**Связи:**
- Таблица `redirects` имеет отношение "многие-к-одному" с таблицей `links` (с каскадным удалением при удалении ссылки).

## Запуск проекта

Для запуска проекта рекомендуется использовать **Docker Compose**.  
В корневой директории выполните:

```bash
docker compose up --build
```

## Методы API

### 1. Root

#### 1.1. GET `/`

Получение основной информации о приложении.

- Авторизация: **НЕТ**
- Кэширование: **ДА**

Пример ответа:

`200 OK`:

```json
{"info": "API для создания коротких ссылок", "status": "OK"}
```

### 2. Auth

#### 2.1. POST `/auth/register`

Регистрация пользователя.

- **Авторизация:** НЕТ  
- **Кэширование:** НЕТ

Пример запроса:

```json
{"email": "user@example.com", "password": "password"}
```

Пример ответа (201 Created):

```json
{"id": 1, "email": "user@example.com", "created_at": "2025-04-01T12:00:00"}
```

#### 2.2. POST `/auth/jwt/login`

Вход в аккаунт.

- **Авторизация:** НЕТ  
- **Кэширование:** НЕТ

Пример запроса (x-www-form-urlencoded):

- username: user@example.com  
- password: password

Пример ответа (200 OK):

```json
{"access_token": "TOKEN", "token_type": "bearer"}
```

#### 2.3. POST `/auth/jwt/logout`

Выход из аккаунта.

- **Авторизация:** ДА  
- **Кэширование:** НЕТ

### 3. Links

#### 3.1. POST `/links/shorten`

Создание короткой ссылки.

- **Авторизация:** ДА (для привязки ссылки к пользователю)  
- **Кэширование:** НЕТ

Пример запроса:

```json
{"original_url": "https://google.com", "alias": "ggl", "expires_at": "2025-04-01T00:00:00"}
```

Пример ответа (201 Created):

```json
{
  "short_code": "ggl",
  "original_url": "https://google.com",
  "created_at": "2025-03-30T10:37:39.286933Z",
  "expires_at": "2025-04-01T00:00:00",
  "click_count": 0,
  "last_click_at": null,
  "owner_id": 1
}
```

#### 3.2. GET `/links/search?original_url={original_url}`

Поиск ссылки по оригинальному URL.

- **Авторизация:** НЕТ (или только для ссылок текущего пользователя)  
- **Кэширование:** НЕТ

Пример ответа (200 OK):

```json
[
  {
    "short_code": "ggl",
    "original_url": "https://google.com",
    "created_at": "2025-03-30T10:37:39.286933Z",
    "expires_at": null
  }
]
```

#### 3.3. GET `/links/user`

Получение всех ссылок, созданных текущим пользователем.

- **Авторизация:** ДА  
- **Кэширование:** НЕТ

Пример ответа (200 OK):

```json
[
  {
    "short_code": "ggl",
    "original_url": "https://google.com",
    "created_at": "2025-03-30T10:37:39.286933Z",
    "expires_at": null
  }
]
```

#### 3.4. GET `/links/{short_code}`

Перенаправление по короткой ссылке на оригинальный URL.

- **Авторизация:** НЕТ (публичный доступ)  
- **Кэширование:** ДА (для ускорения редиректа)

Пример:  
При запросе `http://localhost:8000/ggl` происходит HTTP 302 Redirect на `https://google.com`.

#### 3.5. GET `/links/{short_code}/stats`

Получение статистики использования ссылки.

- **Авторизация:** ДА (только владелец)  
- **Кэширование:** ДА

Пример ответа (200 OK):

```json
{
  "short_code": "ggl",
  "original_url": "https://google.com",
  "created_at": "2025-03-30T10:37:39.286933Z",
  "expires_at": null,
  "click_count": 5,
  "last_click_at": "2025-03-30T12:14:38.074305Z",
  "owner_id": 1
}
```

#### 3.6. PUT `/links/{short_code}`

Обновление данных ссылки.

- **Авторизация:** ДА (только владелец)  
- **Кэширование:** НЕТ

Пример запроса:

```json
{"original_url": "https://yandex.ru", "alias": "newalias", "expires_at": "2025-04-01T00:00:00"}
```

Пример ответа (200 OK):

```json
{"info": "Link with short code newalias was updated successfully"}
```

#### 3.7. DELETE `/links/{short_code}`

Удаление ссылки.

- **Авторизация:** ДА (только владелец)  
- **Кэширование:** НЕТ

Пример ответа (200 OK):

```json
{"info": "Link with short code ggl was deleted successfully"}
```

## Тестирование API-сервиса

Для обеспечения качественного тестового покрытия (не менее 90%) и проверки устойчивости сервиса реализованы следующие типы тестов:

### Юнит-тесты

- **Цель:** Проверка работы отдельных функций (например, генерации уникального короткого кода, валидации входных данных).
- **Инструменты:** `pytest`, `pytest-mock` (или `unittest.mock`).
- **Пример:** Тестирование функции `generate_short_code` из `app/utils/shortener.py`.

### Функциональные тесты

- **Цель:** Проверка API через FastAPI TestClient с использованием `httpx`.
- **Инструменты:** `pytest`, `httpx`.
- **Примеры сценариев:**
  - Тестирование всех CRUD-операций с ссылками (создание, редирект, обновление, удаление).
  - Проверка корректности обработки невалидных данных.
  - Тестирование аутентификации и авторизации (регистрация, логин, доступ к защищённым эндпоинтам).

### Нагрузочное тестирование

- **Цель:** Оценка производительности сервиса под нагрузкой, массовое создание ссылок и влияние кэширования.
- **Инструменты:** `Locust` (или аналогичные, например, k6).
- **Пример:** Написание сценария в файле `locustfile.py`, который моделирует работу большого числа пользователей, одновременно создающих ссылки и выполняющих редиректы.

## Инструкция по запуску тестов

1. **Создайте виртуальное окружение и установите зависимости:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # или venv\Scripts\activate на Windows
   pip install -r requirements.txt
   ```

2. **Запустите тесты с покрытием:**

   ```bash
   coverage run -m pytest tests
   coverage html
   ```

   После этого HTML-отчёт будет сгенерирован в папке `htmlcov`. Откройте файл `htmlcov/index.html` в браузере для просмотра процента покрытия (должен быть не менее 90%).

3. **Запуск нагрузочного тестирования Locust:**

   ```bash
   locust -f tests/locustfile.py --host http://localhost:8000
   ```

   Перейдите по адресу [http://localhost:8089](http://localhost:8089) для запуска и мониторинга тестовой нагрузки.

## Зависимости

### Основные библиотеки для работы сервиса:
- **fastapi**
- **uvicorn**
- **sqlalchemy**
- **psycopg2-binary**
- **python-jose**
- **passlib[bcrypt]**
- **redis**
- **email-validator**

### Библиотеки для тестирования:
- **pytest**
- **pytest-cov**
- **httpx**
- **pytest-mock**
- **locust**

Все зависимости указаны в файле [requirements.txt](requirements.txt).

