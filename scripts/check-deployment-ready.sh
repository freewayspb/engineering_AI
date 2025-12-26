#!/usr/bin/env bash
# Скрипт проверки готовности проекта к развертыванию на immers.cloud

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo "🔍 Проверка готовности проекта к развертыванию на immers.cloud"
echo "================================================================"
echo ""

# Функция для вывода ошибки
error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

# Функция для вывода предупреждения
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

# Функция для вывода успеха
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Проверка Docker
echo "1. Проверка Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    success "Docker установлен: $DOCKER_VERSION"
else
    error "Docker не установлен"
fi

# Проверка Docker Compose
echo ""
echo "2. Проверка Docker Compose..."
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    success "Docker Compose доступен"
else
    error "Docker Compose не найден"
fi

# Проверка GPU
echo ""
echo "3. Проверка GPU..."
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n1)
        success "GPU обнаружен: $GPU_INFO"
    else
        warning "nvidia-smi доступен, но GPU не обнаружен (может быть нормально для локальной проверки)"
    fi
else
    warning "nvidia-smi не найден (может быть нормально для локальной проверки)"
fi

# Проверка файлов конфигурации
echo ""
echo "4. Проверка файлов конфигурации..."

if [ -f "docker-compose.yml" ]; then
    success "docker-compose.yml найден"
    
    # Проверка наличия GPU конфигурации
    if grep -q "nvidia" docker-compose.yml || grep -q "gpu" docker-compose.yml; then
        success "GPU конфигурация найдена в docker-compose.yml"
    else
        error "GPU конфигурация не найдена в docker-compose.yml"
    fi
    
    # Проверка переменных окружения для GPU
    if grep -q "OLLAMA_NUM_GPU" docker-compose.yml; then
        success "OLLAMA_NUM_GPU настроен"
    else
        warning "OLLAMA_NUM_GPU не найден в docker-compose.yml"
    fi
else
    error "docker-compose.yml не найден"
fi

if [ -f ".dockerignore" ]; then
    success ".dockerignore найден"
else
    warning ".dockerignore не найден (рекомендуется для оптимизации сборки)"
fi

if [ -f ".env" ]; then
    success ".env файл найден"
else
    warning ".env файл не найден (создайте его перед развертыванием)"
fi

# Проверка Dockerfile
echo ""
echo "5. Проверка Dockerfile..."
if [ -f "backend/Dockerfile" ]; then
    success "backend/Dockerfile найден"
else
    error "backend/Dockerfile не найден"
fi

# Проверка структуры проекта
echo ""
echo "6. Проверка структуры проекта..."

REQUIRED_DIRS=("backend" "backend/src" "ollama" "ollama/models" "ollama/scripts")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        success "Директория $dir найдена"
    else
        error "Директория $dir не найдена"
    fi
done

# Проверка ключевых файлов
echo ""
echo "7. Проверка ключевых файлов..."

REQUIRED_FILES=(
    "backend/src/main.py"
    "backend/pyproject.toml"
    "ollama/scripts/create_models.sh"
    "ollama/models/agent-classify/Modelfile"
    "ollama/models/agent-doc-extract/Modelfile"
    "ollama/models/agent-qa/Modelfile"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "Файл $file найден"
    else
        error "Файл $file не найден"
    fi
done

# Проверка документации
echo ""
echo "8. Проверка документации..."

if [ -f "DEPLOYMENT.md" ]; then
    success "DEPLOYMENT.md найден"
else
    warning "DEPLOYMENT.md не найден"
fi

if [ -f "documentation/08-tech-documentation/gpu-selection-guide.md" ]; then
    success "GPU selection guide найден"
else
    warning "GPU selection guide не найден"
fi

# Проверка прав на скрипты
echo ""
echo "9. Проверка прав на выполнение..."

if [ -f "ollama/scripts/create_models.sh" ]; then
    if [ -x "ollama/scripts/create_models.sh" ]; then
        success "create_models.sh исполняемый"
    else
        warning "create_models.sh не исполняемый (chmod +x ollama/scripts/create_models.sh)"
    fi
fi

# Итоговый отчет
echo ""
echo "================================================================"
echo "📊 Итоговый отчет:"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ Проект готов к развертыванию!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Проект готов к развертыванию с предупреждениями ($WARNINGS)${NC}"
    echo "Рекомендуется исправить предупреждения перед развертыванием"
    exit 0
else
    echo -e "${RED}❌ Обнаружены критические ошибки ($ERRORS)${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  И предупреждения ($WARNINGS)${NC}"
    fi
    echo "Исправьте ошибки перед развертыванием"
    exit 1
fi

