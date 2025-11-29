# Solution Architecture Document
**BA_AI_GOST — Архитектура решения**

**Версия**: 1.0  
**Дата**: 2025-01-XX  
**Автор**: Solution Architect  
**Статус**: Draft

---

## 1. Executive Summary

### 1.1 Назначение документа
Данный документ описывает архитектуру решения BA_AI_GOST — локальной интеллектуальной системы для автоматизированной обработки инженерных документов с использованием технологий машинного обучения.

### 1.2 Область применения
Документ предназначен для:
- Архитекторов и разработчиков
- Технических специалистов заказчика
- Руководителей проекта
- DevOps-инженеров

### 1.3 Ключевые архитектурные решения
- **Локальное развертывание**: Полностью автономная система без доступа к интернету
- **Микросервисная архитектура**: Разделение на клиентское приложение, backend API и сервис машинного обучения
- **Контейнеризация**: Docker-based deployment для изоляции и переносимости
- **LLM-интеграция**: Использование Ollama для локального выполнения моделей машинного обучения
- **Мультиформатная обработка**: Поддержка PDF, DWG/DXF, ARP, GSFX, XML, RTF, XLSX, DOCX, изображений

---

## 2. System Overview

### 2.1 Бизнес-контекст
BA_AI_GOST — интеллектуальная система, которая:
- Обучается на корпоративных инженерных документах
- Обрабатывает текстовые запросы пользователей на естественном языке
- Извлекает структурированные данные из документов различных форматов
- Классифицирует документы по проектам
- Формирует отчеты в структурированном виде (Excel)

### 2.2 Основные пользователи
- **Учитель системы**: Загружает и валидирует документы для обучения
- **Пользователь системы**: Выполняет запросы и получает структурированные ответы
- **Администратор**: Управляет системой и конфигурацией

### 2.3 Ключевые требования
- **Локальность**: Работа без доступа к интернету
- **Безопасность**: Обработка коммерческих документов
- **Производительность**: Обработка запросов в разумные сроки
- **Масштабируемость**: Возможность обработки больших объемов документов
- **Проектно-ориентированность**: Привязка данных к конкретным проектам

---

## 3. Architecture Principles

### 3.1 Принципы проектирования
1. **Separation of Concerns**: Четкое разделение ответственности между компонентами
2. **Loose Coupling**: Минимизация зависимостей между компонентами
3. **High Cohesion**: Логическая связанность функциональности внутри компонентов
4. **Scalability**: Возможность горизонтального масштабирования
5. **Security by Design**: Безопасность заложена в архитектуру
6. **Offline-First**: Все компоненты работают локально без внешних зависимостей

### 3.2 Технологические принципы
- **Open Source First**: Приоритет открытым технологиям
- **Containerization**: Использование Docker для изоляции и переносимости
- **API-First**: RESTful API для взаимодействия компонентов
- **Stateless Services**: Backend сервисы без состояния для масштабируемости
- **Event-Driven**: Асинхронная обработка длительных операций

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BA_AI_GOST System                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   Electron   │◄───────►│   Backend    │                  │
│  │   Client     │  HTTP   │   API        │                  │
│  │   (Frontend) │         │   (FastAPI)  │                  │
│  └──────────────┘         └──────┬───────┘                  │
│                                   │                           │
│                          ┌────────▼────────┐                │
│                          │     Ollama       │                │
│                          │  (LLM Service)   │                │
│                          └──────────────────┘                │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              Document Processing Layer                │    │
│  │  PDF │ DWG │ ARP │ GSFX │ XML │ RTF │ XLSX │ Images │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Компоненты системы

#### 4.2.1 Electron Client Application
- **Назначение**: Десктопное клиентское приложение
- **Технологии**: Electron, JavaScript, HTML/CSS
- **Функции**:
  - Загрузка документов
  - Отправка запросов к backend
  - Отображение результатов
  - Управление настройками

#### 4.2.2 Backend API Service
- **Назначение**: RESTful API для обработки запросов
- **Технологии**: FastAPI, Python 3.10+
- **Функции**:
  - Обработка файлов различных форматов
  - Маршрутизация запросов к соответствующим обработчикам
  - Интеграция с Ollama
  - Управление сессиями и контекстом

#### 4.2.3 Ollama LLM Service
- **Назначение**: Локальное выполнение моделей машинного обучения
- **Технологии**: Ollama, LLM models (llama3.1, deepseek-r1)
- **Функции**:
  - Обработка текстовых запросов
  - Анализ документов (vision models)
  - Извлечение структурированных данных
  - Классификация документов

#### 4.2.4 Document Processing Services
- **Назначение**: Конвертация документов в обрабатываемые форматы
- **Поддерживаемые форматы**:
  - PDF → Base64 images (для vision models)
  - DWG/DXF → JSON (через ezdxf)
  - ARP → JSON (парсинг текстового формата)
  - GSFX → JSON (парсинг текстового формата)
  - XML → JSON (стандартный парсинг)
  - RTF → JSON (текстовый парсинг)
  - XLSX → JSON (через pandas)
  - Images → Base64 (для vision models)

---

## 5. Component Architecture

### 5.1 Backend Component Structure

```
backend/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── schemas.py              # Pydantic data models
│   ├── ollama_client.py        # Ollama API client wrapper
│   └── services/
│       ├── __init__.py
│       ├── vision.py           # Vision query processing
│       ├── json_service.py     # JSON-based query processing
│       ├── ollama_service.py   # Ollama API integration
│       ├── json_file_router.py # File format routing
│       ├── console_json_ollama.py # Console-based JSON processing
│       └── file_handlers/
│           ├── pdf_upload_service.py
│           ├── dxf_console_service.py
│           ├── arp_upload_service.py
│           ├── gsfx_upload_service.py
│           ├── rtf_upload_service.py
│           ├── xlsx_upload_service.py
│           └── image_upload_service.py
```

### 5.2 Client Component Structure

```
app/
├── main.js              # Electron main process
├── preload.js          # Preload script (IPC bridge)
├── renderer.js         # Renderer process (UI logic)
├── index.html          # UI markup
└── styles/
    ├── variables.css
    ├── layout.css
    ├── components.css
    └── utilities.css
```

### 5.3 Service Interaction Flow

#### 5.3.1 Vision Query Flow
```
User → Electron Client → Backend API (/vision-query)
  → PDF/Image Handler → Base64 Conversion
  → Ollama Vision Model → Response
  → Backend → Client → User
```

#### 5.3.2 JSON Query Flow
```
User → Electron Client → Backend API (/json-query)
  → File Router → Format-specific Handler → JSON
  → Ollama JSON Model → Structured Response
  → Backend → Client → User
```

---

## 6. Data Architecture

### 6.1 Data Flow

```
Input Documents (Various Formats)
    ↓
Format Conversion Layer
    ↓
Structured Data (JSON/Base64)
    ↓
LLM Processing
    ↓
Structured Output (JSON/Excel)
```

### 6.2 Data Models

#### 6.2.1 Request Models
- `GenerateRequest`: Запрос на генерацию текста
- `ChatRequest`: Запрос на диалог с моделью
- Vision Query: Multipart form data (file + question)
- JSON Query: Multipart form data (file + question)

#### 6.2.2 Response Models
- `GenerateResponse`: Результат генерации
- `ChatResponse`: Ответ модели в диалоге
- Vision Response: JSON с ответом и метаданными
- JSON Response: Структурированные данные

### 6.3 Data Storage
- **Временное хранение**: Temp files для обработки
- **Конфигурация**: Electron Store (local storage)
- **Модели**: Ollama volume (Docker volume)
- **Документы**: Обрабатываются in-memory, не сохраняются на диск

---

## 7. Integration Architecture

### 7.1 External Integrations

#### 7.1.1 Ollama Integration
- **Протокол**: HTTP REST API
- **Endpoint**: `http://ollama:11434` (внутри Docker network)
- **Модели**:
  - `agent-doc-extract`: Извлечение данных из документов
  - `agent-classify`: Классификация документов
  - `agent-qa`: Ответы на вопросы
  - Vision models: Анализ изображений и PDF

#### 7.1.2 Client-Backend Integration
- **Протокол**: HTTP REST API
- **Endpoint**: `http://localhost:8080` (или конфигурируемый)
- **CORS**: Разрешен для локального клиента

### 7.2 Internal Integrations

#### 7.2.1 File Handler Router
Маршрутизация файлов по расширению к соответствующим обработчикам:
- `.pdf` → `pdf_upload_service`
- `.dwg`, `.dxf` → `dxf_console_service`
- `.arp` → `arp_upload_service`
- `.gsfx` → `gsfx_upload_service`
- `.xml` → XML parser
- `.rtf` → `rtf_upload_service`
- `.xlsx` → `xlsx_upload_service`
- Images → `image_upload_service`

---

## 8. Deployment Architecture

### 8.1 Container Architecture

```yaml
Services:
  - ollama: LLM service container
  - backend: FastAPI application container
  - ollama-init: One-time model initialization container
```

### 8.2 Docker Compose Configuration

```yaml
Services:
  ollama:
    - Image: ollama/ollama:latest
    - Volumes: ollama data, ollama configs
    - Health check: ollama list
    
  backend:
    - Build: ./backend
    - Depends on: ollama (healthy)
    - Ports: 8080:8080
    - Environment: OLLAMA_BASE_URL
    
  ollama-init:
    - One-time execution
    - Creates custom models from Modelfiles
```

### 8.3 Deployment Scenarios

#### 8.3.1 Development
- Локальный запуск через `docker-compose up`
- Hot reload для backend (при разработке)
- DevTools в Electron клиенте

#### 8.3.2 Production
- Docker Compose для оркестрации
- Volume persistence для моделей
- Health checks и restart policies
- Логирование и мониторинг

### 8.4 Infrastructure Requirements

#### 8.4.1 Минимальные требования
- **CPU**: 4 cores (рекомендуется 8+)
- **RAM**: 16 GB (рекомендуется 32 GB для больших моделей)
- **Storage**: 50 GB свободного места (для моделей и данных)
- **OS**: Linux, macOS, Windows (с Docker)

#### 8.4.2 Рекомендуемые требования
- **CPU**: 8+ cores
- **RAM**: 32+ GB
- **Storage**: 100+ GB SSD
- **GPU**: Опционально (для ускорения LLM inference)

---

## 9. Security Architecture

### 9.1 Security Principles
- **Defense in Depth**: Многоуровневая защита
- **Least Privilege**: Минимальные необходимые права
- **Data Isolation**: Изоляция данных между компонентами
- **No External Access**: Полностью локальная система

### 9.2 Security Measures

#### 9.2.1 Network Security
- Все коммуникации внутри Docker network
- Backend доступен только локально (localhost)
- Нет внешних сетевых подключений

#### 9.2.2 Data Security
- Документы обрабатываются in-memory
- Временные файлы удаляются после обработки
- Нет персистентного хранения пользовательских данных

#### 9.2.3 Application Security
- Input validation на всех уровнях
- File type verification
- Size limits для загружаемых файлов
- Error handling без раскрытия внутренней структуры

### 9.3 Compliance
- Обработка коммерческих документов (не "для служебного пользования")
- Локальное хранение и обработка (соответствие требованиям конфиденциальности)
- Audit trail через логирование операций

---

## 10. Non-Functional Requirements

### 10.1 Performance
- **Response Time**: < 30 секунд для типичных запросов
- **Throughput**: Поддержка множественных параллельных запросов
- **Resource Usage**: Эффективное использование CPU/RAM

### 10.2 Scalability
- **Horizontal Scaling**: Backend может масштабироваться горизонтально
- **Model Caching**: Кэширование моделей в памяти Ollama
- **Async Processing**: Асинхронная обработка длительных операций

### 10.3 Reliability
- **Health Checks**: Мониторинг состояния сервисов
- **Error Recovery**: Graceful degradation при ошибках
- **Restart Policies**: Автоматический перезапуск при сбоях

### 10.4 Maintainability
- **Modular Design**: Модульная архитектура для легкого обслуживания
- **Documentation**: Полная техническая документация
- **Logging**: Структурированное логирование для отладки

### 10.5 Usability
- **Intuitive UI**: Простой и понятный интерфейс
- **Error Messages**: Понятные сообщения об ошибках
- **Progress Indicators**: Индикация прогресса длительных операций

---

## 11. Technology Stack

### 11.1 Frontend
- **Electron**: 28.0.0
- **JavaScript**: ES6+
- **HTML/CSS**: Стандартные веб-технологии
- **electron-store**: Локальное хранение настроек

### 11.2 Backend
- **Python**: 3.10+
- **FastAPI**: 0.110+
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **httpx**: HTTP client для Ollama

### 11.3 Document Processing
- **pypdfium2**: PDF processing
- **ezdxf**: DWG/DXF processing
- **pandas**: Excel processing
- **Standard libraries**: XML, RTF, image processing

### 11.4 ML/AI
- **Ollama**: LLM runtime
- **Models**: llama3.1:8b, deepseek-r1 (базовые модели)
- **Custom Models**: agent-doc-extract, agent-classify, agent-qa

### 11.5 Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Orchestration
- **Linux/macOS/Windows**: Multi-platform support

---

## 12. Risks and Mitigations

### 12.1 Technical Risks

#### 12.1.1 Model Performance
- **Риск**: Низкая точность извлечения данных
- **Митигация**: Тюнинг промптов, использование специализированных моделей

#### 12.1.2 Resource Constraints
- **Риск**: Недостаточно памяти для больших моделей
- **Митигация**: Использование меньших моделей, оптимизация обработки

#### 12.1.3 Format Compatibility
- **Риск**: Неподдерживаемые форматы документов
- **Митигация**: Расширяемая архитектура обработчиков, fallback механизмы

### 12.2 Operational Risks

#### 12.2.1 Deployment Complexity
- **Риск**: Сложность развертывания для неподготовленных пользователей
- **Митигация**: Подробная документация, скрипты автоматизации

#### 12.2.2 Model Updates
- **Риск**: Необходимость обновления моделей
- **Митигация**: Версионирование моделей, механизм обновления

### 12.3 Business Risks

#### 12.3.1 User Adoption
- **Риск**: Низкое принятие пользователями
- **Митигация**: Удобный интерфейс, обучение пользователей

---

## 13. Future Enhancements

### 13.1 Planned Features
- **Knowledge Base**: Персистентное хранилище обработанных документов
- **Project Management**: Управление проектами и документами
- **Advanced Search**: Семантический поиск по документам
- **Batch Processing**: Массовая обработка документов
- **Export Formats**: Дополнительные форматы экспорта

### 13.2 Scalability Improvements
- **Distributed Processing**: Распределенная обработка больших объемов
- **GPU Acceleration**: Использование GPU для ускорения
- **Caching Layer**: Кэширование результатов обработки

### 13.3 Integration Opportunities
- **Document Management Systems**: Интеграция с СЭД
- **CAD Systems**: Прямая интеграция с системами проектирования
- **Reporting Systems**: Интеграция с системами отчетности

---

## 14. Glossary

- **LLM**: Large Language Model — большая языковая модель
- **Ollama**: Локальный runtime для выполнения LLM моделей
- **Vision Model**: Модель для анализа изображений
- **FastAPI**: Современный веб-фреймворк для Python
- **Electron**: Фреймворк для создания десктопных приложений
- **Docker**: Платформа для контейнеризации приложений

---

## 15. References

- [Technical Specification](./technical-specification.md)
- [Business Requirements](../02-requirements/business-requirements.md)
- [Technical Requirements](../02-requirements/technical-requirements.md)
- [Project Vision](../01-project-overview/project-vision.md)
- [Prototypes](../03-prototypes/README.md)

---

**Документ подготовлен**: Solution Architect  
**Дата последнего обновления**: 2025-01-XX  
**Версия**: 1.0

