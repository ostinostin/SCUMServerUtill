SCUM Server Manager
Утилита для управления dedicated сервером SCUM на Unreal Engine. Позволяет запускать, останавливать, перезапускать сервер, обновлять его через SteamCMD и создавать бэкапы сохранений.
Возможности

GUI: Интерфейс с вкладками "Основное", "Бэкап", "Обновление".
Управление сервером:
Запуск/остановка/рестарт сервера (SCUMServer.exe).
Автозапуск при старте утилиты (опционально).
Плановый рестарт по двум заданным временам (ЧЧ:ММ).
Перезапуск при сбое через 5 секунд.


Бэкап:
Архивация файлов SCUM.db, SCUM.db-shm, SCUM.db-wal в ZIP.
Настраиваемые пути для сохранений и бэкапов.


Обновление:
Обновление сервера через SteamCMD в отдельном потоке.
Настраиваемые пути для steamcmd.exe и папки сервера.


Логи: Вывод логов сервера и SteamCMD в GUI, логи утилиты в logs/server.log.
Настройки: Сохранение в settings.json (времена рестарта, аргументы, автозапуск, пути).
Экран загрузки: Отображается при старте утилиты (~2 секунды).

Требования

Python 3.7+
Установленный tkinter (python -c "import tkinter")
PyInstaller для сборки в .exe (pip install pyinstaller)
SCUMServer.exe в C:\Scum\SCUMServer\SCUM\Binaries\Win64
steamcmd.exe в C:\steamcmd\
Папка сохранений: C:\Scum\SCUMServer\SCUM\Saved\SaveFiles\

Установка

Клонируйте репозиторий:git clone <repository_url>


Установите зависимости:python -m venv venv
venv\Scripts\activate
pip install pyinstaller


Соберите .exe:pyinstaller --onefile --noconsole run_scumserver.py


Поместите dist\run_scumserver.exe, SCUMServer.exe, settings.json в C:\Scum\SCUMServer\SCUM\Binaries\Win64.

Использование

Запуск:
Запустите dist\run_scumserver.exe или python run_scumserver.py.
Появится экран загрузки ("Запуск утилиты сервера, ожидайте").


Вкладка "Основное":
Укажите времена рестарта (ЧЧ:ММ), аргументы запуска (например, -log -port=7777), включите автозапуск (чекбокс).
Нажмите "Сохранить" для времени и аргументов.
Кнопки:
Старт: Запускает сервер.
Рестарт сейчас: Перезапускает сервер.
Остановить: Останавливает сервер (утилита остаётся открытой).




Вкладка "Бэкап" (доступна, если сервер остановлен):
Укажите пути к папке сохранений (C:/Scum/SCUMServer/SCUM/Saved/SaveFiles/) и бэкапов (C:/Scum/SCUMServer/backup/).
Нажмите "Сохранить пути".
Нажмите "Сделать бэкап" для создания ZIP-архива в папке бэкапов (имя: backup_YYYY-MM-DD_HH-MM-SS.zip).
Во время бэкапа отображается окно "Утилита работает над сохранением ваших данных, пожалуйста, подождите".


Вкладка "Обновление" (доступна, если сервер остановлен):
Укажите пути к steamcmd.exe (C:/steamcmd/steamcmd.exe) и папке сервера (C:/Scum/SCUMServer/).
Нажмите "Сохранить пути".
Нажмите "Обновить сервер" для запуска SteamCMD.
Логи обновления отображаются в GUI, утилита не зависает, показывается окно "Утилита работает над обновлением сервера, пожалуйста, подождите".


Логи:
Логи сервера и SteamCMD в текстовом поле GUI.
Логи утилиты в logs/server.log.



Примечания

Консоль SCUMServer.exe может появляться (допустимо).
Убедитесь, что пути в settings.json корректны и доступны для записи.
При ошибках проверяйте logs/server.log.

Структура проекта
ScumServerManager/
├── SCUMServer.exe
├── run_scumserver.py
├── settings.json
├── logs/
│   └── server.log
├── C:/Scum/SCUMServer/SCUM/Saved/SaveFiles/
│   ├── SCUM.db
│   ├── SCUM.db-shm
│   └── SCUM.db-wal
├── C:/Scum/SCUMServer/backup/
│   └── backup_YYYY-MM-DD_HH-MM-SS.zip
├── C:/steamcmd/
│   └── steamcmd.exe
├── venv/
├── build/
├── dist/
│   └── run_scumserver.exe
└── .vscode/
    └── settings.json
