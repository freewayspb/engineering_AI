# Быстрая шпаргалка: Развертывание на immers.cloud

**Сервер**: 195.209.210.16  
**Проект**: `/opt/engineering_AI` (или `/root/engineering_AI`)

---

## 🚀 Быстрый старт (пошагово)

### 1. Подключение к серверу
```bash
ssh immers-cloud
# или
ssh root@195.209.210.16
```

### 2. Установка зависимостей (если нужно)
```bash
apt update && apt upgrade -y
apt install -y git docker.io docker-compose
systemctl enable docker && systemctl start docker

# NVIDIA Container Toolkit (ОБЯЗАТЕЛЬНО для GPU)
# Если возникнет ошибка "unknown or invalid runtime name: nvidia", выполните:
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Проверка
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 3. Клонирование репозитория
```bash
cd /opt
git clone <repository-url> engineering_AI
cd engineering_AI
```

### 4. Создание .env файла
```bash
cat > .env << 'EOF'
OLLAMA_NUM_GPU=1
OLLAMA_GPU_LAYERS=35
NVIDIA_VISIBLE_DEVICES=all
BASE_MODEL=llama3.1:8b
API_HOST=0.0.0.0
API_PORT=8080
OLLAMA_BASE_URL=http://ollama:11434
EOF
```

### 5. Запуск проекта

**ВАЖНО**: Если возникает ошибка "Permission denied", используйте `sudo`:
- `sudo docker-compose up -d ollama`
- Или добавьте пользователя в группу docker: `sudo usermod -aG docker $USER` и перелогиньтесь

```bash
# Проверка версии
docker compose version || docker-compose --version

# Проверка доступа к Docker
docker ps || sudo docker ps

# Запуск Ollama (добавьте sudo если нужно)
docker compose up -d ollama || docker-compose up -d ollama || sudo docker-compose up -d ollama

# Ожидание готовности (проверка каждые 2 секунды)
while ! (docker compose ps ollama 2>/dev/null || docker-compose ps ollama 2>/dev/null || sudo docker-compose ps ollama 2>/dev/null) | grep -q healthy; do sleep 2; done

# Инициализация моделей (может занять 10-30 минут при первом запуске)
# ВАЖНО: Убедитесь что скрипт исполняемый: chmod +x ollama/scripts/create_models.sh
chmod +x ollama/scripts/create_models.sh
docker compose run --rm ollama-init || docker-compose run --rm ollama-init || sudo docker-compose run --rm ollama-init

# Запуск Backend
docker compose up -d backend || docker-compose up -d backend || sudo docker-compose up -d backend
```

### 6. Проверка
```bash
# Статус сервисов
docker compose ps

# Health check
curl http://localhost:8080/health

# Список моделей
curl http://localhost:8080/models

# Проверка GPU
docker exec -it ollama nvidia-smi
```

---

## 📋 Полезные команды

### Управление сервисами

**Используйте `docker-compose` (с дефисом) если `docker compose` не работает**

```bash
# Статус
docker compose ps || docker-compose ps

# Логи
docker compose logs -f || docker-compose logs -f
docker compose logs -f ollama || docker-compose logs -f ollama
docker compose logs -f backend || docker-compose logs -f backend

# Перезапуск
docker compose restart || docker-compose restart
docker compose restart ollama || docker-compose restart ollama

# Остановка
docker compose down || docker-compose down

# Запуск
docker compose up -d || docker-compose up -d
```

### Мониторинг
```bash
# GPU
watch -n 1 nvidia-smi

# Контейнеры
docker stats

# Диск
df -h
docker system df
```

### Обновление
```bash
cd /opt/engineering_AI
docker compose down || docker-compose down
git pull
docker compose build backend || docker-compose build backend
docker compose up -d || docker-compose up -d
```

---

## 🔧 Устранение проблем

### GPU не работает
```bash
nvidia-smi
docker exec -it ollama nvidia-smi
systemctl restart docker
docker compose restart ollama || docker-compose restart ollama
```

### Модели не загружаются
```bash
docker compose logs ollama-init || docker-compose logs ollama-init
docker compose run --rm ollama-init || docker-compose run --rm ollama-init
docker exec -it ollama ollama list
```

### Backend не отвечает
```bash
docker compose ps || docker-compose ps
docker compose logs backend || docker-compose logs backend
curl http://localhost:8080/health
```

---

## 📝 Полная документация

- `SERVER-SETUP.md` - Подробная пошаговая инструкция
- `DEPLOYMENT.md` - Общее руководство по развертыванию

---

**Версия**: 1.0

