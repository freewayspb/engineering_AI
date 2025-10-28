// Основной класс приложения
class BA_AI_GOST_Client {
    constructor() {
        this.files = [];
        this.isProcessing = false;
        this.processedCount = 0;
        this.errorCount = 0;
        
        this.initializeElements();
        this.setupEventListeners();
        this.updateUI();
    }

    initializeElements() {
        // Основные элементы интерфейса
        this.fileInputArea = document.getElementById('fileInputArea');
        this.fileList = document.getElementById('fileList');
        this.processBtn = document.getElementById('processBtn');
        this.exportBtn = document.getElementById('exportBtn');
        this.clearBtn = document.getElementById('clearBtn');
        
        // Элементы статуса
        this.systemStatus = document.getElementById('systemStatus');
        this.processedCountEl = document.getElementById('processedCount');
        this.errorCountEl = document.getElementById('errorCount');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        
        // Области контента
        this.resultsArea = document.getElementById('resultsArea');
        this.resultsContent = document.getElementById('resultsContent');
        this.loadingArea = document.getElementById('loadingArea');
    }

    setupEventListeners() {
        // Обработка клика по области загрузки файлов
        this.fileInputArea.addEventListener('click', () => {
            this.openFileDialog();
        });

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
    }

    async openFileDialog() {
        try {
            // В реальном приложении здесь будет вызов диалога выбора файлов
            // Пока что симулируем добавление файла
            this.addFile('example.pdf');
        } catch (error) {
            this.showError('Ошибка при выборе файла: ' + error.message);
        }
    }

    handleFiles(fileList) {
        Array.from(fileList).forEach(file => {
            this.addFile(file.name, file);
        });
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
            
            const statusClass = file.status === 'success' ? 'success' : 
                              file.status === 'error' ? 'error' : '';
            
            fileItem.innerHTML = `
                <span class="file-name">${file.name}</span>
                <span class="file-status ${statusClass}">${this.getStatusText(file.status)}</span>
            `;
            
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
        // Симуляция обработки файла
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                try {
                    // Симуляция успешной обработки или ошибки
                    if (Math.random() > 0.1) { // 90% успеха
                        file.status = 'success';
                        file.result = {
                            type: this.detectFileType(file.name),
                            extractedData: this.generateMockData(file.name),
                            confidence: Math.random() * 0.3 + 0.7 // 70-100%
                        };
                        this.processedCount++;
                    } else {
                        file.status = 'error';
                        file.error = 'Ошибка при извлечении данных';
                        this.errorCount++;
                    }
                    resolve();
                } catch (error) {
                    file.status = 'error';
                    file.error = error.message;
                    this.errorCount++;
                    reject(error);
                }
            }, 1000 + Math.random() * 2000); // 1-3 секунды
        });
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
            this.resultsContent.innerHTML = '<p style="color: #e74c3c; text-align: center;">Нет успешно обработанных файлов</p>';
            return;
        }

        const resultsHTML = successfulFiles.map(file => `
            <div style="background: rgba(39, 174, 96, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h4 style="color: #27ae60; margin-bottom: 10px;">${file.name}</h4>
                <div style="font-size: 14px; color: #2c3e50;">
                    <p><strong>Тип:</strong> ${file.result.type}</p>
                    <p><strong>Уверенность:</strong> ${Math.round(file.result.confidence * 100)}%</p>
                    <p><strong>Страниц:</strong> ${file.result.extractedData.pages}</p>
                    <p><strong>Размер:</strong> ${Math.round(file.result.extractedData.metadata.size / 1024)} KB</p>
                    <details style="margin-top: 10px;">
                        <summary style="cursor: pointer; color: #3498db;">Показать извлеченный текст</summary>
                        <div style="background: #f8f9fa; padding: 10px; margin-top: 5px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                            ${file.result.extractedData.extractedText}
                        </div>
                    </details>
                </div>
            </div>
        `).join('');

        this.resultsContent.innerHTML = resultsHTML;
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
        this.progressFill.style.width = percent + '%';
        this.progressText.textContent = text;
    }

    showLoading(show) {
        this.loadingArea.classList.toggle('hidden', !show);
        this.resultsArea.style.display = show ? 'none' : 'block';
    }

    showError(message) {
        console.error(message);
        // В реальном приложении здесь будет показ уведомления
        alert('Ошибка: ' + message);
    }

    showSuccess(message) {
        console.log(message);
        // В реальном приложении здесь будет показ уведомления
        alert('Успех: ' + message);
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BA_AI_GOST_Client();
});
