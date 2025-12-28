# Настройка клиента для подключения к удаленному backend

**Backend сервер**: 195.209.210.16:8080  
**Клиент**: Electron приложение

---

## Быстрая настройка

### Вариант 1: Через localStorage (рекомендуется)

1. Запустите клиент:
```bash
cd app
yarn install
yarn start
```

2. Откройте DevTools (F12 или Cmd+Option+I на macOS)

3. В консоли выполните:
```javascript
localStorage.setItem('backendUrl', 'http://195.209.210.16:8080');
location.reload();
```

### Вариант 2: Изменить код напрямую

Отредактируйте `app/renderer.js`:

```javascript
// Найти строку (примерно строка 12):
this.backendUrl = 'http://localhost:8080';

// Заменить на:
this.backendUrl = 'http://195.209.210.16:8080';
```

### Вариант 3: Через переменную окружения (для разработки)

```bash
cd app
BACKEND_URL=http://195.209.210.16:8080 yarn start
```

---

## Полная инструкция

### 1. Установка зависимостей

```bash
cd app
yarn install
```

### 2. Настройка URL backend

Выберите один из способов:

#### Способ A: Изменить в коде (постоянно)

Отредактируйте `app/renderer.js`:

```javascript
// Строка ~12
this.backendUrl = 'http://195.209.210.16:8080';
```

#### Способ B: Через localStorage (динамически)

1. Запустите приложение:
```bash
yarn start
```

2. Откройте DevTools (F12)

3. В консоли:
```javascript
localStorage.setItem('backendUrl', 'http://195.209.210.16:8080');
location.reload();
```

#### Способ C: Создать конфигурационный файл

Создайте файл `app/config.js`:

```javascript
window.BACKEND_URL = 'http://195.209.210.16:8080';
```

И добавьте в `app/index.html` перед `renderer.js`:

```html
<script src="config.js"></script>
<script src="renderer.js"></script>
```

### 3. Запуск клиента

```bash
# Режим разработки (с DevTools)
yarn dev

# Обычный режим
yarn start
```

### 4. Проверка подключения

После запуска клиент автоматически проверит подключение к backend. В интерфейсе должно появиться уведомление:
- ✅ "Backend подключен" - если все работает
- ❌ "Backend недоступен" - если есть проблемы

---

## Проверка доступности backend

Перед запуском клиента убедитесь, что backend доступен:

```bash
# С локального компьютера
curl http://195.209.210.16:8080/health

# Ожидаемый ответ:
# {"status":"ok"}
```

Если backend недоступен, проверьте:

1. **Backend запущен на сервере:**
```bash
ssh immers-cloud
sudo docker-compose ps
# Должен быть запущен контейнер ba-ai-gost-backend
```

2. **Порт 8080 открыт:**
```bash
# На сервере
sudo netstat -tlnp | grep 8080
# или
sudo ss -tlnp | grep 8080
```

3. **Firewall разрешает подключения:**
```bash
# На сервере (если используется ufw)
sudo ufw allow 8080/tcp
sudo ufw status
```

---

## Настройка для production

### Создание конфигурационного файла

1. Создайте `app/config.js`:

```javascript
// Конфигурация backend
window.BACKEND_CONFIG = {
    url: 'http://195.209.210.16:8080',
    timeout: 360000, // 6 минут
    retryAttempts: 3
};
```

2. Обновите `app/index.html`:

```html
<!-- Добавьте перед renderer.js -->
<script src="config.js"></script>
<script src="renderer.js"></script>
```

3. Обновите `app/renderer.js`:

```javascript
// В конструкторе класса
const config = window.BACKEND_CONFIG || {};
this.backendUrl = config.url || 'http://localhost:8080';
```

---

## Устранение проблем

### Проблема: "Backend недоступен"

**Причины:**
1. Backend не запущен на сервере
2. Неправильный URL
3. Порт заблокирован firewall
4. CORS проблемы

**Решение:**
```bash
# 1. Проверьте backend на сервере
ssh immers-cloud
sudo docker-compose ps
curl http://localhost:8080/health

# 2. Проверьте доступность с локального компьютера
curl http://195.209.210.16:8080/health

# 3. Проверьте настройки CORS в backend (должно быть allow_origins=["*"])
```

### Проблема: CORS ошибки

Если возникают CORS ошибки, убедитесь что в backend (`backend/src/main.py`) настроен CORS:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для production лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Проблема: Таймауты при обработке

Если запросы занимают много времени, увеличьте таймаут в `renderer.js`:

```javascript
// Строка ~389
signal: AbortSignal.timeout(600000) // 10 минут вместо 6
```

---

## Безопасность

### Для production рекомендуется:

1. **Использовать HTTPS:**
   - Настроить reverse proxy (nginx) с SSL на сервере
   - Изменить URL на `https://195.209.210.16:8080`

2. **Ограничить CORS:**
   - Вместо `allow_origins=["*"]` указать конкретные домены

3. **Аутентификация:**
   - Добавить API ключи или токены для доступа

---

## Быстрая команда для запуска

```bash
# 1. Установка зависимостей (один раз)
cd app && yarn install

# 2. Настройка URL (выберите один способ выше)

# 3. Запуск
yarn start
```

---

**Документ подготовлен**: Solution Architect  
**Дата**: 2025-01-XX  
**Версия**: 1.0

