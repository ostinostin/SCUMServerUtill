import subprocess
import time
import signal
import sys
import os
import logging
from datetime import datetime, time as dt_time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import re
import json
import zipfile

# Настройка логирования
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "server.log")
SETTINGS_FILE = "settings.json"
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Параметры запуска сервера
SERVER_EXECUTABLE = "SCUMServer.exe"
DEFAULT_STEAMCMD_EXECUTABLE = "C:/steamcmd/steamcmd.exe"
DEFAULT_STEAMCMD_INSTALL_DIR = "C:/Scum/SCUMServer/"
DEFAULT_SAVE_DIR = "C:/Scum/SCUMServer/SCUM/Saved/SaveFiles/"
DEFAULT_BACKUP_DIR = "C:/Scum/SCUMServer/backup/"
SAVE_FILES = ["SCUM.db", "SCUM.db-shm", "SCUM.db-wal"]
DEFAULT_ARGS = ["-log", "-port=7777"]
server_args = DEFAULT_ARGS[:]
DEFAULT_RESTART_TIMES = [dt_time(12, 0), dt_time(21, 0)]

# Глобальные переменные
shutdown_flag = False
restart_now = False
server_running = False
auto_start = False
current_process = None
start_time = 0
log_queue = queue.Queue()
restart_times = DEFAULT_RESTART_TIMES[:]
steamcmd_executable = DEFAULT_STEAMCMD_EXECUTABLE
steamcmd_install_dir = DEFAULT_STEAMCMD_INSTALL_DIR
save_dir = DEFAULT_SAVE_DIR
backup_dir = DEFAULT_BACKUP_DIR

def create_splash_screen(root):
    """Создание экрана загрузки."""
    logger.info("Создание экрана загрузки")
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry("400x100+500+300")
    splash.attributes("-alpha", 0.8)
    splash.attributes("-topmost", True)
    
    label = tk.Label(
        splash,
        text="Запуск утилиты сервера, ожидайте",
        font=("Arial", 14),
        fg="blue",
        bg="white",
        pady=20
    )
    label.pack(expand=True, fill="both")
    
    splash.update()
    logger.info("Экран загрузки отображен")
    return splash

def create_backup_splash(root):
    """Создание окна уведомления о бэкапе."""
    logger.info("Создание окна бэкапа")
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry("400x100+500+300")
    splash.attributes("-alpha", 0.8)
    splash.attributes("-topmost", True)
    
    label = tk.Label(
        splash,
        text="Утилита работает над сохранением ваших данных, пожалуйста, подождите",
        font=("Arial", 14),
        fg="blue",
        bg="white",
        pady=20,
        wraplength=350
    )
    label.pack(expand=True, fill="both")
    
    splash.update()
    logger.info("Окно бэкапа отображено")
    return splash

def create_update_splash(root):
    """Создание окна уведомления об обновлении."""
    logger.info("Создание окна обновления")
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry("400x100+500+300")
    splash.attributes("-alpha", 0.8)
    splash.attributes("-topmost", True)
    
    label = tk.Label(
        splash,
        text="Утилита работает над обновлением сервера, пожалуйста, подождите",
        font=("Arial", 14),
        fg="blue",
        bg="white",
        pady=20,
        wraplength=350
    )
    label.pack(expand=True, fill="both")
    
    splash.update()
    logger.info("Окно обновления отображено")
    return splash

def load_settings(time1_entry, time2_entry, args_entry, save_dir_entry, backup_dir_entry, steamcmd_exe_entry, steamcmd_dir_entry, saved_times_label, saved_args_label, saved_paths_label, auto_start_var):
    """Загрузка настроек из файла."""
    global restart_times, server_args, auto_start, steamcmd_executable, steamcmd_install_dir, save_dir, backup_dir
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            restart_times = [dt_time(*map(int, t.split(":"))) for t in data.get("restart_times", ["12:00", "21:00"])]
            server_args = data.get("args", DEFAULT_ARGS[:])
            auto_start = data.get("auto_start", False)
            steamcmd_executable = data.get("steamcmd_executable", DEFAULT_STEAMCMD_EXECUTABLE)
            steamcmd_install_dir = data.get("steamcmd_install_dir", DEFAULT_STEAMCMD_INSTALL_DIR)
            save_dir = data.get("save_dir", DEFAULT_SAVE_DIR)
            backup_dir = data.get("backup_dir", DEFAULT_BACKUP_DIR)
        
        time1_entry.delete(0, tk.END)
        time1_entry.insert(0, f"{restart_times[0].hour:02d}:{restart_times[0].minute:02d}")
        time2_entry.delete(0, tk.END)
        time2_entry.insert(0, f"{restart_times[1].hour:02d}:{restart_times[1].minute:02d}")
        args_entry.delete(0, tk.END)
        args_entry.insert(0, " ".join(server_args))
        save_dir_entry.delete(0, tk.END)
        save_dir_entry.insert(0, save_dir)
        backup_dir_entry.delete(0, tk.END)
        backup_dir_entry.insert(0, backup_dir)
        steamcmd_exe_entry.delete(0, tk.END)
        steamcmd_exe_entry.insert(0, steamcmd_executable)
        steamcmd_dir_entry.delete(0, tk.END)
        steamcmd_dir_entry.insert(0, steamcmd_install_dir)
        saved_times_label.config(text=f"Время рестарта: {time1_entry.get()}, {time2_entry.get()}")
        saved_args_label.config(text=f"Аргументы: {' '.join(server_args)}")
        saved_paths_label.config(text=f"Пути: SteamCMD={steamcmd_executable}, Сервер={steamcmd_install_dir}, Сохранения={save_dir}, Бэкапы={backup_dir}")
        auto_start_var.set(auto_start)
        logger.info("Настройки загружены из settings.json")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Ошибка загрузки настроек: {e}. Используются значения по умолчанию")
        restart_times = DEFAULT_RESTART_TIMES[:]
        server_args = DEFAULT_ARGS[:]
        auto_start = False
        steamcmd_executable = DEFAULT_STEAMCMD_EXECUTABLE
        steamcmd_install_dir = DEFAULT_STEAMCMD_INSTALL_DIR
        save_dir = DEFAULT_SAVE_DIR
        backup_dir = DEFAULT_BACKUP_DIR
        time1_entry.delete(0, tk.END)
        time1_entry.insert(0, "12:00")
        time2_entry.delete(0, tk.END)
        time2_entry.insert(0, "21:00")
        args_entry.delete(0, tk.END)
        args_entry.insert(0, " ".join(DEFAULT_ARGS))
        save_dir_entry.delete(0, tk.END)
        save_dir_entry.insert(0, DEFAULT_SAVE_DIR)
        backup_dir_entry.delete(0, tk.END)
        backup_dir_entry.insert(0, DEFAULT_BACKUP_DIR)
        steamcmd_exe_entry.delete(0, tk.END)
        steamcmd_exe_entry.insert(0, DEFAULT_STEAMCMD_EXECUTABLE)
        steamcmd_dir_entry.delete(0, tk.END)
        steamcmd_dir_entry.insert(0, DEFAULT_STEAMCMD_INSTALL_DIR)
        saved_times_label.config(text="Время рестарта: 12:00, 21:00")
        saved_args_label.config(text=f"Аргументы: {' '.join(DEFAULT_ARGS)}")
        saved_paths_label.config(text=f"Пути: SteamCMD={DEFAULT_STEAMCMD_EXECUTABLE}, Сервер={DEFAULT_STEAMCMD_INSTALL_DIR}, Сохранения={DEFAULT_SAVE_DIR}, Бэкапы={DEFAULT_BACKUP_DIR}")
        auto_start_var.set(False)

def save_settings():
    """Сохранение настроек в файл."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "restart_times": [f"{t.hour:02d}:{t.minute:02d}" for t in restart_times],
                "args": server_args,
                "auto_start": auto_start,
                "steamcmd_executable": steamcmd_executable,
                "steamcmd_install_dir": steamcmd_install_dir,
                "save_dir": save_dir,
                "backup_dir": backup_dir
            }, f, indent=4)
        logger.info("Настройки сохранены в settings.json")
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек: {e}")

def signal_handler(sig, frame):
    """Обработчик сигнала Ctrl+C."""
    global shutdown_flag
    logger.info("Получен сигнал Ctrl+C. Выполняется graceful shutdown...")
    shutdown_flag = True
    if current_process:
        try:
            current_process.terminate()
            current_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("Процесс не завершился вовремя, принудительное завершение...")
            current_process.kill()

def validate_time_input(time_str):
    """Проверка формата времени HH:MM."""
    pattern = r"^\d{1,2}:\d{2}$"
    if not re.match(pattern, time_str):
        return False
    try:
        hours, minutes = map(int, time_str.split(":"))
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return True
        return False
    except ValueError:
        return False

def validate_path(path_str):
    """Проверка существования пути."""
    return os.path.exists(os.path.dirname(path_str)) or path_str == ""

def backup_server(root, log_widget):
    """Создание бэкапа файлов сохранений."""
    if server_running:
        messagebox.showerror("Ошибка", "Сначала остановите сервер")
        logger.warning("Попытка бэкапа при запущенном сервере")
        return
    
    logger.info("Запуск процесса бэкапа")
    backup_splash = create_backup_splash(root)
    
    try:
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.zip")
        
        files_to_backup = [os.path.join(save_dir, f) for f in SAVE_FILES if os.path.isfile(os.path.join(save_dir, f))]
        if not files_to_backup:
            logger.error(f"Файлы для бэкапа не найдены в {save_dir}")
            log_queue.put(f"Ошибка: Файлы для бэкапа не найдены в {save_dir}")
            messagebox.showerror("Ошибка", f"Файлы для бэкапа не найдены в {save_dir}")
            backup_splash.destroy()
            return
        
        with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in files_to_backup:
                zipf.write(file, os.path.basename(file))
                logger.info(f"Добавлен файл в архив: {file}")
                log_queue.put(f"Добавлен файл в архив: {os.path.basename(file)}")
        
        logger.info(f"Бэкап успешно создан: {backup_file}")
        log_queue.put(f"Бэкап успешно создан: {backup_file}")
        messagebox.showinfo("Успех", f"Бэкап создан: {backup_file}")
    except Exception as e:
        logger.error(f"Ошибка при создании бэкапа: {e}")
        log_queue.put(f"Ошибка при создании бэкапа: {e}")
        messagebox.showerror("Ошибка", f"Ошибка при создании бэкапа: {e}")
    
    backup_splash.destroy()

def update_server(root, log_widget):
    """Обновление сервера через SteamCMD в отдельном потоке."""
    if server_running:
        messagebox.showerror("Ошибка", "Сначала остановите сервер")
        logger.warning("Попытка обновления при запущенном сервере")
        return
    
    logger.info(f"Запуск обновления сервера через {steamcmd_executable}")
    update_splash = create_update_splash(root)
    
    def run_update():
        try:
            if not os.path.isfile(steamcmd_executable):
                logger.error(f"Файл {steamcmd_executable} не найден")
                log_queue.put(f"Ошибка: {steamcmd_executable} не найден")
                root.after(0, lambda: messagebox.showerror("Ошибка", f"Файл {steamcmd_executable} не найден"))
                root.after(0, update_splash.destroy)
                return
            
            args = ["+force_install_dir", steamcmd_install_dir, "+login", "anonymous", "+app_update", "3792580", "+quit"]
            process = subprocess.Popen(
                [steamcmd_executable] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors='replace',
                creationflags=0x08000000
            )
            logger.info(f"SteamCMD запущен с PID: {process.pid}")
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    log_queue.put(line.strip())
            
            for line in process.stderr:
                if line:
                    log_queue.put(f"STDERR: {line.strip()}")
            
            return_code = process.returncode
            if return_code == 0:
                logger.info("Обновление сервера завершено успешно")
                log_queue.put("Обновление сервера завершено успешно")
                root.after(0, lambda: messagebox.showinfo("Успех", "Обновление сервера завершено"))
            else:
                logger.error(f"Ошибка обновления сервера, код возврата: {return_code}")
                log_queue.put(f"Ошибка обновления сервера, код возврата: {return_code}")
                root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка обновления, код возврата: {return_code}"))
        except Exception as e:
            logger.error(f"Ошибка при обновлении сервера: {e}")
            log_queue.put(f"Ошибка при обновлении сервера: {e}")
            root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при обновлении: {e}"))
        root.after(0, update_splash.destroy)
    
    threading.Thread(target=run_update, daemon=True).start()

def read_output(process, log_widget):
    """Чтение вывода процесса и добавление в текстовое поле."""
    while True:
        try:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                log_queue.put(line.strip())
        except Exception as e:
            log_queue.put(f"Ошибка чтения вывода: {e}")
    
    for line in process.stderr:
        if line:
            log_queue.put(f"STDERR: {line.strip()}")

def update_log_widget(log_widget, root):
    """Обновление текстового поля логами из очереди."""
    try:
        while True:
            line = log_queue.get_nowait()
            log_widget.insert(tk.END, line + "\n")
            log_widget.see(tk.END)
    except queue.Empty:
        pass
    root.after(100, update_log_widget, log_widget, root)

def run_server(log_widget, notebook):
    """Запуск сервера и контроль его работы."""
    global shutdown_flag, restart_now, current_process, start_time, server_running
    if auto_start:
        server_running = True
    
    while not shutdown_flag:
        if not server_running:
            notebook.tab(1, state="normal")
            notebook.tab(2, state="normal")
            time.sleep(1)
            continue
        else:
            notebook.tab(1, state="disabled")
            notebook.tab(2, state="disabled")
        
        logger.info(f"Попытка запуска {SERVER_EXECUTABLE} с аргументами: {' '.join(server_args)}")
        start_time = time.time()
        
        try:
            if not os.path.isfile(SERVER_EXECUTABLE):
                logger.error(f"Файл {SERVER_EXECUTABLE} не найден в текущей директории: {os.getcwd()}")
                shutdown_flag = True
                break
            if not os.access(SERVER_EXECUTABLE, os.X_OK):
                logger.error(f"Нет прав на запуск {SERVER_EXECUTABLE}")
                shutdown_flag = True
                break
            
            current_process = subprocess.Popen(
                [SERVER_EXECUTABLE] + server_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors='replace',
                creationflags=0x08000000
            )
            logger.info(f"Сервер запущен с PID: {current_process.pid}")
            
            output_thread = threading.Thread(target=read_output, args=(current_process, log_widget), daemon=True)
            output_thread.start()
            
            while server_running and not shutdown_flag:
                current_time = datetime.now().time()
                if restart_now or any(current_time.hour == rt.hour and current_time.minute == rt.minute for rt in restart_times):
                    reason = "рестарт по времени" if not restart_now else "ручной рестарт"
                    logger.info(f"Остановка сервера по запросу ({reason})...")
                    current_process.terminate()
                    try:
                        current_process.wait(timeout=10)
                        logger.info("Сервер остановлен")
                    except subprocess.TimeoutExpired:
                        logger.warning("Процесс не завершился вовремя, принудительное завершение...")
                        current_process.kill()
                    restart_now = False
                    break
                
                if current_process.poll() is not None:
                    return_code = current_process.returncode
                    logger.error(f"Сервер неожиданно завершил работу. Код возврата: {return_code}")
                    break
                
                time.sleep(1)
                
        except subprocess.SubprocessError as e:
            logger.error(f"Ошибка при запуске сервера: {e}")
            shutdown_flag = True
            break
        
        current_process = None
        if server_running and not shutdown_flag:
            logger.info("Перезапуск сервера через 5 секунд...")
            time.sleep(5)

def update_timer(root, label, status_label, notebook):
    """Обновление таймера и статуса."""
    if shutdown_flag:
        root.quit()
        return
    
    current_time = datetime.now().time()
    next_restart = None
    for rt in restart_times:
        if current_time <= rt:
            next_restart = rt
            break
    if not next_restart:
        next_restart = restart_times[0]
    
    delta = (datetime.combine(datetime.today(), next_restart) - datetime.combine(datetime.today(), current_time)).total_seconds()
    if delta < 0:
        delta += 24 * 3600
    label.config(text=f"До рестарта: {format_time(delta)}")
    
    status_label.config(text=f"Статус: {'Запущен' if server_running else 'Остановлен'}")
    notebook.tab(1, state="disabled" if server_running else "normal")
    notebook.tab(2, state="disabled" if server_running else "normal")
    root.after(1000, update_timer, root, label, status_label, notebook)

def format_time(seconds):
    """Форматирование времени в ЧЧ:ММ:СС."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def trigger_start():
    """Обработчик нажатия кнопки старта."""
    global server_running
    if not server_running:
        logger.info("Запрос запуска сервера через GUI")
        server_running = True

def trigger_restart():
    """Обработчик нажатия кнопки рестарта."""
    global restart_now
    if server_running:
        logger.info("Запрос немедленного рестарта через GUI")
        restart_now = True

def trigger_stop():
    """Обработчик нажатия кнопки остановки."""
    global server_running
    logger.info("Запрос остановки сервера через GUI")
    server_running = False
    if current_process:
        try:
            current_process.terminate()
            current_process.wait(timeout=10)
            logger.info("Сервер остановлен")
        except subprocess.TimeoutExpired:
            logger.warning("Процесс не завершился вовремя, принудительное завершение...")
            current_process.kill()

def save_restart_times(time1_entry, time2_entry, saved_times_label):
    """Сохранение времени рестарта."""
    global restart_times
    time1_str = time1_entry.get()
    time2_str = time2_entry.get()
    
    if not (validate_time_input(time1_str) and validate_time_input(time2_str)):
        messagebox.showerror("Ошибка", "Введите время в формате ЧЧ:ММ (например, 12:35)")
        return
    
    try:
        h1, m1 = map(int, time1_str.split(":"))
        h2, m2 = map(int, time2_str.split(":"))
        restart_times = [dt_time(h1, m1), dt_time(h2, m2)]
        saved_times_label.config(text=f"Время рестарта: {time1_str}, {time2_str}")
        logger.info(f"Установлено время рестарта: {time1_str}, {time2_str}")
        save_settings()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Неверный формат времени: {e}")

def save_args(args_entry, saved_args_label):
    """Сохранение аргументов запуска."""
    global server_args
    args_str = args_entry.get().strip()
    if args_str:
        server_args = args_str.split()
    else:
        server_args = DEFAULT_ARGS[:]
    saved_args_label.config(text=f"Аргументы: {' '.join(server_args)}")
    logger.info(f"Установлены аргументы: {' '.join(server_args)}")
    save_settings()

def save_paths(save_dir_entry, backup_dir_entry, steamcmd_exe_entry, steamcmd_dir_entry, saved_paths_label):
    """Сохранение путей для бэкапа и обновления."""
    global save_dir, backup_dir, steamcmd_executable, steamcmd_install_dir
    save_dir = save_dir_entry.get().strip()
    backup_dir = backup_dir_entry.get().strip()
    steamcmd_executable = steamcmd_exe_entry.get().strip()
    steamcmd_install_dir = steamcmd_dir_entry.get().strip()
    
    if not validate_path(save_dir):
        messagebox.showerror("Ошибка", f"Недопустимый путь для сохранений: {save_dir}")
        return
    if not validate_path(backup_dir):
        messagebox.showerror("Ошибка", f"Недопустимый путь для бэкапов: {backup_dir}")
        return
    if not validate_path(steamcmd_executable):
        messagebox.showerror("Ошибка", f"Недопустимый путь для SteamCMD: {steamcmd_executable}")
        return
    if not validate_path(steamcmd_install_dir):
        messagebox.showerror("Ошибка", f"Недопустимый путь для сервера: {steamcmd_install_dir}")
        return
    
    saved_paths_label.config(text=f"Пути: SteamCMD={steamcmd_executable}, Сервер={steamcmd_install_dir}, Сохранения={save_dir}, Бэкапы={backup_dir}")
    logger.info(f"Установлены пути: SteamCMD={steamcmd_executable}, Сервер={steamcmd_install_dir}, Сохранения={save_dir}, Бэкапы={backup_dir}")
    save_settings()

def toggle_auto_start(var):
    """Обработчик изменения состояния чекбокса автозапуска."""
    global auto_start
    auto_start = var.get()
    logger.info(f"Автозапуск {'включён' if auto_start else 'выключен'}")
    save_settings()

def create_gui(root):
    """Создание графического интерфейса."""
    root.title("SCUM Server Manager")
    root.geometry("600x500")
    root.resizable(True, True)
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Вкладка "Основное"
    main_frame = ttk.Frame(notebook, padding="10")
    notebook.add(main_frame, text="Основное")
    
    status_label = ttk.Label(main_frame, text="Статус: Остановлен", font=("Arial", 12))
    status_label.pack(pady=5)
    
    timer_label = ttk.Label(main_frame, text="До рестарта: --:--:--", font=("Arial", 14))
    timer_label.pack(pady=5)
    
    time_frame = ttk.Frame(main_frame)
    time_frame.pack(pady=10)
    
    ttk.Label(time_frame, text="Время рестарта 1 (ЧЧ:ММ):").pack(side=tk.LEFT)
    time1_entry = ttk.Entry(time_frame, width=6)
    time1_entry.pack(side=tk.LEFT, padx=5)
    
    ttk.Label(time_frame, text="Время рестарта 2 (ЧЧ:ММ):").pack(side=tk.LEFT)
    time2_entry = ttk.Entry(time_frame, width=6)
    time2_entry.pack(side=tk.LEFT, padx=5)
    
    save_button = ttk.Button(time_frame, text="Сохранить", command=lambda: save_restart_times(time1_entry, time2_entry, saved_times_label))
    save_button.pack(side=tk.LEFT, padx=5)
    
    saved_times_label = ttk.Label(main_frame, text="Время рестарта: 12:00, 21:00", font=("Arial", 10))
    saved_times_label.pack(pady=5)
    
    args_frame = ttk.Frame(main_frame)
    args_frame.pack(pady=10)
    
    ttk.Label(args_frame, text="Аргументы запуска:").pack(side=tk.LEFT)
    args_entry = ttk.Entry(args_frame, width=30)
    args_entry.pack(side=tk.LEFT, padx=5)
    
    save_args_button = ttk.Button(args_frame, text="Сохранить аргументы", command=lambda: save_args(args_entry, saved_args_label))
    save_args_button.pack(side=tk.LEFT, padx=5)
    
    saved_args_label = ttk.Label(main_frame, text=f"Аргументы: {' '.join(DEFAULT_ARGS)}", font=("Arial", 10))
    saved_args_label.pack(pady=5)
    
    auto_start_var = tk.BooleanVar(value=auto_start)
    auto_start_check = ttk.Checkbutton(main_frame, text="Автозапуск сервера", variable=auto_start_var, command=lambda: toggle_auto_start(auto_start_var))
    auto_start_check.pack(pady=5)
    
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=10)
    
    start_button = ttk.Button(button_frame, text="Старт", command=trigger_start)
    start_button.pack(side=tk.LEFT, padx=5)
    
    restart_button = ttk.Button(button_frame, text="Рестарт сейчас", command=trigger_restart)
    restart_button.pack(side=tk.LEFT, padx=5)
    
    stop_button = ttk.Button(button_frame, text="Остановить", command=trigger_stop)
    stop_button.pack(side=tk.LEFT, padx=5)
    
    # Вкладка "Бэкап"
    backup_frame = ttk.Frame(notebook, padding="10")
    notebook.add(backup_frame, text="Бэкап")
    
    ttk.Label(backup_frame, text="Путь к сохранениям:").pack(pady=5)
    save_dir_entry = ttk.Entry(backup_frame, width=50)
    save_dir_entry.pack(pady=5)
    
    ttk.Label(backup_frame, text="Путь к бэкапам:").pack(pady=5)
    backup_dir_entry = ttk.Entry(backup_frame, width=50)
    backup_dir_entry.pack(pady=5)
    
    save_paths_button = ttk.Button(backup_frame, text="Сохранить пути", command=lambda: save_paths(save_dir_entry, backup_dir_entry, steamcmd_exe_entry, steamcmd_dir_entry, saved_paths_label))
    save_paths_button.pack(pady=5)
    
    backup_button = ttk.Button(backup_frame, text="Сделать бэкап", command=lambda: backup_server(root, log_widget))
    backup_button.pack(pady=5)
    
    # Вкладка "Обновление"
    update_frame = ttk.Frame(notebook, padding="10")
    notebook.add(update_frame, text="Обновление")
    
    ttk.Label(update_frame, text="Путь к SteamCMD:").pack(pady=5)
    steamcmd_exe_entry = ttk.Entry(update_frame, width=50)
    steamcmd_exe_entry.pack(pady=5)
    
    ttk.Label(update_frame, text="Путь к серверу:").pack(pady=5)
    steamcmd_dir_entry = ttk.Entry(update_frame, width=50)
    steamcmd_dir_entry.pack(pady=5)
    
    save_paths_button_update = ttk.Button(update_frame, text="Сохранить пути", command=lambda: save_paths(save_dir_entry, backup_dir_entry, steamcmd_exe_entry, steamcmd_dir_entry, saved_paths_label))
    save_paths_button_update.pack(pady=5)
    
    update_button = ttk.Button(update_frame, text="Обновить сервер", command=lambda: update_server(root, log_widget))
    update_button.pack(pady=5)
    
    saved_paths_label = ttk.Label(main_frame, text=f"Пути: SteamCMD={DEFAULT_STEAMCMD_EXECUTABLE}, Сервер={DEFAULT_STEAMCMD_INSTALL_DIR}, Сохранения={DEFAULT_SAVE_DIR}, Бэкапы={DEFAULT_BACKUP_DIR}", font=("Arial", 10))
    saved_paths_label.pack(pady=5)
    
    # Текстовое поле для логов
    log_frame = ttk.Frame(main_frame)
    log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    log_widget = tk.Text(log_frame, height=10, wrap=tk.WORD, state='normal', font=("Courier", 10))
    log_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_widget.config(yscrollcommand=scrollbar.set)
    
    # Загрузка настроек
    load_settings(time1_entry, time2_entry, args_entry, save_dir_entry, backup_dir_entry, steamcmd_exe_entry, steamcmd_dir_entry, saved_times_label, saved_args_label, saved_paths_label, auto_start_var)
    
    # Запуск обновления таймера и логов
    root.after(1000, update_timer, root, timer_label, status_label, notebook)
    root.after(100, update_log_widget, log_widget, root)
    
    return root, log_widget, notebook

def main():
    """Основная функция."""
    global shutdown_flag
    
    root = tk.Tk()
    root.withdraw()
    splash = create_splash_screen(root)
    
    logger.info(f"Запуск скрипта управления сервером {SERVER_EXECUTABLE}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    
    root, log_widget, notebook = create_gui(root)
    server_thread = threading.Thread(target=run_server, args=(log_widget, notebook), daemon=True)
    server_thread.start()
    
    root.after(2000, lambda: [splash.destroy(), root.deiconify()])
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        shutdown_flag = True
    
    logger.info("Скрипт завершен")

if __name__ == "__main__":
    main()