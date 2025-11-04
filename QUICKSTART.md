# Быстрый старт — BA AI GOST

Краткие инструкции для запуска front-end и back-end частей проекта.

## Backend (FastAPI + Ollama)

### Вариант 1: Docker Compose (рекомендуется)

```bash
# В корне проекта
docker compose up -d ollama
docker compose run --rm ollama-init
docker compose up -d backend

# Проверка
curl http://localhost:8080/health
curl http://localhost:8080/models
```

### Вариант 2: Локально

```bash
# 1. Установить зависимости
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip3 install -U pip
pip3 install -e .

# 2. Запустить Ollama (если не через docker)
ollama serve

# 3. Запустить API
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

**Swagger документация**: http://localhost:8080/docs

## Frontend (Electron)

```bash
# 1. Установить зависимости
cd app
yarn install

# 2. Запустить в режиме разработки
yarn dev

# 3. Или запустить обычный режим
yarn start

# 4. Сборка для распространения
yarn build
```

## Полный стек (Docker Compose)

```bash
# В корне проекта
docker compose up -d ollama
docker compose run --rm ollama-init
docker compose up -d backend

# Затем в отдельном терминале
cd app
yarn install
yarn dev
```

## Переменные окружения

### Backend
- `OLLAMA_BASE_URL` (по умолчанию: `http://localhost:11434`)
- `API_HOST` (по умолчанию: `0.0.0.0`)
- `API_PORT` (по умолчанию: `8080`)

### Frontend
- Backend URL настроен в `app/renderer.js` (по умолчанию: `http://localhost:8080`)

## Проверка работы

### Backend
```bash
# Health check
curl http://localhost:8080/health

# Список моделей
curl http://localhost:8080/models

# Генерация текста
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"agent-classify","prompt":"Тест"}'
```

### Frontend
- Откройте Electron приложение
- Загрузите файлы через drag & drop или кнопку
- Нажмите "Обработать документы"
- Проверьте результаты в таблице

## Устранение проблем

### Backend не отвечает
- Проверьте, что Ollama запущен: `docker compose ps`
- Проверьте логи: `docker compose logs backend ollama`
- Убедитесь, что порт 8080 свободен: `lsof -i :8080`

### Frontend не подключается к Backend
- Проверьте, что backend запущен и доступен на `http://localhost:8080`
- Откройте DevTools в Electron (Cmd+Option+I на macOS)
- Проверьте консоль на ошибки подключения

### Ollama модели не создаются
- Проверьте, что Ollama запущен и здоров: `docker compose ps`
- Проверьте логи init: `docker compose logs ollama-init`
- Вручную запустите скрипт: `docker compose run --rm ollama-init`

