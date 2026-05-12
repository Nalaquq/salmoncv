from pathlib import Path

T9_BASE = Path("/media/nalaquq/T9/salmoncv")
SD_BASE = Path.home() / "salmoncv"

T9_CAPTURE_DIR = T9_BASE / "captures"
SD_CAPTURE_DIR = SD_BASE / "captures"

DATA_DIR = SD_BASE / "data"


def t9_available():
    mount = Path("/media/nalaquq/T9")
    if not mount.exists():
        return False
    try:
        usage = __import__("shutil").disk_usage(str(mount))
        if usage.free < 100 * 1024 * 1024:
            return False
        test = mount / ".salmoncv_write_test"
        test.write_text("ok")
        test.unlink()
        return True
    except OSError:
        return False


def get_capture_dir():
    if t9_available():
        T9_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        return T9_CAPTURE_DIR
    SD_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    return SD_CAPTURE_DIR


def get_storage_info():
    using_t9 = t9_available()
    capture_dir = T9_CAPTURE_DIR if using_t9 else SD_CAPTURE_DIR
    return {
        "drive": "Samsung T9" if using_t9 else "SD Card",
        "capture_dir": str(capture_dir),
        "t9_available": using_t9,
    }
