// Основной класс приложения
class BA_AI_GOST_Client {
    constructor() {
        this.files = [];
        this.isProcessing = false;
        this.processedCount = 0;
        this.errorCount = 0;
        this.maxFiles = 100;
        this.maxFileSizeBytes = 50 * 1024 * 1024; // 50 MB
        this.allowedExtensions = ['pdf','dwg','arp','gsfx','xml','rtf','xlsx','docx'];
        this.backendUrl = 'http://localhost:8080';
        this.notifier = typeof Notyf !== 'undefined' ? new Notyf({
            duration: 2500,
            position: { x: 'right', y: 'top' }
        }) : null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.updateUI();
        this.pingBackend();
    }

    initializeElements() {
        // Основные элементы интерфейса
        this.fileInputArea = document.getElementById('fileInputArea');
        this.fileHiddenInput = document.getElementById('fileHiddenInput');
        this.fileList = document.getElementById('fileList');
        this.processBtn = document.getElementById('processBtn');
        this.exportBtn = document.getElementById('exportBtn');
        this.clearBtn = document.getElementById('clearBtn');
        
        // Элементы статуса
        this.systemStatus = document.getElementById('systemStatus');
        this.processedCountEl = document.getElementById('processedCount');
        this.errorCountEl = document.getElementById('errorCount');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        
        // Области контента
        this.resultsArea = document.getElementById('resultsArea');
        this.resultsContent = document.getElementById('resultsContent');
        this.loadingArea = document.getElementById('loadingArea');
    }

    async pingBackend() {
        try {
            const res = await fetch(this.backendUrl + '/health');
            if (res.ok) {
                this.showSuccess('Backend подключен');
                return true;
            }
        } catch (e) {
            this.showError('Backend недоступен: ' + (e?.message || ''));
        }
        return false;
    }

    setupEventListeners() {
        // Обработка клика по области загрузки файлов
        this.fileInputArea.addEventListener('click', () => {
            this.openFileDialog();
        });

        if (this.fileHiddenInput) {
            this.fileHiddenInput.addEventListener('change', (e) => {
                const files = e.target.files;
                if (files && files.length > 0) {
                    this.handleFiles(files);
                    // сбрасываем значение, чтобы повторный выбор тех же файлов сработал
                    e.target.value = '';
                }
            });
        }

        // Обработка перетаскивания файлов
        this.fileInputArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.fileInputArea.classList.add('dragover');
        });

        this.fileInputArea.addEventListener('dragleave', () => {
            this.fileInputArea.classList.remove('dragover');
        });

        this.fileInputArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.fileInputArea.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });

        // Кнопки действий
        this.processBtn.addEventListener('click', () => {
            this.processDocuments();
        });

        this.exportBtn.addEventListener('click', () => {
            this.exportResults();
        });

        this.clearBtn.addEventListener('click', () => {
            this.clearAll();
        });

        // Слушатель событий от основного процесса
        if (window.electronAPI) {
            window.electronAPI.onFileSelected((filePath) => {
                this.addFile(filePath);
            });
        }

        // Тултипы
        if (typeof tippy !== 'undefined') {
            tippy(this.fileInputArea, { content: 'Нажмите или перетащите файлы', placement: 'right' });
            tippy(this.processBtn, { content: 'Запустить обработку', placement: 'right' });
            tippy(this.exportBtn, { content: 'Экспортировать результаты', placement: 'right' });
            tippy(this.clearBtn, { content: 'Очистить список', placement: 'right' });
        }
    }

    async openFileDialog() {
        try {
            if (this.fileHiddenInput) {
                this.fileHiddenInput.click();
                return;
            }
            this.showError('Элемент выбора файла не найден');
        } catch (error) {
            this.showError('Ошибка при выборе файла: ' + error.message);
        }
    }

    handleFiles(fileList) {
        if (!fileList || fileList.length === 0) return;

        const incoming = Array.from(fileList);

        // Лимит по количеству
        if (this.files.length + incoming.length > this.maxFiles) {
            const available = this.maxFiles - this.files.length;
            if (available <= 0) {
                this.showError(`Достигнут лимит файлов (${this.maxFiles})`);
                return;
            }
            this.showError(`Можно добавить ещё только ${available} файл(ов)`);
        }

        const available = Math.max(0, this.maxFiles - this.files.length);
        const toProcess = incoming.slice(0, available || incoming.length);

        toProcess.forEach(file => {
            const validation = this.validateFile(file);
            if (!validation.ok) {
                this.showError(validation.error);
                return;
            }

            // Проверка дубликатов по имени + размеру (если есть File)
            const isDuplicate = this.files.some(f => {
                const sameName = f.name === file.name;
                const sameSize = f.file && file && typeof f.file.size === 'number' && f.file.size === file.size;
                return sameName && (sameSize || !file);
            });
            if (isDuplicate) {
                this.showError(`Файл уже добавлен: ${file.name}`);
                return;
            }

            this.addFile(file.name, file);
        });
    }

    validateFile(file) {
        try {
            if (!file) return { ok: false, error: 'Файл не определён' };

            // Размер
            if (typeof file.size === 'number' && file.size > this.maxFileSizeBytes) {
                const mb = Math.round(this.maxFileSizeBytes / (1024*1024));
                return { ok: false, error: `Файл слишком большой (> ${mb} MB): ${file.name}` };
            }

            // Расширение
            const name = file.name || '';
            const ext = (name.split('.').pop() || '').toLowerCase();
            if (ext && !this.allowedExtensions.includes(ext)) {
                return { ok: false, error: `Недопустимый тип файла: .${ext} (${name})` };
            }

            return { ok: true };
        } catch (e) {
            return { ok: false, error: 'Ошибка валидации файла' };
        }
    }

    addFile(fileName, file = null) {
        const fileInfo = {
            id: Date.now() + Math.random(),
            name: fileName,
            file: file,
            status: 'pending',
            result: null,
            error: null
        };

        this.files.push(fileInfo);
        this.updateFileList();
        this.updateUI();
    }

    updateFileList() {
        this.fileList.innerHTML = '';
        
        this.files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';

            const nameEl = document.createElement('span');
            nameEl.className = 'file-name';
            nameEl.textContent = file.name;

            const statusEl = document.createElement('span');
            const statusClass = file.status === 'success' ? 'success' : file.status === 'error' ? 'error' : '';
            statusEl.className = `file-status ${statusClass}`.trim();
            statusEl.textContent = this.getStatusText(file.status);

            fileItem.appendChild(nameEl);
            fileItem.appendChild(statusEl);
            this.fileList.appendChild(fileItem);
        });
    }

    getStatusText(status) {
        const statusMap = {
            'pending': 'Ожидает',
            'processing': 'Обработка',
            'success': 'Готово',
            'error': 'Ошибка'
        };
        return statusMap[status] || 'Неизвестно';
    }

    async processDocuments() {
        if (this.files.length === 0) {
            this.showError('Нет файлов для обработки');
            return;
        }

        this.isProcessing = true;
        this.processedCount = 0;
        this.errorCount = 0;
        
        this.updateUI();
        this.showLoading(true);
        this.updateProgress(0, 'Начало обработки...');

        try {
            for (let i = 0; i < this.files.length; i++) {
                const file = this.files[i];
                file.status = 'processing';
                this.updateFileList();
                
                this.updateProgress(
                    (i / this.files.length) * 100,
                    `Обработка файла: ${file.name}`
                );

                // Симуляция обработки файла
                await this.processFile(file);
                
                this.updateProgress(
                    ((i + 1) / this.files.length) * 100,
                    `Обработан файл: ${file.name}`
                );
            }

            this.updateProgress(100, 'Обработка завершена');
            this.showResults();
            
        } catch (error) {
            this.showError('Ошибка при обработке: ' + error.message);
        } finally {
            this.isProcessing = false;
            this.showLoading(false);
            this.updateUI();
        }
    }

    async processFile(file) {
        // Попытка реальной обработки через backend (agent-doc-extract)
        try {
            const connected = await this.pingBackend();
            if (connected) {
                const prompt = `Извлеки ключевые поля из документа с именем: ${file.name}. Верни JSON с полями fields, confidence, notes.`;
                const result = await this.callBackendGenerate('agent-doc-extract', prompt);
                const parsed = this.tryParseJSON(result?.response ?? '');
                if (!parsed) throw new Error('Некорректный ответ модели');
                file.status = 'success';
                file.result = {
                    type: this.detectFileType(file.name),
                    extractedData: {
                        title: `Документ: ${file.name}`,
                        pages: parsed?.fields?.pages ?? this.generateMockData(file.name).pages,
                        extractedText: JSON.stringify(parsed.fields ?? {}, null, 2),
                        metadata: { size: file.file?.size ?? 0, format: (file.name.split('.').pop() || '').toUpperCase() }
                    },
                    confidence: typeof parsed.confidence === 'number' ? parsed.confidence : 0.8
                };
                this.processedCount++;
                return;
            }
        } catch (e) {
            this.showError('Backend обработка не удалась, используем симуляцию');
        }

        // Фолбэк: симуляция обработки
        await new Promise((resolve) => setTimeout(resolve, 800));
        if (Math.random() > 0.1) {
            file.status = 'success';
            file.result = {
                type: this.detectFileType(file.name),
                extractedData: this.generateMockData(file.name),
                confidence: Math.random() * 0.3 + 0.7
            };
            this.processedCount++;
        } else {
            file.status = 'error';
            file.error = 'Ошибка при извлечении данных';
            this.errorCount++;
        }
    }

    async callBackendGenerate(model, prompt) {
        const resp = await fetch(this.backendUrl + '/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model, prompt })
        });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return await resp.json();
    }

    tryParseJSON(text) {
        try {
            return JSON.parse(text);
        } catch {
            return null;
        }
    }

    detectFileType(fileName) {
        const ext = fileName.split('.').pop().toLowerCase();
        const typeMap = {
            'pdf': 'PDF документ',
            'dwg': 'Чертеж AutoCAD',
            'arp': 'Архивный файл',
            'gsfx': 'Графический файл',
            'xml': 'XML документ',
            'rtf': 'RTF документ',
            'xlsx': 'Excel таблица',
            'docx': 'Word документ'
        };
        return typeMap[ext] || 'Неизвестный тип';
    }

    generateMockData(fileName) {
        return {
            title: `Документ: ${fileName}`,
            author: 'Система BA_AI_GOST',
            date: new Date().toLocaleDateString('ru-RU'),
            pages: Math.floor(Math.random() * 50) + 1,
            extractedText: `Извлеченный текст из файла ${fileName}...`,
            metadata: {
                size: Math.floor(Math.random() * 1000000) + 10000,
                format: fileName.split('.').pop().toUpperCase()
            }
        };
    }

    showResults() {
        this.resultsContent.innerHTML = '';

        const successfulFiles = this.files.filter(f => f.status === 'success');

        if (successfulFiles.length === 0) {
            const p = document.createElement('p');
            p.style.color = '#e74c3c';
            p.style.textAlign = 'center';
            p.textContent = 'Нет успешно обработанных файлов';
            this.resultsContent.appendChild(p);
            return;
        }

        // Если доступен gridjs, рендерим таблицу
        if (typeof gridjs !== 'undefined' && gridjs.Grid) {
            const tableContainer = document.createElement('div');
            this.resultsContent.appendChild(tableContainer);

            const rows = successfulFiles.map(file => [
                file.name,
                file.result.type,
                Math.round(file.result.confidence * 100) + '%',
                file.result.extractedData.pages,
                Math.round(file.result.extractedData.metadata.size / 1024) + ' KB'
            ]);

            new gridjs.Grid({
                columns: ['Файл', 'Тип', 'Уверенность', 'Страниц', 'Размер'],
                data: rows,
                search: true,
                sort: true,
                pagination: { enabled: true, limit: 10 },
                language: {
                    'search': { 'placeholder': 'Поиск...' },
                    'pagination': { 'previous': 'Назад', 'next': 'Вперёд', 'showing': 'Показано', 'results': () => 'строк' }
                }
            }).render(tableContainer);

            // Детали под таблицей (без innerHTML)
            const detailsWrapper = document.createElement('div');
            successfulFiles.forEach(file => {
                const details = document.createElement('details');
                details.style.marginTop = '10px';

                const summary = document.createElement('summary');
                summary.style.cursor = 'pointer';
                summary.style.color = '#3498db';
                summary.textContent = `${file.name}: извлеченный текст`;

                const content = document.createElement('div');
                content.style.background = '#f8f9fa';
                content.style.padding = '10px';
                content.style.marginTop = '5px';
                content.style.borderRadius = '4px';
                content.style.fontFamily = 'monospace';
                content.style.fontSize = '12px';
                content.textContent = file.result.extractedData.extractedText;

                details.appendChild(summary);
                details.appendChild(content);
                detailsWrapper.appendChild(details);
            });
            this.resultsContent.appendChild(detailsWrapper);
        } else {
            // Фолбэк без gridjs
            successfulFiles.forEach(file => {
                const card = document.createElement('div');
                card.style.background = 'rgba(39, 174, 96, 0.1)';
                card.style.padding = '15px';
                card.style.borderRadius = '8px';
                card.style.marginBottom = '15px';

                const title = document.createElement('h4');
                title.style.color = '#27ae60';
                title.style.marginBottom = '10px';
                title.textContent = file.name;

                const box = document.createElement('div');
                box.style.fontSize = '14px';
                box.style.color = '#2c3e50';

                const pType = document.createElement('p');
                pType.innerHTML = '<strong>Тип:</strong> ' + this.escapeForHTML(file.result.type);

                const pConf = document.createElement('p');
                pConf.innerHTML = '<strong>Уверенность:</strong> ' + Math.round(file.result.confidence * 100) + '%';

                const pPages = document.createElement('p');
                pPages.innerHTML = '<strong>Страниц:</strong> ' + file.result.extractedData.pages;

                const pSize = document.createElement('p');
                pSize.innerHTML = '<strong>Размер:</strong> ' + Math.round(file.result.extractedData.metadata.size / 1024) + ' KB';

                const details = document.createElement('details');
                details.style.marginTop = '10px';
                const summary = document.createElement('summary');
                summary.style.cursor = 'pointer';
                summary.style.color = '#3498db';
                summary.textContent = 'Показать извлеченный текст';
                const content = document.createElement('div');
                content.style.background = '#f8f9fa';
                content.style.padding = '10px';
                content.style.marginTop = '5px';
                content.style.borderRadius = '4px';
                content.style.fontFamily = 'monospace';
                content.style.fontSize = '12px';
                content.textContent = file.result.extractedData.extractedText;

                details.appendChild(summary);
                details.appendChild(content);

                box.appendChild(pType);
                box.appendChild(pConf);
                box.appendChild(pPages);
                box.appendChild(pSize);
                box.appendChild(details);

                card.appendChild(title);
                card.appendChild(box);
                this.resultsContent.appendChild(card);
            });
        }
    }

    // Безопасное экранирование для использования в внутренних фрагментах HTML, если нужно
    escapeForHTML(value) {
        const div = document.createElement('div');
        div.textContent = String(value);
        return div.innerHTML;
    }

    async exportResults() {
        try {
            const successfulFiles = this.files.filter(f => f.status === 'success');
            
            if (successfulFiles.length === 0) {
                this.showError('Нет данных для экспорта');
                return;
            }

            const exportData = {
                timestamp: new Date().toISOString(),
                totalFiles: this.files.length,
                processedFiles: successfulFiles.length,
                errorFiles: this.errorCount,
                results: successfulFiles.map(file => ({
                    fileName: file.name,
                    type: file.result.type,
                    confidence: file.result.confidence,
                    extractedData: file.result.extractedData
                }))
            };

            // В реальном приложении здесь будет вызов диалога сохранения
            console.log('Экспорт данных:', exportData);
            this.showSuccess('Результаты экспортированы в консоль разработчика');

        } catch (error) {
            this.showError('Ошибка при экспорте: ' + error.message);
        }
    }

    clearAll() {
        this.files = [];
        this.processedCount = 0;
        this.errorCount = 0;
        this.updateFileList();
        this.updateUI();
        this.resultsContent.innerHTML = '<p style="color: #7f8c8d; text-align: center; margin-top: 50px;">Загрузите документы для начала обработки</p>';
        this.updateProgress(0, 'Готов к работе');
    }

    updateUI() {
        // Обновление состояния кнопок
        this.processBtn.disabled = this.files.length === 0 || this.isProcessing;
        this.exportBtn.disabled = this.processedCount === 0 || this.isProcessing;
        
        // Обновление счетчиков
        this.processedCountEl.textContent = this.processedCount;
        this.errorCountEl.textContent = this.errorCount;
        
        // Обновление статуса системы
        if (this.isProcessing) {
            this.systemStatus.textContent = 'Обработка';
            this.systemStatus.style.color = '#f39c12';
        } else if (this.errorCount > 0) {
            this.systemStatus.textContent = 'Ошибки';
            this.systemStatus.style.color = '#e74c3c';
        } else if (this.processedCount > 0) {
            this.systemStatus.textContent = 'Готово';
            this.systemStatus.style.color = '#27ae60';
        } else {
            this.systemStatus.textContent = 'Готов';
            this.systemStatus.style.color = '#3498db';
        }
    }

    updateProgress(percent, text) {
        if (this.progressBar) {
            this.progressBar.value = Math.max(0, Math.min(100, percent));
        }
        this.progressText.textContent = text;
    }

    showLoading(show) {
        this.loadingArea.classList.toggle('hidden', !show);
        this.resultsArea.style.display = show ? 'none' : 'block';
    }

    showError(message) {
        console.error(message);
        if (this.notifier) {
            this.notifier.error(message);
        }
    }

    showSuccess(message) {
        console.log(message);
        if (this.notifier) {
            this.notifier.success(message);
        }
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BA_AI_GOST_Client();
});
