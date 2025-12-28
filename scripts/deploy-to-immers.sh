#!/usr/bin/env bash
# Скрипт для автоматического развертывания на immers.cloud

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVER_IP="195.209.210.16"
SERVER_USER="root"
SSH_HOST="immers-cloud"
PROJECT_DIR="/opt/engineering_AI"

echo -e "${BLUE}🚀 Развертывание BA_AI_GOST на immers.cloud${NC}"
echo "================================================================"
echo ""

# Функция для выполнения команд на сервере
run_remote() {
    ssh "$SSH_HOST" "$1"
}

# Функция для вывода успеха
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Функция для вывода ошибки
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Функция для вывода предупреждения
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Проверка подключения
echo "1. Проверка подключения к серверу..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes "$SSH_HOST" exit 2>/dev/null; then
    success "Подключение к серверу успешно"
else
    error "Не удалось подключиться к серверу"
    echo "Проверьте SSH настройки и подключение"
    exit 1
fi

# Проверка зависимостей
echo ""
echo "2. Проверка зависимостей на сервере..."

if run_remote "command -v git >/dev/null 2>&1"; then
    success "Git установлен"
else
    warning "Git не найден, установка..."
    run_remote "apt update && apt install -y git"
    success "Git установлен"
fi

if run_remote "command -v docker >/dev/null 2>&1"; then
    success "Docker установлен"
else
    warning "Docker не найден, установка..."
    run_remote "apt install -y docker.io docker-compose && systemctl enable docker && systemctl start docker"
    success "Docker установлен"
fi

if run_remote "nvidia-smi >/dev/null 2>&1"; then
    success "GPU доступен"
else
    error "GPU не доступен"
    exit 1
fi

# Проверка NVIDIA Container Toolkit
if run_remote "docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1"; then
    success "NVIDIA Container Toolkit работает"
else
    warning "NVIDIA Container Toolkit не настроен"
    echo "Выполните установку вручную на сервере:"
    echo "  distribution=\$(. /etc/os-release;echo \$ID\$VERSION_ID)"
    echo "  curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -"
    echo "  curl -s -L https://nvidia.github.io/nvidia-docker/\$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list"
    echo "  apt-get update && apt-get install -y nvidia-container-toolkit"
    echo "  systemctl restart docker"
    read -p "Нажмите Enter после установки NVIDIA Container Toolkit..."
fi

# Клонирование или обновление репозитория
echo ""
echo "3. Настройка репозитория..."

read -p "URL репозитория (или нажмите Enter если уже склонирован): " REPO_URL

if [ -n "$REPO_URL" ]; then
    if run_remote "[ -d $PROJECT_DIR ]"; then
        warning "Директория $PROJECT_DIR уже существует"
        read -p "Обновить существующий репозиторий? (y/n): " UPDATE_REPO
        if [ "$UPDATE_REPO" = "y" ] || [ "$UPDATE_REPO" = "Y" ]; then
            run_remote "cd $PROJECT_DIR && git pull"
            success "Репозиторий обновлен"
        fi
    else
        run_remote "mkdir -p $(dirname $PROJECT_DIR) && cd $(dirname $PROJECT_DIR) && git clone $REPO_URL engineering_AI"
        success "Репозиторий склонирован"
    fi
else
    if run_remote "[ -d $PROJECT_DIR ]"; then
        success "Репозиторий уже существует"
    else
        error "Репозиторий не найден и URL не указан"
        exit 1
    fi
fi

# Создание .env файла
echo ""
echo "4. Настройка окружения..."

if run_remote "[ -f $PROJECT_DIR/.env ]"; then
    warning ".env файл уже существует"
    read -p "Перезаписать .env файл? (y/n): " OVERWRITE_ENV
    if [ "$OVERWRITE_ENV" = "y" ] || [ "$OVERWRITE_ENV" = "Y" ]; then
        run_remote "cat > $PROJECT_DIR/.env << 'EOF'
OLLAMA_NUM_GPU=1
OLLAMA_GPU_LAYERS=35
NVIDIA_VISIBLE_DEVICES=all
BASE_MODEL=llama3.1:8b
API_HOST=0.0.0.0
API_PORT=8080
OLLAMA_BASE_URL=http://ollama:11434
EOF"
        success ".env файл создан"
    fi
else
    run_remote "cat > $PROJECT_DIR/.env << 'EOF'
OLLAMA_NUM_GPU=1
OLLAMA_GPU_LAYERS=35
NVIDIA_VISIBLE_DEVICES=all
BASE_MODEL=llama3.1:8b
API_HOST=0.0.0.0
API_PORT=8080
OLLAMA_BASE_URL=http://ollama:11434
EOF"
    success ".env файл создан"
fi

# Запуск сервисов
echo ""
echo "5. Запуск сервисов..."

echo "Запуск Ollama..."
run_remote "cd $PROJECT_DIR && docker compose up -d ollama"

# Ожидание готовности Ollama
echo "Ожидание готовности Ollama..."
for i in {1..30}; do
    if run_remote "cd $PROJECT_DIR && docker compose ps ollama | grep -q healthy"; then
        success "Ollama готов"
        break
    fi
    if [ $i -eq 30 ]; then
        error "Ollama не запустился за отведенное время"
        run_remote "cd $PROJECT_DIR && docker compose logs ollama"
        exit 1
    fi
    sleep 2
done

echo "Инициализация моделей..."
run_remote "cd $PROJECT_DIR && docker compose run --rm ollama-init"

echo "Запуск Backend..."
run_remote "cd $PROJECT_DIR && docker compose up -d backend"

# Проверка статуса
echo ""
echo "6. Проверка статуса..."

sleep 5

STATUS=$(run_remote "cd $PROJECT_DIR && docker compose ps")
echo "$STATUS"

# Проверка health endpoint
echo ""
echo "Проверка health endpoint..."
HEALTH=$(run_remote "curl -s http://localhost:8080/health || echo 'FAILED'")
if echo "$HEALTH" | grep -q "ok"; then
    success "Backend работает"
else
    warning "Backend может быть еще не готов, проверьте логи"
fi

# Итоговый отчет
echo ""
echo "================================================================"
echo -e "${GREEN}✅ Развертывание завершено!${NC}"
echo ""
echo "Проверка статуса:"
echo "  ssh $SSH_HOST 'cd $PROJECT_DIR && docker compose ps'"
echo ""
echo "Просмотр логов:"
echo "  ssh $SSH_HOST 'cd $PROJECT_DIR && docker compose logs -f'"
echo ""
echo "Проверка API:"
echo "  ssh $SSH_HOST 'curl http://localhost:8080/health'"
echo ""

