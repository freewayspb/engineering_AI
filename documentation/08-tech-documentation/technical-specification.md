# Technical Specification
**BA_AI_GOST — Техническая спецификация**

**Версия**: 1.0  
**Дата**: 2025-01-XX  
**Автор**: Solution Architect  
**Статус**: Draft

---

## 1. Introduction

### 1.1 Purpose
Данный документ содержит детальную техническую спецификацию системы BA_AI_GOST, включая API спецификации, схемы данных, конфигурации и процедуры развертывания.

### 1.2 Scope
Документ охватывает:
- Детальные технические требования
- API спецификации
- Модели данных и схемы
- Конфигурации компонентов
- Процедуры сборки и развертывания
- Требования к тестированию

### 1.3 Document Structure
- Раздел 2: Системные требования
- Раздел 3: API спецификации
- Раздел 4: Модели данных
- Раздел 5: Спецификации компонентов
- Раздел 6: Конфигурация
- Раздел 7: Зависимости
- Раздел 8: Сборка и развертывание
- Раздел 9: Тестирование
- Раздел 10: Обработка ошибок

---

## 2. System Requirements

### 2.1 Hardware Requirements

#### 2.1.1 Minimum Requirements
- **CPU**: 4 cores (x86_64 или ARM64)
- **RAM**: 16 GB
- **Storage**: 50 GB свободного места
- **Network**: Не требуется (локальная система)

#### 2.1.2 Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 32+ GB
- **Storage**: 100+ GB SSD
- **GPU**: Опционально (NVIDIA GPU с CUDA для ускорения)

### 2.2 Software Requirements

#### 2.2.1 Operating System
- Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)
- macOS 11.0+ (Big Sur и выше)
- Windows 10/11 (с WSL2 или Docker Desktop)

#### 2.2.2 Runtime Dependencies
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 18+ (для Electron клиента, опционально для разработки)

### 2.3 Network Requirements
- **Локальная сеть**: Не требуется
- **Интернет**: Не требуется (полностью автономная система)
- **Порты**:
  - 8080: Backend API (конфигурируемый)
  - 11434: Ollama service (внутри Docker network)

---

## 3. API Specifications

### 3.1 Backend API

#### 3.1.1 Base URL
```
http://localhost:8080
```
Или конфигурируемый через переменную окружения `API_HOST` и `API_PORT`.

#### 3.1.2 API Endpoints

##### GET /
**Описание**: Информация о доступных маршрутах API

**Response**:
```json
{
  "message": "BA_AI_GOST Backend",
  "routes": ["/", "/health", "/health/ollama", "/models", "/vision-query", "/json-query"]
}
```

##### GET /health
**Описание**: Проверка состояния backend сервиса

**Response**:
```json
{
  "status": "ok"
}
```

##### GET /health/ollama
**Описание**: Проверка доступности Ollama сервиса

**Response** (успех):
```json
{
  "status": "ok",
  "ollama_url": "http://ollama:11434",
  "models_available": 3
}
```

**Response** (ошибка):
```json
{
  "detail": "Ollama unavailable: <error message>"
}
```
**Status Code**: 503

##### GET /models
**Описание**: Список доступных моделей Ollama

**Response**:
```json
{
  "models": [
    {
      "name": "agent-doc-extract",
      "model": "agent-doc-extract",
      "size": 1234567890,
      "digest": "sha256:...",
      "details": {...}
    }
  ]
}
```

##### POST /vision-query
**Описание**: Запрос к vision модели для анализа изображений/PDF

**Request**:
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `image_file` (file, required): Изображение или PDF файл
  - `question` (string, required): Вопрос на русском или английском языке
  - `response_language` (string, optional): Язык ответа (`ru`, `en`, `auto`), по умолчанию `ru`

**Response** (успех):
```json
{
  "answer": "Ответ модели на вопрос",
  "model": "agent-doc-extract",
  "source": "PDF-файл 'document.pdf', страниц: 5",
  "language": "ru"
}
```

**Response** (ошибка):
```json
{
  "detail": "Описание ошибки"
}
```
**Status Codes**:
- 400: Неверный запрос
- 422: Файл не может быть обработан
- 502: Ошибка подключения к Ollama
- 504: Таймаут запроса

##### POST /json-query
**Описание**: Запрос к модели для обработки структурированных данных (JSON)

**Request**:
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `json_file` (file, required): JSON файл или файл, конвертированный в JSON
  - `question` (string, required): Вопрос на русском или английском языке
  - `response_language` (string, optional): Язык ответа (`ru`, `en`, `auto`), по умолчанию `ru`

**Response** (успех):
```json
{
  "answer": "Структурированный ответ модели",
  "model": "agent-doc-extract",
  "source": "ARP файл 'specification.arp'",
  "language": "ru"
}
```

**Response** (ошибка):
```json
{
  "detail": "Описание ошибки"
}
```
**Status Codes**: Аналогично `/vision-query`

##### POST /generate
**Описание**: Генерация текста с использованием Ollama модели

**Request**:
```json
{
  "model": "llama3.1:8b",
  "prompt": "Текст промпта",
  "options": {
    "temperature": 0.7,
    "top_p": 0.9
  }
}
```

**Response**:
```json
{
  "model": "llama3.1:8b",
  "created_at": "2025-01-XX...",
  "response": "Сгенерированный текст",
  "done": true
}
```

##### POST /chat
**Описание**: Диалог с Ollama моделью

**Request**:
```json
{
  "model": "agent-qa",
  "messages": [
    {
      "role": "system",
      "content": "Системный промпт"
    },
    {
      "role": "user",
      "content": "Вопрос пользователя"
    }
  ],
  "options": {
    "temperature": 0.7
  }
}
```

**Response**:
```json
{
  "model": "agent-qa",
  "created_at": "2025-01-XX...",
  "message": {
    "role": "assistant",
    "content": "Ответ модели"
  },
  "done": true
}
```

### 3.2 Ollama API Integration

#### 3.2.1 Base URL
```
http://ollama:11434
```
(Внутри Docker network) или `http://localhost:11434` для локальной разработки.

#### 3.2.2 Используемые Endpoints
- `POST /api/generate`: Генерация текста
- `POST /api/chat`: Диалог с моделью
- `GET /api/tags`: Список моделей

---

## 4. Data Models

### 4.1 Request Models

#### 4.1.1 GenerateRequest
```python
class GenerateRequest(BaseModel):
    model: str  # Имя модели Ollama
    prompt: str  # Промпт для генерации
    options: Optional[Dict[str, Any]]  # Параметры модели
```

#### 4.1.2 ChatRequest
```python
class ChatRequest(BaseModel):
    model: str  # Имя модели
    messages: List[ChatMessage]  # История сообщений
    options: Optional[Dict[str, Any]]  # Параметры модели

class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str  # Содержимое сообщения
```

### 4.2 Response Models

#### 4.2.1 Vision Query Response
```python
{
    "answer": str,  # Ответ модели
    "model": str,  # Использованная модель
    "source": str,  # Информация об источнике
    "language": str  # Язык ответа
}
```

#### 4.2.2 JSON Query Response
```python
{
    "answer": str,  # Структурированный ответ
    "model": str,  # Использованная модель
    "source": str,  # Информация об источнике
    "language": str  # Язык ответа
}
```

### 4.3 File Format Conversions

#### 4.3.1 PDF → Base64 Images
```python
{
    "source_filename": str,
    "page_count": int,
    "images": [
        {
            "page": int,
            "base64": str,  # Base64 encoded image
            "width": int,
            "height": int
        }
    ]
}
```

#### 4.3.2 DWG/DXF → JSON
```python
{
    "entities": [
        {
            "type": str,
            "layer": str,
            "geometry": {...},
            "properties": {...}
        }
    ],
    "metadata": {
        "version": str,
        "units": str
    }
}
```

#### 4.3.3 ARP → JSON
```python
{
    "sections": [
        {
            "name": str,
            "fields": [
                {
                    "name": str,
                    "value": str | float | int
                }
            ]
        }
    ]
}
```

#### 4.3.4 XLSX → JSON
```python
{
    "sheets": [
        {
            "name": str,
            "data": [
                {
                    "row": int,
                    "columns": {
                        "A": value,
                        "B": value,
                        ...
                    }
                }
            ],
            "metadata": {
                "header_row": int,
                "total_rows": int,
                "total_columns": int
            }
        }
    ]
}
```

---

## 5. Component Specifications

### 5.1 Backend Components

#### 5.1.1 Main Application (`main.py`)
- **Framework**: FastAPI
- **Port**: 8080 (конфигурируемый)
- **CORS**: Разрешен для всех источников (локальная разработка)
- **Endpoints**: Определены в секции 3.1.2

#### 5.1.2 Vision Service (`services/vision.py`)
- **Function**: `process_vision_query(image_file, question, response_language)`
- **Input**: UploadFile, string, string
- **Output**: dict с ответом модели
- **Dependencies**: `ollama_service`, `file_handlers`

#### 5.1.3 JSON Service (`services/json_service.py`)
- **Function**: `process_json_query(json_file, question, response_language)`
- **Input**: UploadFile, string, string
- **Output**: dict с ответом модели
- **Dependencies**: `json_file_router`, `console_json_ollama`

#### 5.1.4 File Handlers

##### PDF Handler (`file_handlers/pdf_upload_service.py`)
- **Function**: `convert_pdf_upload_to_base64_images(pdf_file)`
- **Library**: pypdfium2
- **Output**: dict с массивом base64 изображений

##### DXF Handler (`file_handlers/dxf_console_service.py`)
- **Function**: `convert_dxf_upload_to_json(dxf_file)`
- **Library**: ezdxf
- **Output**: dict с структурированными данными

##### ARP Handler (`file_handlers/arp_upload_service.py`)
- **Function**: `convert_arp_upload_to_json(arp_file)`
- **Method**: Текстовый парсинг с разделителем `#`
- **Output**: dict с секциями и полями

##### XLSX Handler (`file_handlers/xlsx_upload_service.py`)
- **Function**: `convert_xlsx_upload_to_json(xlsx_file)`
- **Library**: pandas
- **Output**: dict с данными листов

#### 5.1.5 Ollama Service (`services/ollama_service.py`)
- **Function**: `call_ollama(endpoint, payload)`
- **Timeout**: 1800 секунд (30 минут)
- **Error Handling**: HTTPException с соответствующими кодами

### 5.2 Client Components

#### 5.2.1 Main Process (`main.js`)
- **Framework**: Electron
- **Window Management**: Создание и управление окнами
- **Menu**: Настройка меню приложения
- **IPC**: Обработка IPC сообщений

#### 5.2.2 Renderer Process (`renderer.js`)
- **UI Logic**: Управление интерфейсом
- **API Calls**: HTTP запросы к backend
- **File Handling**: Загрузка и обработка файлов

#### 5.2.3 Preload Script (`preload.js`)
- **IPC Bridge**: Безопасный мост между renderer и main процессами
- **API Exposure**: Предоставление API для renderer процесса

---

## 6. Configuration

### 6.1 Environment Variables

#### 6.1.1 Backend
- `API_HOST`: Host для FastAPI (по умолчанию: `0.0.0.0`)
- `API_PORT`: Port для FastAPI (по умолчанию: `8080`)
- `OLLAMA_BASE_URL`: URL Ollama сервиса (по умолчанию: `http://localhost:11434`)

#### 6.1.2 Docker Compose
- `BASE_MODEL`: Базовая модель для создания кастомных моделей (по умолчанию: `llama3.1:8b`)

### 6.2 Docker Compose Configuration

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama:/root/.ollama
      - ./ollama:/opt/ollama:ro
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 10s
      timeout: 5s
      retries: 10

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - API_HOST=0.0.0.0
      - API_PORT=8080
    depends_on:
      ollama:
        condition: service_healthy
    ports:
      - "8080:8080"
```

### 6.3 Ollama Models Configuration

#### 6.3.1 Model Files Location
```
ollama/
├── models/
│   ├── agent-classify/
│   │   └── Modelfile
│   ├── agent-doc-extract/
│   │   └── Modelfile
│   └── agent-qa/
│       └── Modelfile
├── prompts/
│   ├── classify.system
│   ├── doc_extract.system
│   └── qa.system
└── scripts/
    └── create_models.sh
```

#### 6.3.2 Modelfile Structure
```
FROM <base_model>
SYSTEM """
<system prompt>
"""
PARAMETER temperature 0.7
PARAMETER top_p 0.9
```

---

## 7. Dependencies

### 7.1 Backend Dependencies

#### 7.1.1 Core Dependencies
```toml
fastapi>=0.110
uvicorn[standard]>=0.23
httpx>=0.27
pydantic>=2.6
python-multipart>=0.0.9
```

#### 7.1.2 Document Processing
```toml
ezdxf>=1.4.2      # DWG/DXF processing
pandas>=2.0.0     # Excel processing
pypdfium2>=4.27.0 # PDF processing
```

#### 7.1.3 Development Dependencies
```toml
ruff>=0.6         # Linting
pytest>=8.0       # Testing
```

### 7.2 Client Dependencies

#### 7.2.1 Core Dependencies
```json
{
  "electron": "^28.0.0",
  "electron-store": "^8.1.0"
}
```

#### 7.2.2 Development Dependencies
```json
{
  "electron-builder": "^24.6.4"
}
```

### 7.3 Infrastructure Dependencies
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Ollama**: Latest (через Docker image)

---

## 8. Build and Deployment

### 8.1 Backend Build

#### 8.1.1 Docker Build
```bash
cd backend
docker build -t ba-ai-gost-backend .
```

#### 8.1.2 Local Development Setup
```bash
cd backend
pip install -e .
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

### 8.2 Client Build

#### 8.2.1 Development
```bash
cd app
npm install
npm run dev
```

#### 8.2.2 Production Build
```bash
cd app
npm install
npm run build
```

### 8.3 Deployment

#### 8.3.1 Docker Compose Deployment
```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

#### 8.3.2 Initial Model Setup
Модели создаются автоматически при первом запуске через `ollama-init` сервис.

#### 8.3.3 Manual Model Creation
```bash
docker exec -it ollama bash
cd /opt/ollama
bash scripts/create_models.sh
```

### 8.4 Update Procedure

#### 8.4.1 Backend Update
```bash
# Пересборка образа
docker-compose build backend

# Перезапуск сервиса
docker-compose up -d backend
```

#### 8.4.2 Model Update
```bash
# Обновление базовой модели
docker exec -it ollama ollama pull llama3.1:8b

# Пересоздание кастомных моделей
docker-compose up ollama-init
```

---

## 9. Testing

### 9.1 Unit Testing

#### 9.1.1 Backend Tests
```bash
cd backend
pytest tests/
```

#### 9.1.2 Test Coverage
- Целевое покрытие: 80%+
- Критические компоненты: 90%+

### 9.2 Integration Testing

#### 9.2.1 API Tests
- Тестирование всех endpoints
- Проверка обработки ошибок
- Валидация форматов ответов

#### 9.2.2 File Processing Tests
- Тестирование всех поддерживаемых форматов
- Проверка конвертации в JSON/Base64
- Валидация структуры выходных данных

### 9.3 End-to-End Testing

#### 9.3.1 User Scenarios
- Загрузка документа
- Отправка запроса
- Получение ответа
- Экспорт результатов

### 9.4 Performance Testing

#### 9.4.1 Load Testing
- Одновременные запросы
- Большие файлы
- Длительные операции

#### 9.4.2 Resource Monitoring
- CPU usage
- Memory usage
- Disk I/O
- Network (внутренний)

---

## 10. Error Handling

### 10.1 Error Categories

#### 10.1.1 Client Errors (4xx)
- **400 Bad Request**: Неверный формат запроса
- **422 Unprocessable Entity**: Файл не может быть обработан
- **404 Not Found**: Ресурс не найден

#### 10.1.2 Server Errors (5xx)
- **500 Internal Server Error**: Внутренняя ошибка сервера
- **502 Bad Gateway**: Ошибка подключения к Ollama
- **503 Service Unavailable**: Сервис недоступен
- **504 Gateway Timeout**: Таймаут запроса

### 10.2 Error Response Format

```json
{
  "detail": "Описание ошибки на русском языке"
}
```

### 10.3 Error Handling Strategy

#### 10.3.1 Input Validation
- Проверка типов файлов
- Проверка размеров файлов
- Валидация параметров запроса

#### 10.3.2 Service Errors
- Graceful degradation
- Retry mechanisms (где применимо)
- Informative error messages

#### 10.3.3 Logging
- Структурированное логирование
- Уровни логирования (DEBUG, INFO, WARNING, ERROR)
- Контекстная информация

---

## 11. Performance Requirements

### 11.1 Response Time
- **Simple queries**: < 10 секунд
- **Complex queries**: < 30 секунд
- **Large files**: < 60 секунд

### 11.2 Throughput
- **Concurrent requests**: До 5 одновременных запросов
- **Queue management**: Очередь для превышения лимита

### 11.3 Resource Limits
- **File size**: Максимум 100 MB на файл
- **Memory**: Эффективное использование, освобождение после обработки
- **CPU**: Оптимизация для доступных ресурсов

---

## 12. Security Considerations

### 12.1 Input Validation
- Проверка MIME types
- Ограничение размеров файлов
- Санитизация пользовательского ввода

### 12.2 Data Isolation
- Изоляция обработки файлов
- Очистка временных файлов
- Нет персистентного хранения пользовательских данных

### 12.3 Network Security
- Локальные соединения только
- Нет внешних сетевых вызовов
- CORS только для локального клиента

---

## 13. Monitoring and Logging

### 13.1 Logging Levels
- **DEBUG**: Детальная информация для отладки
- **INFO**: Общая информация о работе
- **WARNING**: Предупреждения о потенциальных проблемах
- **ERROR**: Ошибки, требующие внимания

### 13.2 Log Format
Структурированное логирование в формате JSON для удобного парсинга.

### 13.3 Health Checks
- `/health`: Проверка состояния backend
- `/health/ollama`: Проверка доступности Ollama
- Docker health checks для контейнеров

---

## 14. Maintenance

### 14.1 Regular Maintenance Tasks
- Обновление базовых моделей
- Очистка логов
- Проверка дискового пространства
- Обновление зависимостей

### 14.2 Backup Procedures
- Backup конфигураций моделей
- Backup Docker volumes (при необходимости)

### 14.3 Troubleshooting
- Проверка логов: `docker-compose logs`
- Проверка статуса сервисов: `docker-compose ps`
- Проверка ресурсов: `docker stats`

---

## 15. Appendices

### 15.1 API Examples

#### 15.1.1 Vision Query Example
```bash
curl -X POST "http://localhost:8080/vision-query" \
  -F "image_file=@document.pdf" \
  -F "question=Извлеки все спецификации материалов" \
  -F "response_language=ru"
```

#### 15.1.2 JSON Query Example
```bash
curl -X POST "http://localhost:8080/json-query" \
  -F "json_file=@data.json" \
  -F "question=Суммируй все значения в колонке Amount" \
  -F "response_language=ru"
```

### 15.2 Configuration Examples

#### 15.2.1 Environment Variables
```bash
export API_HOST=0.0.0.0
export API_PORT=8080
export OLLAMA_BASE_URL=http://ollama:11434
```

### 15.3 Troubleshooting Guide

#### 15.3.1 Common Issues
- **Ollama недоступен**: Проверить статус контейнера `docker-compose ps ollama`
- **Модели не загружены**: Запустить `docker-compose up ollama-init`
- **Порт занят**: Изменить `API_PORT` в docker-compose.yml

---

## 16. References

- [Solution Architecture](./solution-architecture.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Electron Documentation](https://www.electronjs.org/docs)
- [Docker Documentation](https://docs.docker.com/)

---

**Документ подготовлен**: Solution Architect  
**Дата последнего обновления**: 2025-01-XX  
**Версия**: 1.0

