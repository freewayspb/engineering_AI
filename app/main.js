const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const Store = require('electron-store');

// Инициализация хранилища настроек
const store = new Store();

// Создание главного окна приложения
function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'), // Иконка приложения
    titleBarStyle: 'default',
    show: false // Не показывать окно до полной загрузки
  });

  // Загрузка HTML файла
  mainWindow.loadFile('index.html');

  // Показать окно когда готово
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Открыть DevTools в режиме разработки
    if (process.argv.includes('--dev')) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Обработка закрытия окна
  mainWindow.on('closed', () => {
    // Сохранение состояния окна
    store.set('windowState', mainWindow.getBounds());
  });

  return mainWindow;
}

// Создание меню приложения
function createMenu() {
  const template = [
    {
      label: 'Файл',
      submenu: [
        {
          label: 'Открыть документ',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            const result = await dialog.showOpenDialog({
              properties: ['openFile'],
              filters: [
                { name: 'Документы', extensions: ['pdf', 'dwg', 'dxf', 'arp', 'gsfx', 'xml', 'rtf', 'xlsx', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'ico', 'webp'] },
                { name: 'Все файлы', extensions: ['*'] }
              ]
            });
            
            if (!result.canceled) {
              // Отправить путь к файлу в процесс рендеринга
              const mainWindow = BrowserWindow.getFocusedWindow();
              if (mainWindow) {
                mainWindow.webContents.send('file-selected', result.filePaths[0]);
              }
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Выход',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Правка',
      submenu: [
        { role: 'undo', label: 'Отменить' },
        { role: 'redo', label: 'Повторить' },
        { type: 'separator' },
        { role: 'cut', label: 'Вырезать' },
        { role: 'copy', label: 'Копировать' },
        { role: 'paste', label: 'Вставить' }
      ]
    },
    {
      label: 'Вид',
      submenu: [
        { role: 'reload', label: 'Перезагрузить' },
        { role: 'forceReload', label: 'Принудительная перезагрузка' },
        { role: 'toggleDevTools', label: 'Инструменты разработчика' },
        { type: 'separator' },
        { role: 'resetZoom', label: 'Сбросить масштаб' },
        { role: 'zoomIn', label: 'Увеличить' },
        { role: 'zoomOut', label: 'Уменьшить' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'Полноэкранный режим' }
      ]
    },
    {
      label: 'Окно',
      submenu: [
        { role: 'minimize', label: 'Свернуть' },
        { role: 'close', label: 'Закрыть' }
      ]
    },
    {
      label: 'Справка',
      submenu: [
        {
          label: 'О программе',
          click: () => {
            dialog.showMessageBox({
              type: 'info',
              title: 'О программе',
              message: 'BA AI GOST Client',
              detail: 'Клиентское приложение для системы обработки документов BA_AI_GOST\nВерсия: 1.0.0'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Обработчики IPC для взаимодействия с процессом рендеринга
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-store-value', (event, key) => {
  return store.get(key);
});

ipcMain.handle('set-store-value', (event, key, value) => {
  store.set(key, value);
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(options);
  return result;
});

// События приложения
app.whenReady().then(() => {
  createWindow();
  createMenu();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Безопасность: предотвращение создания новых окон
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
  });
});
