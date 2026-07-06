"""
Streamlit 백그라운드 실행기
- 콘솔 창 없음
- 작업 표시줄 아이콘 없음
- 시스템 트레이 아이콘 없음
- 실행한 Streamlit 프로세스 PID를 streamlit_server.pid에 저장
"""

import ctypes
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON = BASE_DIR / "venv" / "Scripts" / "python.exe"
APP_FILE = BASE_DIR / "streamlit_app.py"
LOG_FILE = BASE_DIR / "streamlit_background.log"
PID_FILE = BASE_DIR / "streamlit_server.pid"

HOST = "0.0.0.0"
PORT = "8501"


def process_exists(pid: int) -> bool:
    """Windows에서 PID가 현재 실행 중인지 확인한다."""
    if os.name != "nt" or pid <= 0:
        return False

    process_query_limited_information = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(
        process_query_limited_information,
        False,
        pid,
    )
    if handle:
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    return False


def read_existing_pid() -> int | None:
    if not PID_FILE.exists():
        return None

    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def write_log(message: str) -> None:
    try:
        with LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(message.rstrip() + "\n")
    except OSError:
        pass


def main() -> None:
    if os.name != "nt":
        write_log("[ERROR] 이 실행기는 Windows 전용입니다.")
        return

    if not PYTHON.exists():
        write_log(f"[ERROR] Python 실행 파일을 찾을 수 없습니다: {PYTHON}")
        return

    if not APP_FILE.exists():
        write_log(f"[ERROR] Streamlit 앱 파일을 찾을 수 없습니다: {APP_FILE}")
        return

    existing_pid = read_existing_pid()
    if existing_pid and process_exists(existing_pid):
        # 이미 실행 중이면 중복 실행하지 않는다.
        return

    # 오래된 PID 파일 정리
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass

    env = os.environ.copy()
    env["BROWSER"] = "none"
    env["PYTHONUNBUFFERED"] = "1"

    command = [
        str(PYTHON),
        "-m",
        "streamlit",
        "run",
        str(APP_FILE),
        "--server.address",
        HOST,
        "--server.port",
        PORT,
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]

    creation_flags = (
        subprocess.CREATE_NO_WINDOW
        | subprocess.CREATE_NEW_PROCESS_GROUP
    )

    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = subprocess.SW_HIDE

    try:
        with LOG_FILE.open("a", encoding="utf-8") as log_handle:
            process = subprocess.Popen(
                command,
                cwd=str(BASE_DIR),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=creation_flags,
                startupinfo=startup_info,
                close_fds=True,
            )

        PID_FILE.write_text(str(process.pid), encoding="utf-8")
    except Exception as exc:
        write_log(f"[ERROR] Streamlit 실행 실패: {exc!r}")


if __name__ == "__main__":
    main()
