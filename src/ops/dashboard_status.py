import shutil
from pathlib import Path


def build_storage_summary(path_specs):
    rows = []

    for label, folder in path_specs:
        path = Path(folder)
        total_bytes = 0
        file_count = 0

        if path.exists():
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    file_count += 1
                    total_bytes += file_path.stat().st_size

        rows.append({
            "label": label,
            "path": str(path),
            "exists": path.exists(),
            "file_count": file_count,
            "bytes": total_bytes,
        })

    return rows


def get_disk_usage(path="."):
    usage = shutil.disk_usage(path)
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
    }


def read_log_tail(log_path, line_count=120):
    path = Path(log_path)
    if not path.exists():
        return ""

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-int(line_count):])
