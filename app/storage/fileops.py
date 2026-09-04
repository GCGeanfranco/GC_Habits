import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

logger = logging.getLogger(__name__)

MAX_WRITE_ATTEMPTS = 3


def _atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = Path(str(path) + ".tmp")
    for attempt in range(1, MAX_WRITE_ATTEMPTS + 1):
        try:
            tmp_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            os.replace(tmp_path, path)
            return
        except OSError as exc:
            if attempt == MAX_WRITE_ATTEMPTS:
                raise RuntimeError(
                    f"No se pudo escribir {path} tras {MAX_WRITE_ATTEMPTS} intentos."
                ) from exc
            sleep(0.1 * 2 ** (attempt - 1))


def _backup_corrupt(path):
    path = Path(path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    backup_path = Path(str(path) + f".corrupt.{timestamp}")
    os.replace(path, backup_path)


def _read_with_corrupt_handling(path):
    data, _ = _read_with_corrupt_flag(path)
    return data


def _read_with_corrupt_flag(path):
    if not path.exists():
        return {"habits": [], "metadata": {}}, False
    try:
        return json.loads(path.read_text(encoding="utf-8")), False
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        logger.error(
            "Datos corruptos o ilegibles en %s; se hace backup y se reinician.",
            path,
        )
        _backup_corrupt(path)
        return {"habits": [], "metadata": {}}, True