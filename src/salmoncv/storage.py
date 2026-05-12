import json
import shutil
from pathlib import Path

T9_BASE = Path("/media/nalaquq/T9/salmoncv")
SD_BASE = Path.home() / "salmoncv"

T9_CAPTURE_DIR = T9_BASE / "captures"
SD_CAPTURE_DIR = SD_BASE / "captures"

DATA_DIR = SD_BASE / "data"
STORAGE_CONF = DATA_DIR / "storage_config.json"


def _load_pref():
    if STORAGE_CONF.exists():
        try:
            return json.loads(STORAGE_CONF.read_text())["mode"]
        except (json.JSONDecodeError, KeyError):
            pass
    return "auto"


def set_storage_pref(mode):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_CONF.write_text(json.dumps({"mode": mode}))


def t9_available():
    mount = Path("/media/nalaquq/T9")
    if not mount.exists():
        return False
    try:
        usage = shutil.disk_usage(str(mount))
        if usage.free < 100 * 1024 * 1024:
            return False
        test = mount / ".salmoncv_write_test"
        test.write_text("ok")
        test.unlink()
        return True
    except OSError:
        return False


def get_capture_dir():
    pref = _load_pref()
    if pref == "sd":
        SD_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        return SD_CAPTURE_DIR
    if pref == "t9":
        if t9_available():
            T9_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
            return T9_CAPTURE_DIR
        SD_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        return SD_CAPTURE_DIR
    if t9_available():
        T9_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        return T9_CAPTURE_DIR
    SD_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    return SD_CAPTURE_DIR


def get_storage_info():
    pref = _load_pref()
    t9_ok = t9_available()
    capture_dir = get_capture_dir()
    using_t9 = str(capture_dir).startswith(str(T9_BASE))

    result = {
        "mode": pref,
        "drive": "Samsung T9" if using_t9 else "SD Card",
        "capture_dir": str(capture_dir),
        "t9_available": t9_ok,
    }

    if t9_ok:
        t9_disk = shutil.disk_usage("/media/nalaquq/T9")
        result["t9_total_gb"] = round(t9_disk.total / (1024 ** 3), 1)
        result["t9_used_gb"] = round(t9_disk.used / (1024 ** 3), 1)
        result["t9_free_gb"] = round(t9_disk.free / (1024 ** 3), 1)
        result["t9_percent"] = round(t9_disk.used / t9_disk.total * 100, 1)

    sd_disk = shutil.disk_usage(str(Path.home()))
    result["sd_total_gb"] = round(sd_disk.total / (1024 ** 3), 1)
    result["sd_used_gb"] = round(sd_disk.used / (1024 ** 3), 1)
    result["sd_free_gb"] = round(sd_disk.free / (1024 ** 3), 1)
    result["sd_percent"] = round(sd_disk.used / sd_disk.total * 100, 1)

    return result
