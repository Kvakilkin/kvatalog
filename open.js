const { app, BrowserWindow, ipcMain } = require('electron');
const { exec } = require('child_process');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        }
    });

    win.loadFile('Ozon.html');
}

app.whenReady().then(createWindow);

ipcMain.on('open-python-script', (event) => {
    const filePath = path.join(__dirname, 'ozon_parcer.py');
    exec(`python "${filePath}"`, (error) => {
        if (error) {
            console.error(`Ошибка при открытии скрипта: ${error.message}`);
        } else {
            console.log('Скрипт успешно открыт и запущен!');
        }
    });
});