import json
from pathlib import Path
from unittest.mock import patch

import pytest

from salmoncv import storage


@pytest.fixture(autouse=True)
def patch_paths(tmp_path, monkeypatch):
    """Redirect all storage paths to tmp_path so tests don't touch real filesystems."""
    t9_base = tmp_path / "t9" / "salmoncv"
    sd_base = tmp_path / "sd"
    data_dir = sd_base / "data"
    data_dir.mkdir(parents=True)

    monkeypatch.setattr(storage, "T9_BASE", t9_base)
    monkeypatch.setattr(storage, "SD_BASE", sd_base)
    monkeypatch.setattr(storage, "T9_CAPTURE_DIR", t9_base / "captures")
    monkeypatch.setattr(storage, "SD_CAPTURE_DIR", sd_base / "captures")
    monkeypatch.setattr(storage, "DATA_DIR", data_dir)
    monkeypatch.setattr(storage, "STORAGE_CONF", data_dir / "storage_config.json")

    return tmp_path


class TestLoadPref:
    def test_default_auto(self, tmp_path):
        assert storage._load_pref() == "auto"

    def test_reads_saved_pref(self, tmp_path):
        storage.set_storage_pref("t9")
        assert storage._load_pref() == "t9"

    def test_handles_corrupt_json(self, tmp_path):
        storage.STORAGE_CONF.write_text("not json")
        assert storage._load_pref() == "auto"

    def test_handles_missing_key(self, tmp_path):
        storage.STORAGE_CONF.write_text(json.dumps({"other": "stuff"}))
        assert storage._load_pref() == "auto"


class TestSetStoragePref:
    def test_saves_mode(self, tmp_path):
        storage.set_storage_pref("sd")
        conf = json.loads(storage.STORAGE_CONF.read_text())
        assert conf["mode"] == "sd"

    def test_overwrites_previous(self, tmp_path):
        storage.set_storage_pref("t9")
        storage.set_storage_pref("auto")
        assert storage._load_pref() == "auto"


class TestT9Available:
    def test_not_available_when_not_mounted(self, tmp_path):
        assert storage.t9_available() is False

    def test_available_when_mounted_with_space(self, tmp_path, monkeypatch):
        mount = tmp_path / "t9"
        mount.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(storage, "t9_available", lambda: True)
        assert storage.t9_available() is True


class TestGetCaptureDir:
    def test_returns_sd_when_t9_unavailable(self, tmp_path):
        result = storage.get_capture_dir()
        assert "captures" in str(result)
        assert result.exists()

    def test_respects_sd_pref(self, tmp_path):
        storage.set_storage_pref("sd")
        result = storage.get_capture_dir()
        assert str(storage.SD_CAPTURE_DIR) == str(result)

    def test_t9_pref_falls_back_to_sd(self, tmp_path):
        storage.set_storage_pref("t9")
        result = storage.get_capture_dir()
        assert str(storage.SD_CAPTURE_DIR) == str(result)


class TestGetStorageInfo:
    def test_returns_expected_keys(self, tmp_path):
        info = storage.get_storage_info()
        assert "mode" in info
        assert "drive" in info
        assert "capture_dir" in info
        assert "sd_total_gb" in info
        assert "sd_free_gb" in info

    def test_mode_matches_pref(self, tmp_path):
        storage.set_storage_pref("sd")
        info = storage.get_storage_info()
        assert info["mode"] == "sd"
