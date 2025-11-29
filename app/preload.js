const { contextBridge, ipcRenderer } = require('electron');

// Безопасный API для процесса рендеринга
contextBridge.exposeInMainWorld('electronAPI', {
  // Получение версии приложения
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Работа с хранилищем настроек
  getStoreValue: (key) => ipcRenderer.invoke('get-store-value', key),
  setStoreValue: (key, value) => ipcRenderer.invoke('set-store-value', key, value),
  
  // Диалоги файлов
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  
  // События от основного процесса
  onFileSelected: (callback) => {
    ipcRenderer.on('file-selected', (event, filePath) => callback(filePath));
  },
  
  // Удаление слушателей событий
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});
