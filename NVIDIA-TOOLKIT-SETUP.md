# Установка NVIDIA Container Toolkit

## Проблема

При запуске `docker-compose up -d ollama` возникает ошибка:
```
ERROR: Cannot create container for service ollama: unknown or invalid runtime name: nvidia
```

## Причина

NVIDIA Container Toolkit не установлен или не настроен на сервере.

## Решение

### Вариант 1: Установка NVIDIA Container Toolkit (рекомендуется для GPU)

```bash
# 1. Определение дистрибутива
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
echo "Дистрибутив: $distribution"

# 2. Добавление репозитория NVIDIA
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 3. Обновление пакетов
sudo apt-get update

# 4. Установка NVIDIA Container Toolkit
sudo apt-get install -y nvidia-container-toolkit

# 5. Настройка Docker для использования NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# 6. Перезапуск Docker
sudo systemctl restart docker

# 7. Проверка установки
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Вариант 2: Альтернативная установка (для старых систем)

```bash
# Для Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Проверка
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Вариант 3: Временная работа БЕЗ GPU (для тестирования)

Если GPU не критичен или нужно протестировать без GPU:

```bash
# Используйте альтернативный файл конфигурации
sudo docker-compose -f docker-compose.no-gpu.yml up -d ollama
sudo docker-compose -f docker-compose.no-gpu.yml run --rm ollama-init
sudo docker-compose -f docker-compose.no-gpu.yml up -d backend
```

**Примечание**: Без GPU модели будут работать медленнее, но функциональность сохранится.

## Проверка после установки

```bash
# 1. Проверка GPU
nvidia-smi

# 2. Проверка Docker с GPU
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# 3. Проверка конфигурации Docker
cat /etc/docker/daemon.json
# Должно содержать настройки для nvidia runtime

# 4. Запуск проекта
sudo docker-compose up -d ollama
sudo docker-compose ps
```

## Устранение проблем

### Проблема: "nvidia-ctk: command not found"

```bash
# Убедитесь что пакет установлен
dpkg -l | grep nvidia-container-toolkit

# Если не установлен, повторите установку
sudo apt-get install -y nvidia-container-toolkit
```

### Проблема: Docker не видит nvidia runtime

```bash
# Проверка конфигурации
cat /etc/docker/daemon.json

# Если файл пустой или не содержит nvidia, настройте вручную:
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Или вручную создайте /etc/docker/daemon.json:
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia"
}
EOF

sudo systemctl restart docker
```

### Проблема: "Failed to initialize NVML: Unknown Error"

```bash
# Проверка драйверов NVIDIA
nvidia-smi

# Если nvidia-smi не работает, установите драйверы:
sudo apt-get update
sudo apt-get install -y nvidia-driver-535  # или последняя версия
sudo reboot
```

## Быстрая установка (одной командой)

```bash
# Для Ubuntu 22.04 / Debian 12
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg && \
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && \
sudo apt-get update && \
sudo apt-get install -y nvidia-container-toolkit && \
sudo nvidia-ctk runtime configure --runtime=docker && \
sudo systemctl restart docker && \
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## После установки

После успешной установки NVIDIA Container Toolkit:

```bash
# Запуск проекта
sudo docker-compose up -d ollama
sudo docker-compose run --rm ollama-init
sudo docker-compose up -d backend

# Проверка использования GPU
sudo docker exec -it ollama nvidia-smi
```

---

**Версия**: 1.0

