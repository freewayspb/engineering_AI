# Пошаговая настройка проекта на immers.cloud

**Сервер**: 195.209.210.16  
**Пользователь**: root  
**Проект**: BA_AI_GOST

---

## Шаг 1: Подключение к серверу

### 1.1 Настройка SSH на локальном компьютере

```bash
# Сохраните приватный ключ
mkdir -p ~/.ssh
nano ~/.ssh/id_rsa_immers
# Вставьте приватный ключ, сохраните (Ctrl+O, Enter, Ctrl+X)
chmod 600 ~/.ssh/id_rsa_immers

# Настройте SSH config
cat >> ~/.ssh/config << 'EOF'
Host immers-cloud
    HostName 195.209.210.16
    User root
    IdentityFile ~/.ssh/id_rsa_immers
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
```

### 1.2 Подключение

```bash
ssh immers-cloud
```

---

## Шаг 2: Проверка и установка зависимостей

### 2.1 Обновление системы

```bash
apt update && apt upgrade -y
```

### 2.2 Проверка Git

```bash
# Проверка наличия Git
git --version

# Если Git не установлен:
apt install -y git
```

### 2.3 Проверка Docker

```bash
# Проверка Docker
docker --version
docker compose version || docker-compose --version

# Если Docker не установлен:
apt install -y docker.io docker-compose
systemctl enable docker
systemctl start docker

# ВАЖНО: Настройка прав доступа к Docker
# Если вы не root, добавьте пользователя в группу docker:
usermod -aG docker $USER
# Затем выйдите и войдите снова, или выполните:
newgrp docker

# Или используйте sudo для команд Docker:
# sudo docker-compose up -d ollama
```

### 2.4 Проверка GPU и NVIDIA Container Toolkit

```bash
# Проверка GPU
nvidia-smi

# Проверка NVIDIA Container Toolkit
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Если возникает ошибка "unknown or invalid runtime name: nvidia",
# установите NVIDIA Container Toolkit:

# 1. Определение дистрибутива
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

# 2. Добавление репозитория NVIDIA
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 3. Установка
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 4. Настройка Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 5. Проверка после установки
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**ВАЖНО**: Если NVIDIA Container Toolkit не установлен, вы получите ошибку "unknown or invalid runtime name: nvidia" при запуске docker-compose. См. подробную инструкцию в `NVIDIA-TOOLKIT-SETUP.md`.

---

## Шаг 3: Клонирование репозитория

### 3.1 Выбор директории для проекта

```bash
# Рекомендуется использовать /opt или /root
cd /opt
# или
cd /root
```

### 3.2 Клонирование репозитория

```bash
# Если репозиторий публичный:
git clone <repository-url> engineering_AI

# Если репозиторий приватный, настройте SSH ключ на сервере:
# 1. Сгенерируйте SSH ключ на сервере (если нужно)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -C "immers-server"
cat ~/.ssh/id_rsa.pub
# 2. Добавьте публичный ключ в настройки репозитория (GitHub/GitLab)
# 3. Клонируйте:
git clone git@github.com:your-org/engineering_AI.git
# или
git clone https://github.com/your-org/engineering_AI.git
```

### 3.3 Переход в директорию проекта

```bash
cd engineering_AI
pwd  # Проверка текущей директории
```

---

## Шаг 4: Настройка окружения

### 4.1 Создание .env файла

```bash
cd /opt/engineering_AI  # или /root/engineering_AI
nano .env
```

Вставьте следующее содержимое:

```bash
# GPU конфигурация
OLLAMA_NUM_GPU=1
OLLAMA_GPU_LAYERS=35
NVIDIA_VISIBLE_DEVICES=all

# Базовая модель
BASE_MODEL=llama3.1:8b

# Backend конфигурация
API_HOST=0.0.0.0
API_PORT=8080
OLLAMA_BASE_URL=http://ollama:11434
```

Сохраните файл (Ctrl+O, Enter, Ctrl+X).

### 4.2 Проверка конфигурации

```bash
cat .env
```

---

## Шаг 5: Проверка конфигурации Docker Compose

### 5.1 Проверка docker-compose.yml

```bash
cat docker-compose.yml
```

Убедитесь, что файл содержит настройки для GPU (`runtime: nvidia`).

### 5.2 Проверка структуры проекта

```bash
ls -la
ls -la backend/
ls -la ollama/
```

---

## Шаг 6: Запуск проекта

### 6.1 Запуск Ollama

**Примечание**: Если команда `docker compose` не работает, используйте `docker-compose` (с дефисом).

```bash
# Проверка версии Docker Compose
docker compose version
# или
docker-compose --version

# Запуск сервиса Ollama
docker compose up -d ollama
# или (для старых версий)
docker-compose up -d ollama

# Проверка статуса
docker compose ps
# или
docker-compose ps

# Просмотр логов
docker compose logs -f ollama
# или
docker-compose logs -f ollama
```

Дождитесь, пока Ollama запустится (статус `healthy`).

### 6.2 Инициализация моделей

**ВАЖНО**: Перед инициализацией убедитесь, что скрипт имеет права на исполнение:

```bash
# Установка прав на исполнение для скрипта
chmod +x ollama/scripts/create_models.sh

# Проверка
ls -la ollama/scripts/create_models.sh
# Должно быть: -rwxr-xr-x (исполняемый)
```

Затем инициализируйте модели:

```bash
# Инициализация моделей (может занять время при первом запуске)
docker compose run --rm ollama-init
# или (для старых версий)
docker-compose run --rm ollama-init
# или (если нужен sudo)
sudo docker-compose run --rm ollama-init

# Проверка загруженных моделей
docker exec -it ollama ollama list
# или
sudo docker exec -it ollama ollama list
```

**Примечание**: При первом запуске загрузка базовой модели `llama3.1:8b` может занять 10-30 минут в зависимости от скорости интернета.

### 6.3 Запуск Backend

```bash
# Запуск backend
docker compose up -d backend
# или (для старых версий)
docker-compose up -d backend

# Проверка статуса
docker compose ps
# или
docker-compose ps

# Просмотр логов
docker compose logs -f backend
# или
docker-compose logs -f backend
```

---

## Шаг 7: Проверка работоспособности

### 7.1 Health Check Backend

```bash
# Проверка health endpoint
curl http://localhost:8080/health

# Ожидаемый ответ:
# {"status":"ok"}
```

### 7.2 Проверка моделей

```bash
# Список доступных моделей
curl http://localhost:8080/models

# Ожидаемый ответ должен содержать:
# agent-classify, agent-doc-extract, agent-qa
```

### 7.3 Проверка GPU

```bash
# Проверка использования GPU
docker exec -it ollama nvidia-smi

# Проверка использования GPU Ollama
docker exec -it ollama ollama ps
```

### 7.4 Тест генерации

```bash
# Тест генерации текста
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agent-qa",
    "prompt": "Тестовый запрос",
    "options": {"temperature": 0.7}
  }'
```

---

## Шаг 8: Настройка автозапуска (опционально)

### 8.1 Создание systemd service

```bash
nano /etc/systemd/system/ba-ai-gost.service
```

Вставьте:

```ini
[Unit]
Description=BA AI GOST Backend
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/engineering_AI
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=root

[Install]
WantedBy=multi-user.target
```

Сохраните и активируйте:

```bash
systemctl daemon-reload
systemctl enable ba-ai-gost.service
systemctl start ba-ai-gost.service
```

---

## Шаг 9: Мониторинг и обслуживание

### 9.1 Просмотр логов

```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f ollama
docker compose logs -f backend
```

### 9.2 Мониторинг ресурсов

```bash
# Использование GPU
watch -n 1 nvidia-smi

# Использование контейнеров
docker stats

# Дисковое пространство
df -h
docker system df
```

### 9.3 Остановка и перезапуск

```bash
# Остановка всех сервисов
docker compose down

# Перезапуск
docker compose restart

# Перезапуск конкретного сервиса
docker compose restart ollama
docker compose restart backend
```

---

## Шаг 10: Обновление проекта

### 10.1 Обновление кода

```bash
cd /opt/engineering_AI  # или /root/engineering_AI

# Остановка сервисов
docker compose down

# Обновление кода
git pull

# Пересборка backend (если нужно)
docker compose build backend

# Запуск
docker compose up -d
```

### 10.2 Обновление моделей

```bash
# Обновление базовой модели
docker exec -it ollama ollama pull llama3.1:8b

# Пересоздание кастомных моделей
docker compose run --rm ollama-init
```

---

## Устранение проблем

### Проблема: GPU не доступен

```bash
# Проверка GPU
nvidia-smi

# Проверка в контейнере
docker exec -it ollama nvidia-smi

# Если GPU не виден:
systemctl restart docker
docker compose down
docker compose up -d ollama
```

### Проблема: Ollama не использует GPU

```bash
# Проверка переменных окружения
docker exec -it ollama env | grep OLLAMA

# Проверка .env файла
cat .env

# Перезапуск с правильными настройками
docker compose down
docker compose up -d ollama
```

### Проблема: Модели не загружаются

```bash
# Проверка логов
docker compose logs ollama-init

# Ручная инициализация
docker compose run --rm ollama-init

# Проверка доступности базовой модели
docker exec -it ollama ollama list
```

### Проблема: Backend не подключается к Ollama

```bash
# Проверка статуса Ollama
docker compose ps ollama
curl http://localhost:11434/api/tags

# Проверка сетевого подключения
docker exec -it ba-ai-gost-backend ping ollama

# Проверка переменных окружения
docker exec -it ba-ai-gost-backend env | grep OLLAMA
```

### Проблема: Порт 8080 занят

```bash
# Проверка занятости порта
lsof -i :8080

# Измените порт в .env файле
nano .env
# Измените API_PORT=8080 на другой порт, например API_PORT=8081
# Обновите docker-compose.yml или перезапустите
docker compose down
docker compose up -d
```

---

## Быстрая команда для проверки статуса

Создайте алиас для быстрой проверки:

```bash
cat >> ~/.bashrc << 'EOF'
alias ba-status='docker compose ps && echo "" && curl -s http://localhost:8080/health && echo "" && docker exec -it ollama ollama list'
EOF

source ~/.bashrc

# Использование
ba-status
```

---

## Итоговый чеклист

- [ ] Подключение к серверу работает
- [ ] Git установлен и работает
- [ ] Docker и Docker Compose установлены
- [ ] NVIDIA Container Toolkit установлен
- [ ] GPU доступен (nvidia-smi работает)
- [ ] Репозиторий склонирован
- [ ] .env файл создан и настроен
- [ ] Ollama запущен и здоров
- [ ] Модели инициализированы
- [ ] Backend запущен
- [ ] Health check проходит успешно
- [ ] API endpoints работают
- [ ] GPU используется Ollama

---

**Документ подготовлен**: Solution Architect  
**Дата**: 2025-01-XX  
**Версия**: 1.0

