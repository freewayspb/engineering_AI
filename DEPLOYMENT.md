# Руководство по развертыванию на immers.cloud

**Проект**: BA_AI_GOST  
**Платформа**: immers.cloud  
**Дата**: 2025-01-XX

---

## 1. Предварительные требования

### 1.1 Аппаратные требования
- **GPU**: RTX 3090 24GB или RTX 4090 24GB (рекомендуется)
- **CPU**: 8+ cores
- **RAM**: 32+ GB
- **Storage**: 100+ GB SSD

### 1.2 Программные требования
- Docker 20.10+ с поддержкой GPU
- Docker Compose 2.0+
- NVIDIA Container Toolkit (nvidia-container-runtime)
- Доступ к immers.cloud с GPU инстансом

### 1.3 Проверка окружения
```bash
# Проверка Docker
docker --version
docker compose version

# Проверка GPU
nvidia-smi

# Проверка NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## 2. Подготовка к развертыванию

### 2.1 Клонирование репозитория
```bash
git clone <repository-url>
cd engineering_AI
```

### 2.2 Настройка переменных окружения
Создайте файл `.env` в корне проекта:

```bash
# GPU конфигурация
OLLAMA_NUM_GPU=1
OLLAMA_GPU_LAYERS=35
NVIDIA_VISIBLE_DEVICES=all

# Базовая модель
BASE_MODEL=llama3.1:8b

# Backend конфигурация (опционально)
API_HOST=0.0.0.0
API_PORT=8080
OLLAMA_BASE_URL=http://ollama:11434
```

### 2.3 Проверка готовности
Запустите скрипт проверки:
```bash
chmod +x scripts/check-deployment-ready.sh
./scripts/check-deployment-ready.sh
```

---

## 3. Развертывание на immers.cloud

### 3.1 Подключение к серверу
```bash
ssh user@your-immers-cloud-instance
```

### 3.2 Установка зависимостей (если нужно)
```bash
# Установка NVIDIA Container Toolkit (если не установлен)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 3.3 Загрузка проекта
```bash
# Клонирование или загрузка файлов
git clone <repository-url>
cd engineering_AI

# Или через scp
scp -r . user@your-immers-cloud-instance:/path/to/project
```

### 3.4 Настройка конфигурации
```bash
# Создайте .env файл
cp .env.example .env  # Если есть пример
# Или создайте вручную (см. раздел 2.2)
```

### 3.5 Запуск сервисов
```bash
# Запуск Ollama
docker compose up -d ollama

# Инициализация моделей (может занять время при первом запуске)
docker compose run --rm ollama-init

# Запуск backend
docker compose up -d backend

# Проверка статуса
docker compose ps
```

### 3.6 Проверка работы
```bash
# Health check backend
curl http://localhost:8080/health

# Проверка моделей
curl http://localhost:8080/models

# Проверка GPU
docker exec -it ollama nvidia-smi
docker exec -it ollama ollama ps
```

---

## 4. Конфигурация для production

### 4.1 Настройка портов и безопасности
Если нужно изменить порты или настроить firewall:

```bash
# В docker-compose.yml измените:
ports:
  - "${API_PORT:-8080}:8080"

# Настройка firewall (если нужно)
sudo ufw allow 8080/tcp
```

### 4.2 Настройка логирования
```bash
# Просмотр логов
docker compose logs -f ollama
docker compose logs -f backend

# Ротация логов (настройте в docker-compose.yml или через logrotate)
```

### 4.3 Мониторинг ресурсов
```bash
# Мониторинг GPU
watch -n 1 nvidia-smi

# Мониторинг контейнеров
docker stats

# Мониторинг дискового пространства
df -h
docker system df
```

---

## 5. Обновление и обслуживание

### 5.1 Обновление кода
```bash
# Остановка сервисов
docker compose down

# Обновление кода
git pull

# Пересборка и перезапуск
docker compose build backend
docker compose up -d
```

### 5.2 Обновление моделей
```bash
# Обновление базовой модели
docker exec -it ollama ollama pull llama3.1:8b

# Пересоздание кастомных моделей
docker compose run --rm ollama-init
```

### 5.3 Очистка
```bash
# Очистка неиспользуемых образов
docker system prune -a

# Очистка volumes (осторожно - удалит модели!)
docker volume prune
```

---

## 6. Устранение проблем

### 6.1 GPU не доступен
```bash
# Проверка доступности GPU
nvidia-smi

# Проверка в контейнере
docker exec -it ollama nvidia-smi

# Если GPU не виден, проверьте:
# 1. Установлен ли nvidia-container-toolkit
# 2. Перезапущен ли Docker после установки
# 3. Правильно ли настроен docker-compose.yml
```

### 6.2 Ollama не использует GPU
```bash
# Проверка переменных окружения
docker exec -it ollama env | grep OLLAMA

# Проверка использования GPU
docker exec -it ollama ollama ps

# Если GPU не используется, проверьте:
# 1. Переменные OLLAMA_NUM_GPU и OLLAMA_GPU_LAYERS
# 2. Доступность GPU в контейнере
```

### 6.3 Модели не загружаются
```bash
# Проверка логов инициализации
docker compose logs ollama-init

# Ручная инициализация
docker compose run --rm ollama-init

# Проверка доступности базовой модели
docker exec -it ollama ollama list
```

### 6.4 Backend не подключается к Ollama
```bash
# Проверка статуса Ollama
docker compose ps ollama
curl http://localhost:11434/api/tags

# Проверка сетевого подключения
docker exec -it ba-ai-gost-backend ping ollama

# Проверка переменной OLLAMA_BASE_URL
docker exec -it ba-ai-gost-backend env | grep OLLAMA
```

---

## 7. Рекомендации по безопасности

### 7.1 Сетевая безопасность
- Используйте firewall для ограничения доступа к портам
- Настройте reverse proxy (nginx/traefik) для production
- Используйте HTTPS для внешнего доступа

### 7.2 Управление секретами
- Не коммитьте `.env` файлы в git
- Используйте секреты Docker или внешние системы управления секретами
- Ограничьте права доступа к файлам конфигурации

### 7.3 Мониторинг и логирование
- Настройте централизованное логирование
- Настройте алерты на критические ошибки
- Регулярно проверяйте использование ресурсов

---

## 8. Проверка после развертывания

### 8.1 Чеклист
- [ ] GPU доступен и используется Ollama
- [ ] Все модели загружены и работают
- [ ] Backend отвечает на health check
- [ ] API endpoints работают корректно
- [ ] Логи не содержат критических ошибок
- [ ] Использование ресурсов в норме

### 8.2 Тестирование
```bash
# Тест health check
curl http://localhost:8080/health

# Тест списка моделей
curl http://localhost:8080/models

# Тест генерации
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agent-qa",
    "prompt": "Тестовый запрос",
    "options": {"temperature": 0.7}
  }'
```

---

## 9. Дополнительные ресурсы

- [GPU Selection Guide](./documentation/08-tech-documentation/gpu-selection-guide.md)
- [Technical Specification](./documentation/08-tech-documentation/technical-specification.md)
- [Ollama Documentation](https://ollama.ai/docs)
- [Docker GPU Support](https://docs.docker.com/config/containers/resource_constraints/#gpu)

---

**Документ подготовлен**: Solution Architect  
**Дата**: 2025-01-XX  
**Версия**: 1.0

