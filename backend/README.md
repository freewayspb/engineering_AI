# Backend (FastAPI) с локальной Ollama

Назначение: локальный REST API для работы с моделями Ollama (генерация, чат, список моделей), интеграция с клиентским Electron-приложением. Все операции локально, без внешнего интернета.

## Структура

```
backend/
  src/
    main.py                # точки входа FastAPI
    ollama_client.py       # клиент для HTTP API Ollama
    schemas.py             # Pydantic-схемы запросов/ответов
  pyproject.toml           # зависимости
  .env.example             # пример переменных окружения
```

## Запуск локально

1. Установить зависимости:
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
```

2. Запустить Ollama (если не через docker):
```bash
ollama serve
```

3. Запуск API:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

Открыть Swagger-документацию: http://localhost:8080/docs

## Переменные окружения

- OLLAMA_BASE_URL (по умолчанию: http://localhost:11434)
- API_HOST (по умолчанию: 0.0.0.0)
- API_PORT (по умолчанию: 8080)

## Docker Compose (альтернатива)

См. `docker-compose.yml` в корне проекта для запуска `ollama` и `backend` совместно.


