import csv
import json
import os
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from salmoncv import storage
from salmoncv.web import app as web_module


@pytest.fixture(autouse=True)
def patch_all_paths(tmp_path, monkeypatch):
    """Redirect storage and web module paths to tmp_path."""
    data = tmp_path / "data"
    data.mkdir()
    captures = tmp_path / "captures"
    captures.mkdir()
    thumbs = data / "thumbs"

    # Patch storage module
    monkeypatch.setattr(storage, "T9_BASE", tmp_path / "t9" / "salmoncv")
    monkeypatch.setattr(storage, "SD_BASE", tmp_path)
    monkeypatch.setattr(storage, "T9_CAPTURE_DIR", tmp_path / "t9" / "salmoncv" / "captures")
    monkeypatch.setattr(storage, "SD_CAPTURE_DIR", captures)
    monkeypatch.setattr(storage, "DATA_DIR", data)
    monkeypatch.setattr(storage, "STORAGE_CONF", data / "storage_config.json")

    # Patch web module paths
    monkeypatch.setattr(web_module, "DATA_DIR", data)
    monkeypatch.setattr(web_module, "THUMB_DIR", thumbs)
    monkeypatch.setattr(web_module, "PID_FILE", data / ".camera_pid")
    monkeypatch.setattr(web_module, "LIGHTS_PID", data / ".lights_pid")
    monkeypatch.setattr(web_module, "STARLINK_PID", data / ".starlink_pid")
    monkeypatch.setattr(web_module, "SENSORS_PID", data / ".sensors_pid")
    monkeypatch.setattr(web_module, "LIGHTS_CONF", data / "lights_config.json")
    monkeypatch.setattr(web_module, "STARLINK_CONF", data / "starlink_config.json")
    monkeypatch.setattr(web_module, "SYSTEM_CONF", data / "system_config.json")
    monkeypatch.setattr(web_module, "WEB_LOG", data / "web_log.csv")

    return tmp_path


@pytest.fixture
def client(tmp_path):
    app = web_module.create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestPageRoutes:
    def test_dashboard(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_camera_page(self, client):
        r = client.get("/camera")
        assert r.status_code == 200

    def test_gallery_page(self, client):
        r = client.get("/gallery")
        assert r.status_code == 200

    def test_sensors_page(self, client):
        r = client.get("/sensors")
        assert r.status_code == 200

    def test_monitor_page(self, client):
        r = client.get("/monitor")
        assert r.status_code == 200

    def test_power_page(self, client):
        r = client.get("/power")
        assert r.status_code == 200

    def test_settings_page(self, client):
        r = client.get("/settings")
        assert r.status_code == 200

    def test_404_for_unknown_route(self, client):
        r = client.get("/nonexistent")
        assert r.status_code == 404


class TestCameraAPI:
    @patch("salmoncv.web.app.subprocess.run")
    def test_capture_success(self, mock_run, client):
        r = client.post("/api/camera/capture",
                        json={"awb": "auto"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert "filename" in data

    @patch("salmoncv.web.app.subprocess.run",
           side_effect=subprocess.CalledProcessError(1, "rpicam-still"))
    def test_capture_failure(self, mock_run, client):
        r = client.post("/api/camera/capture", json={})
        assert r.status_code == 500

    def test_camera_status(self, client):
        r = client.get("/api/camera/status")
        assert r.status_code == 200
        data = r.get_json()
        assert "running" in data
        assert data["running"] is False
        assert "total_images" in data

    def test_stop_when_not_running(self, client):
        r = client.post("/api/camera/stop")
        data = r.get_json()
        assert data["ok"] is False

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_start_timelapse(self, mock_popen, client, tmp_path):
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_popen.return_value = mock_proc

        r = client.post("/api/camera/start",
                        json={"interval": 5, "width": 1920, "height": 1080})
        data = r.get_json()
        assert data["ok"] is True
        assert data["pid"] == 12345

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_start_refuses_when_already_running(self, mock_popen, client, tmp_path):
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        mock_popen.return_value = mock_proc

        client.post("/api/camera/start", json={})

        with patch("os.kill"):
            r = client.post("/api/camera/start", json={})
            data = r.get_json()
            assert data["ok"] is False
            assert "already running" in data["error"]


class TestGalleryAPI:
    def test_empty_gallery(self, client):
        r = client.get("/api/gallery")
        data = r.get_json()
        assert data["total"] == 0
        assert data["images"] == []

    def test_gallery_with_images(self, client, tmp_path):
        captures = storage.get_capture_dir()
        for i in range(3):
            (captures / f"img_{i}.jpg").write_bytes(b"\xff\xd8" + b"\x00" * 100)
        r = client.get("/api/gallery")
        data = r.get_json()
        assert data["total"] == 3

    def test_gallery_pagination(self, client, tmp_path):
        captures = storage.get_capture_dir()
        for i in range(60):
            (captures / f"img_{i:03d}.jpg").write_bytes(b"\xff\xd8" + b"\x00" * 10)
        r = client.get("/api/gallery?page=1")
        data = r.get_json()
        assert len(data["images"]) == 50
        assert data["pages"] == 2

        r2 = client.get("/api/gallery?page=2")
        data2 = r2.get_json()
        assert len(data2["images"]) == 10

    def test_delete_images(self, client, tmp_path):
        captures = storage.get_capture_dir()
        (captures / "del_me.jpg").write_bytes(b"\xff\xd8" + b"\x00" * 10)
        assert (captures / "del_me.jpg").exists()

        r = client.post("/api/gallery/delete",
                        json={"filenames": ["del_me.jpg"]})
        data = r.get_json()
        assert data["ok"] is True
        assert data["deleted"] == 1
        assert not (captures / "del_me.jpg").exists()

    def test_delete_rejects_empty(self, client):
        r = client.post("/api/gallery/delete", json={"filenames": []})
        assert r.status_code == 400

    def test_delete_blocks_path_traversal(self, client, tmp_path):
        captures = storage.get_capture_dir()
        secret = tmp_path / "secret.txt"
        secret.write_text("do not delete")

        r = client.post("/api/gallery/delete",
                        json={"filenames": ["../secret.txt"]})
        data = r.get_json()
        assert data["deleted"] == 0
        assert secret.exists()

    def test_delete_blocks_absolute_path(self, client, tmp_path):
        r = client.post("/api/gallery/delete",
                        json={"filenames": ["/etc/passwd"]})
        data = r.get_json()
        assert data["deleted"] == 0

    def test_delete_blocks_backslash(self, client):
        r = client.post("/api/gallery/delete",
                        json={"filenames": ["..\\secret.txt"]})
        data = r.get_json()
        assert data["deleted"] == 0


class TestSensorsAPI:
    def test_current_returns_json(self, client):
        r = client.get("/api/sensors/current")
        assert r.status_code == 200
        data = r.get_json()
        # On non-Pi machine, sensor won't be available
        assert "ok" in data or "error" in data

    def test_history_empty(self, client):
        r = client.get("/api/sensors/history")
        data = r.get_json()
        assert data["rows"] == []

    def test_history_with_data(self, client, tmp_path):
        log = web_module.DATA_DIR / "sensor_log.csv"
        with open(log, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "timestamp", "temperature_c", "temperature_f",
                "humidity", "pressure_hpa",
            ])
            w.writeheader()
            w.writerow({
                "timestamp": "2026-05-11 12:00:00",
                "temperature_c": "22.5",
                "temperature_f": "72.5",
                "humidity": "45.0",
                "pressure_hpa": "1013.25",
            })
        r = client.get("/api/sensors/history?limit=10")
        data = r.get_json()
        assert len(data["rows"]) == 1
        assert data["rows"][0]["temperature_c"] == "22.5"

    def test_chart_empty(self, client):
        r = client.get("/api/sensors/chart")
        data = r.get_json()
        assert data["timestamps"] == []


class TestPowerAPI:
    @patch("salmoncv.power.subprocess.run")
    def test_lights_on(self, mock_run, client):
        r = client.post("/api/power/lights", json={"action": "on"})
        data = r.get_json()
        assert data["ok"] is True

    @patch("salmoncv.power.subprocess.run")
    def test_lights_off(self, mock_run, client):
        r = client.post("/api/power/lights", json={"action": "off"})
        data = r.get_json()
        assert data["ok"] is True

    def test_lights_invalid_action(self, client):
        r = client.post("/api/power/lights", json={"action": "blink"})
        assert r.status_code == 400

    def test_power_status(self, client):
        r = client.get("/api/power/status")
        data = r.get_json()
        assert "lights" in data
        assert "starlink" in data
        assert data["lights"]["on"] is False

    def test_power_draw(self, client):
        r = client.get("/api/power/draw")
        data = r.get_json()
        assert "pi" in data
        assert "total" in data
        assert data["pi"] == 5.0


class TestStorageAPI:
    def test_get_storage(self, client):
        r = client.get("/api/storage")
        data = r.get_json()
        assert "mode" in data
        assert "drive" in data

    def test_set_storage_sd(self, client):
        r = client.post("/api/storage/set", json={"mode": "sd"})
        data = r.get_json()
        assert data["ok"] is True
        assert data["mode"] == "sd"

    def test_set_storage_invalid(self, client):
        r = client.post("/api/storage/set", json={"mode": "usb"})
        assert r.status_code == 400


class TestSchedulerAPI:
    def test_lights_config_defaults(self, client):
        r = client.get("/api/scheduler/lights/config")
        data = r.get_json()
        assert data["mode"] == "auto"
        assert data["running"] is False

    def test_starlink_config_defaults(self, client):
        r = client.get("/api/scheduler/starlink/config")
        data = r.get_json()
        assert data["mode"] == "auto"
        assert data["upload_speed"] == 5.0

    def test_lights_stop_when_not_running(self, client):
        r = client.post("/api/scheduler/lights/stop")
        data = r.get_json()
        assert data["ok"] is False

    def test_starlink_stop_when_not_running(self, client):
        r = client.post("/api/scheduler/starlink/stop")
        data = r.get_json()
        assert data["ok"] is False


class TestSystemAPI:
    def test_system_info(self, client):
        r = client.get("/api/system")
        data = r.get_json()
        assert "hostname" in data
        assert "image_count" in data

    def test_system_running_all_stopped(self, client):
        r = client.get("/api/system/running")
        data = r.get_json()
        assert data["all_running"] is False
        assert data["any_running"] is False
        assert data["camera"] is False

    def test_system_stop_all(self, client):
        r = client.post("/api/system/stop")
        data = r.get_json()
        assert data["ok"] is True


class TestLogsAPI:
    def test_allowed_log(self, client, tmp_path):
        log = web_module.DATA_DIR / "sensor_log.csv"
        log.write_text("timestamp,value\n2026-05-11,1\n")
        r = client.get("/api/logs/sensor_log.csv")
        assert r.status_code == 200

    def test_disallowed_log(self, client):
        r = client.get("/api/logs/../../etc/passwd")
        assert r.status_code == 404

    def test_nonexistent_log(self, client):
        r = client.get("/api/logs/sensor_log.csv")
        assert r.status_code == 404


class TestWebLog:
    @patch("salmoncv.web.app.subprocess.run")
    def test_capture_logs_activity(self, mock_run, client, tmp_path):
        client.post("/api/camera/capture", json={})
        log = web_module.WEB_LOG
        assert log.exists()
        content = log.read_text()
        assert "capture" in content
