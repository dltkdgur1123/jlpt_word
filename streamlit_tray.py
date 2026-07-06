import os
import signal
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item

BASE_DIR = Path(__file__).resolve().parent
PYTHONW = BASE_DIR / 'venv' / 'Scripts' / 'pythonw.exe'
PYTHON = BASE_DIR / 'venv' / 'Scripts' / 'python.exe'
APP_FILE = BASE_DIR / 'streamlit_app.py'
LOG_FILE = BASE_DIR / 'streamlit_tray.log'
HOST = '0.0.0.0'
PORT = '8501'
DASHBOARD_URL = f'http://127.0.0.1:{PORT}'

process = None
process_lock = threading.Lock()


def create_icon_image() -> Image.Image:
    image = Image.new('RGBA', (64, 64), '#111827')
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6, 6, 58, 58), radius=12, fill='#1f2937', outline='#60a5fa', width=2)
    draw.rectangle((18, 18, 46, 46), fill='#60a5fa')
    draw.rectangle((24, 24, 40, 40), fill='#111827')
    return image


def streamlit_command() -> list[str]:
    python_exe = str(PYTHON if PYTHON.exists() else PYTHONW)
    return [
        python_exe,
        '-m',
        'streamlit',
        'run',
        str(APP_FILE),
        '--server.address',
        HOST,
        '--server.port',
        PORT,
        '--server.headless',
        'true',
    ]


def start_streamlit() -> None:
    global process
    with process_lock:
        if process and process.poll() is None:
            return

        env = os.environ.copy()
        env['BROWSER'] = 'none'

        log_handle = open(LOG_FILE, 'a', encoding='utf-8')
        process = subprocess.Popen(
            streamlit_command(),
            cwd=str(BASE_DIR),
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )


def stop_streamlit() -> None:
    global process
    with process_lock:
        if not process or process.poll() is not None:
            process = None
            return

        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        finally:
            process = None


def restart_streamlit(icon: pystray.Icon, _item: item) -> None:
    stop_streamlit()
    time.sleep(1)
    start_streamlit()
    icon.notify('Streamlit 서버를 다시 시작했습니다.', 'JLPT Word')


def open_dashboard(icon: pystray.Icon, _item: item) -> None:
    webbrowser.open(DASHBOARD_URL)


def open_log(_icon: pystray.Icon, _item: item) -> None:
    if LOG_FILE.exists():
        os.startfile(LOG_FILE)


def quit_app(icon: pystray.Icon, _item: item) -> None:
    stop_streamlit()
    icon.stop()


def monitor_process(icon: pystray.Icon) -> None:
    while icon.visible:
        with process_lock:
            current = process
        if current and current.poll() is not None:
            icon.notify('Streamlit 서버가 종료되어 자동으로 다시 시작합니다.', 'JLPT Word')
            start_streamlit()
        time.sleep(5)


def main() -> None:
    start_streamlit()

    icon = pystray.Icon(
        'jlpt_word_streamlit',
        create_icon_image(),
        'JLPT Word Streamlit',
        menu=pystray.Menu(
            item('대시보드 열기', open_dashboard, default=True),
            item('서버 재시작', restart_streamlit),
            item('로그 열기', open_log),
            item('종료', quit_app),
        ),
    )

    monitor = threading.Thread(target=monitor_process, args=(icon,), daemon=True)
    monitor.start()
    icon.run()


if __name__ == '__main__':
    main()
