# Search System — поиск товаров по прайсам

Внутренняя поисковая система для товаров из прайсов компаний-партнёров.
Позволяет искать товар по артикулу, вести справочник компаний, загружать
прайсы из Excel с гибким маппингом колонок и отслеживать историю загрузок.


---

## 1. Возможности

- Поиск товаров по артикулу без учёта регистра, с фильтром по компании.
  Минимум 4 символа в запросе, вывод не более 100 результатов.
- Справочник компаний: создание, редактирование, удаление
  (удаление компании каскадно удаляет её товары).
- Загрузка прайсов из `.xlsx` и `.xls` в два шага:
  1. Предпросмотр файла, выбор листа, выбор колонок (артикул, цена,
     цена за отрез), выбор диапазона строк (начало и конец).
  2. Импорт: старые товары компании заменяются новыми.
- История загрузок: кто, когда, какой файл, сколько строк, какие
  артикулы сняты с продажи (разница между старым и новым прайсом).
- Просмотр полного прайса компании с поиском и пагинацией.
- Аутентификация по логину и паролю, cookie-сессии.
- Ролевая модель: superuser, администратор (может управлять
  пользователями), обычный пользователь.
- Журнал входов: успешные и неудачные попытки, IP, User-Agent.
- Защита от подбора пароля: 5 неудачных попыток за 15 минут —
  блокировка на 15 минут (по паре логин + IP).
- Развёртывание в Docker: PostgreSQL, приложение, Nginx, Certbot (SSL).

---

## 2. Технологический стек

| Слой | Технология |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Шаблоны | Jinja2, Bootstrap 5 (CDN) |
| ORM | SQLAlchemy 2.0, Alembic |
| БД | PostgreSQL 16 (Docker) |
| Сессии | Starlette SessionMiddleware (подписанный cookie) |
| Пароли | bcrypt |
| Excel | openpyxl (.xlsx), xlrd (.xls) |
| Reverse proxy | Nginx 1.27 |
| SSL | Let's Encrypt via Certbot |
| Оркестрация | Docker Compose V2 |

---

## 3. Структура проекта

```
project/
├── app/
│   ├── main.py                  # точка входа, middleware, обработчики ошибок
│   ├── config.py                # настройки из .env
│   ├── database.py              # engine, SessionLocal, Base
│   ├── dependencies.py          # require_user, require_user_manager
│   ├── models/
│   │   ├── company.py
│   │   ├── product.py
│   │   ├── user.py
│   │   ├── login_history.py
│   │   └── upload_history.py
│   ├── routers/
│   │   ├── auth.py              # /login, /logout
│   │   ├── pages.py             # / (поиск)
│   │   ├── admin.py             # /admin/companies, загрузка прайсов
│   │   └── admin_users.py       # /admin/users
│   ├── services/
│   │   ├── auth.py              # хэширование, валидация пароля, транслит
│   │   ├── excel_loader.py      # чтение Excel, превью, парсинг
│   │   ├── search.py            # поиск товаров
│   │   └── brute_force.py       # in-memory защита от подбора
│   ├── templates/               # Jinja2-шаблоны
│   └── static/                  # favicon, логотип, CSS
├── alembic/
│   └── versions/                # миграции
├── alembic.ini
├── nginx/
│   ├── nginx.conf
│   └── certbot/
│       ├── conf/                # сертификаты Let's Encrypt
│       └── www/                 # ACME-челлендж
├── Dockerfile
├── entrypoint.sh                # alembic upgrade + uvicorn
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 4. Модель данных

### companies

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| name | String(255) | NOT NULL, UNIQUE |
| phone | String(50) | NULL |
| email | String(255) | NULL |

### products

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| article | String(255) | NOT NULL, индекс |
| company_id | Integer | FK → companies.id, ON DELETE CASCADE |
| price | Numeric(10,2) | NULL |
| price_cut | Numeric(10,2) | NULL (цена за отрез) |

Уникальный индекс: `(company_id, article)`.

### users

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| first_name | String(100) | NOT NULL |
| last_name | String(100) | NOT NULL |
| login | String(100) | NOT NULL, UNIQUE |
| password_hash | String(255) | NOT NULL |
| is_superuser | Boolean | NOT NULL, default false |
| can_manage_users | Boolean | NOT NULL, default false |
| created_at | DateTime | NOT NULL, UTC |

### login_history

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| user_id | Integer | FK → users.id, ON DELETE SET NULL, NULL при неудачной попытке |
| login_attempted | String(100) | NOT NULL |
| ip_address | String(45) | NULL |
| user_agent | String(500) | NULL |
| success | Boolean | NOT NULL |
| login_at | DateTime | NOT NULL, UTC |

### upload_history

| Поле | Тип | Ограничения |
|---|---|---|
| id | Integer | PK |
| company_id | Integer | FK → companies.id, ON DELETE CASCADE |
| user_id | Integer | FK → users.id, ON DELETE SET NULL |
| filename | String(500) | NOT NULL |
| rows_count | Integer | NOT NULL |
| removed_articles_json | Text | NULL, JSON-массив артикулов |
| removed_count | Integer | NOT NULL, default 0 |
| uploaded_at | DateTime | NOT NULL, UTC |

---

## 5. Роли и права

| Роль | Признак | Права |
|---|---|---|
| Superuser | `is_superuser = true` | Всё. Не может быть удалён никем. |
| Администратор | `can_manage_users = true` | Всё, кроме удаления/редактирования superuser. Может создавать, редактировать, удалять пользователей и выдавать флаг «Администратор» другим. |
| Пользователь | флаги отсутствуют | Поиск, работа с компаниями и прайсами. Нет доступа к разделу «Пользователи». |

Правила:

- Superuser создаётся автоматически при старте приложения, если его нет.
- Удалить superuser нельзя.
- Удалить собственную учётную запись нельзя.
- Администратор не может редактировать superuser.
- Вкладка «Пользователи» в админке скрыта от обычных пользователей;
  прямой заход на `/admin/users` возвращает 403.

**Учётная запись superuser по умолчанию:**

```
Логин:  superuser
Пароль: 137784
```

Пароль задан в `app/main.py` в `lifespan` и хранится в БД в виде bcrypt-хэша.
Пароль не соответствует политике сложности — это допустимо, так как
создаётся напрямую через `hash_password()`. **Смените его после первого
входа** (через `/admin/users` → редактирование superuser недоступно,
поэтому смена пароля superuser выполняется SQL-запросом или
пересозданием записи — см. раздел «Обслуживание»).

---

## 6. Политика паролей

Пароль должен содержать:

- минимум 8 символов;
- минимум 1 заглавную латинскую букву;
- минимум 1 цифру;
- минимум 1 специальный символ;
- только латиницу (кириллица запрещена).

Проверка реализована в `app/services/auth.py::validate_password`.

Генерация логина при создании пользователя (если поле «Логин» пустое):

- первая буква имени (транслит) + `.` + фамилия (транслит);
- транслитерация по таблице ГОСТ (в `app/services/auth.py`, словарь `TRANSLIT_MAP`);
- если логин занят — добавляется числовой суффикс: `a.ivanov`, `a.ivanov1`, `a.ivanov2`.

---

## 7. Переменные окружения

Файл `.env` в корне проекта. Пример — `.env.example`.

| Переменная | Назначение | Пример |
|---|---|---|
| `POSTGRES_USER` | Пользователь PostgreSQL | `postgres` |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | `postgres` |
| `POSTGRES_DB` | Имя БД | `shop_search` |
| `DATABASE_URL` | Строка подключения для SQLAlchemy | `postgresql+psycopg2://postgres:postgres@db:5432/shop_search` |
| `UPLOAD_FOLDER` | Папка временных загрузок | `/app/uploads` |
| `SECRET_KEY` | Ключ подписи cookie-сессий | случайная строка ≥ 32 символов |
| `LOGO_PATH` | URL логотипа | `/static/images/logo.png` |

`SECRET_KEY` сгенерировать:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**При смене `SECRET_KEY` все активные сессии станут недействительны.**

---

## 8. Требования к серверу

- Linux (проверено на Ubuntu 22.04 / Debian 12).
- Docker Engine 24+ и Docker Compose V2 (`docker compose`, с пробелом).
- Открытые порты 80 и 443.
- Домен, A-запись которого указывает на IP сервера (для SSL).
- 1 ГБ RAM, 1 vCPU, 10 ГБ диска — минимум.

Установка Docker (если нет):

```bash
curl -fsSL https://get.docker.com | sh
sudo apt-get install -y docker-compose-plugin
docker compose version
```

> **Важно.** Не используйте старый `docker-compose` V1 (команда с дефисом).

---

## 9. Первое развёртывание (production)

### 9.1. Клонирование и настройка

```bash
git clone <repo-url> search_system
cd search_system
cp .env.example .env
nano .env
```

Заполните `.env` (см. раздел 7). Минимум — `POSTGRES_*`, `SECRET_KEY`.

### 9.2. Подготовка папок для сертификатов

```bash
mkdir -p nginx/certbot/conf nginx/certbot/www
```

### 9.3. Первый запуск (HTTP-only)

Пока SSL-сертификата нет, Nginx не должен пытаться его загрузить.
Убедитесь, что `nginx/nginx.conf` содержит HTTP-версию конфигурации
(см. раздел 10.1), затем:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f app
```

Приложение поднимет БД, применит миграции (`entrypoint.sh` вызывает
`alembic upgrade head`) и создаст superuser.

Проверка: `http://<ваш-домен>/login` должен открыться.

### 9.4. Получение SSL-сертификата

Убедитесь, что домен резолвится на сервер:

```bash
dig +short your-domain.com
```

Затем:

```bash
docker compose run --rm --entrypoint certbot certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos --no-eff-email \
  -d your-domain.com -d www.your-domain.com
```

Сертификаты появятся в `nginx/certbot/conf/live/your-domain.com/`.

Проверка:

```bash
ls -la nginx/certbot/conf/live/your-domain.com/
```

Должны быть `fullchain.pem`, `privkey.pem`, `chain.pem`, `cert.pem`.

### 9.5. Включение HTTPS

Замените `nginx/nginx.conf` на HTTPS-версию (раздел 10.2) и перезапустите:

```bash
docker compose restart nginx
```

Проверка: `https://your-domain.com` открывается, HTTP редиректит на HTTPS.

Продление сертификата — автоматически, контейнер `certbot` проверяет
раз в 12 часов. Чтобы изменения подхватились Nginx, добавьте cron на хосте:

```bash
# crontab -e
0 3 * * * cd /root/search_system && docker compose exec -T nginx nginx -s reload
```

---

## 10. Конфигурация Nginx

### 10.1. HTTP-only (для первого запуска)

```nginx
upstream fastapi_app {
    server app:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://fastapi_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### 10.2. HTTPS (production)

```nginx
upstream fastapi_app {
    server app:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    http2 on;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

    location / {
        proxy_pass http://fastapi_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

---

## 11. Docker Compose — состав сервисов

| Сервис | Образ / сборка | Порт | Назначение |
|---|---|---|---|
| `db` | postgres:16-alpine | внутренний 5432 | База данных, volume `postgres_data` |
| `app` | build: . | внутренний 8000 | FastAPI, volume `uploads_data` |
| `nginx` | nginx:1.27-alpine | 80, 443 | Reverse proxy |
| `certbot` | certbot/certbot | — | Автопродление SSL |

Сети: `app_network` (bridge).
Тома: `postgres_data`, `uploads_data`.

`app` не проброшен наружу — доступен только через Nginx.
Если нужно для отладки: `ports: ["127.0.0.1:8000:8000"]`.

---

## 12. Миграции базы данных

Все миграции применяются автоматически при старте контейнера `app`
(`entrypoint.sh` → `alembic upgrade head`).

Вручную:

```bash
docker compose exec app alembic upgrade head      # применить все
docker compose exec app alembic current            # текущая ревизия
docker compose exec app alembic heads              # последняя доступная
docker compose exec app alembic downgrade -1       # откатить одну (осторожно)
```

Список миграций (в порядке применения):

1. `20260830_01` — companies, products
2. `20260831_01` — products.price_cut
3. `20260903_01` — users, login_history
4. `20260910_01` — upload_history
5. `20260915_01` — users.can_manage_users

---

## 13. Обновление проекта на сервере

Стандартная процедура (миграции применит `entrypoint.sh`):

```bash
cd /path/to/project
git pull
docker compose up -d --build
docker compose logs -f --tail=50 app
```

Если хотите контролировать миграции отдельно:

```bash
docker compose stop app
docker compose build app
docker compose run --rm --entrypoint alembic app upgrade head
docker compose up -d
```

Перед обновлением рекомендуется сделать бэкап (раздел 14).

---

## 14. Резервное копирование и восстановление

### 14.1. Бэкап БД

```bash
docker compose exec -T db pg_dump -U postgres shop_search \
  > backup_$(date +%Y%m%d_%H%M).sql
```

Рекомендуется делать перед каждым обновлением и раз в сутки по cron:

```bash
# crontab -e
0 2 * * * cd /root/search_system && docker compose exec -T db pg_dump -U postgres shop_search > backups/db_$(date +\%Y\%m\%d).sql
```

### 14.2. Восстановление БД

```bash
docker compose exec -T db psql -U postgres shop_search < backup_YYYYMMDD_HHMM.sql
```

### 14.3. Бэкап загруженных файлов

Прайсы не хранятся постоянно — временные файлы удаляются после импорта.
Если нужно сохранить содержимое volume `uploads_data`:

```bash
docker run --rm -v search_system_uploads_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/uploads_$(date +%Y%m%d).tar.gz -C /data .
```

Имя volume можно уточнить: `docker volume ls`.

---

## 15. Обслуживание

### Смена пароля superuser

Раздел «Пользователи» не позволяет редактировать superuser
(только Администраторы могут управлять пользователями, а superuser —
не редактируется). Смена пароля выполняется через SQL:

```bash
# Сгенерировать bcrypt-хэш
docker compose exec app python -c "
import bcrypt
print(bcrypt.hashpw(b'NEW_PASSWORD_HERE', bcrypt.gensalt()).decode())
"

# Обновить в БД
docker compose exec db psql -U postgres -d shop_search -c \
  "UPDATE users SET password_hash = '<вставить_хэш>' WHERE login = 'superuser';"
```

### Назначение нового Администратора

Через `superuser`: `/admin/users` → редактировать пользователя →
отметить «Права администратора».

### Просмотр журнала входов

`/admin/users` → «История» рядом с пользователем. Показываются
последние 200 записей: дата/время (UTC), попытка логина, IP,
User-Agent, результат.

### Очистка неиспользуемых Docker-ресурсов

```bash
docker image prune -f
docker system df
```

---

## 16. Локальная разработка (без Docker)

Требуется Python 3.12+ и доступный PostgreSQL.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# .env: DATABASE_URL указывает на локальный PostgreSQL
alembic upgrade head
uvicorn app.main:app --reload
```

Приложение на `http://127.0.0.1:8000`.

---

## 17. Журналирование

- Логи приложения: `docker compose logs -f app`.
- Логи БД: `docker compose logs -f db`.
- Логи Nginx: `docker compose logs -f nginx`, а также стандартные
  `/var/log/nginx/access.log` и `/var/log/nginx/error.log` внутри контейнера.
- Журнал входов в систему хранится в таблице `login_history`
  и доступен через админку.
- История загрузок прайсов — в таблице `upload_history`.

---

## 18. Безопасность

- Все страницы, включая главную и поиск, требуют аутентификации.
- Пароли хранятся в виде bcrypt-хэшей.
- Сессии — подписанные cookie (HMAC через `itsdangerous`).
- Автоматический logout после 1 часа неактивности.
- Защита от подбора пароля: 5 неудач за 15 минут — блокировка на 15 минут
  по паре логин + IP. Реализация in-memory (сбрасывается при рестарте).
- Все действия по управлению пользователями доступны только superuser
  и администраторам.
- Внешний порт приложения (`8000`) не пробрасывается — трафик идёт
  только через Nginx.

Перед вводом в эксплуатацию обязательно:

1. Заменить `SECRET_KEY` в `.env` на случайный.
2. Сменить пароль superuser по умолчанию.
3. Настроить резервное копирование БД.
4. Ограничить доступ к серверу по SSH-ключу (не паролю).

---
