import csv
import json
import os
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from salmoncv import power, storage
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

    # Patch power module state files so create_app() cleanup targets tmp_path
    monkeypatch.setattr(power, "LIGHTS_STATE", data / ".lights_on_since")
    monkeypatch.setattr(power, "STARLINK_STATE", data / ".starlink_on_since")

    return tmp_path


@pytest.fixture
def client(tmp_path):
    app = web_module.create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestVenvBin:
    def test_venv_bin_resolves_to_directory(self):
        assert web_module.VENV_BIN.is_dir()

    def test_venv_bin_matches_running_python(self):
        import sys
        assert str(web_module.VENV_BIN) == str(Path(sys.executable).parent)


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
    def test_start_timelapse_uses_venv_path(self, mock_popen, client, tmp_path):
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_popen.return_value = mock_proc

        client.post("/api/camera/start", json={})
        cmd = mock_popen.call_args[0][0]
        assert cmd[0] == str(web_module.VENV_BIN / "salmoncv-camera")

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

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_lights_start_uses_venv_path(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 11111
        mock_popen.return_value = mock_proc

        r = client.post("/api/scheduler/lights/start", json={"mode": "auto"})
        data = r.get_json()
        assert data["ok"] is True
        cmd = mock_popen.call_args[0][0]
        assert cmd[0] == str(web_module.VENV_BIN / "salmoncv-lights")

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_starlink_start_uses_venv_path(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 22222
        mock_popen.return_value = mock_proc

        r = client.post("/api/scheduler/starlink/start",
                        json={"mode": "auto", "upload_speed": 5.0})
        data = r.get_json()
        assert data["ok"] is True
        cmd = mock_popen.call_args[0][0]
        assert cmd[0] == str(web_module.VENV_BIN / "salmoncv-starlink")

    def test_lights_stop_when_not_running(self, client):
        r = client.post("/api/scheduler/lights/stop")
        data = r.get_json()
        assert data["ok"] is False

    def test_starlink_stop_when_not_running(self, client):
        r = client.post("/api/scheduler/starlink/stop")
        data = r.get_json()
        assert data["ok"] is False

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_lights_start_stop_roundtrip(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 33333
        mock_popen.return_value = mock_proc

        r = client.post("/api/scheduler/lights/start", json={"mode": "auto"})
        assert r.get_json()["ok"] is True

        with patch("os.kill"):
            r = client.post("/api/scheduler/lights/stop")
            assert r.get_json()["ok"] is True

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_lights_start_saves_config(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 44444
        mock_popen.return_value = mock_proc

        client.post("/api/scheduler/lights/start",
                    json={"mode": "manual", "on_time": "20:00", "off_time": "06:00"})
        conf = json.loads(web_module.LIGHTS_CONF.read_text())
        assert conf["mode"] == "manual"
        assert conf["on_time"] == "20:00"
        assert conf["off_time"] == "06:00"

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_starlink_start_saves_config(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 55555
        mock_popen.return_value = mock_proc

        client.post("/api/scheduler/starlink/start",
                    json={"mode": "manual", "on_time": "14:00",
                          "upload_time": "30", "upload_speed": 10.0,
                          "admin_time": "off", "admin_duration": 20})
        conf = json.loads(web_module.STARLINK_CONF.read_text())
        assert conf["mode"] == "manual"
        assert conf["upload_speed"] == 10.0
        assert conf["admin_time"] == "off"


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
        assert data["lights_relay"] is False
        assert data["starlink_relay"] is False

    def test_system_stop_all(self, client):
        r = client.post("/api/system/stop")
        data = r.get_json()
        assert data["ok"] is True

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_system_start_launches_all_services(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 10001
        mock_popen.return_value = mock_proc

        r = client.post("/api/system/start",
                        json={"camera_interval": 5, "sensor_interval": 60})
        data = r.get_json()
        assert data["ok"] is True
        results = data["results"]
        assert results["camera"]["started"] is True
        assert results["sensors"]["started"] is True
        assert results["lights"]["started"] is True
        assert results["starlink"]["started"] is True
        assert mock_popen.call_count == 4

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_system_start_uses_venv_paths(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 10002
        mock_popen.return_value = mock_proc

        client.post("/api/system/start", json={})
        venv_bin = str(web_module.VENV_BIN)
        for call in mock_popen.call_args_list:
            cmd = call[0][0]
            assert cmd[0].startswith(venv_bin), (
                f"Expected {cmd[0]} to start with {venv_bin}"
            )

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_system_start_saves_config(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 10003
        mock_popen.return_value = mock_proc

        client.post("/api/system/start",
                    json={"camera_interval": 10, "sensor_interval": 120})
        conf = json.loads(web_module.SYSTEM_CONF.read_text())
        assert conf["camera_interval"] == 10
        assert conf["sensor_interval"] == 120
        assert "started_at" in conf

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_system_start_skips_already_running(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 10004
        mock_popen.return_value = mock_proc

        client.post("/api/system/start", json={})

        with patch("os.kill"):
            r = client.post("/api/system/start", json={})
            results = r.get_json()["results"]
            assert results["camera"]["started"] is False
            assert results["camera"]["reason"] == "already running"

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_system_start_then_stop(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 10005
        mock_popen.return_value = mock_proc

        client.post("/api/system/start", json={})

        with patch("os.kill"):
            r = client.post("/api/system/stop")
            data = r.get_json()
            assert data["ok"] is True

        r = client.get("/api/system/running")
        data = r.get_json()
        assert data["any_running"] is False

    @patch("salmoncv.power.subprocess.run")
    @patch("salmoncv.web.app.subprocess.Popen")
    def test_system_stop_turns_off_relays(self, mock_popen, mock_pin, client):
        mock_proc = MagicMock()
        mock_proc.pid = 10009
        mock_popen.return_value = mock_proc

        power.LIGHTS_STATE.write_text("2026-05-12T10:00:00")
        power.STARLINK_STATE.write_text("2026-05-12T10:00:00")

        with patch("os.kill"):
            r = client.post("/api/system/stop")
            data = r.get_json()
            assert data["ok"] is True

        assert not power.LIGHTS_STATE.exists()
        assert not power.STARLINK_STATE.exists()

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_system_running_relays_independent_of_schedulers(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 10007
        mock_popen.return_value = mock_proc

        client.post("/api/system/start", json={})

        with patch("os.kill"):
            r = client.get("/api/system/running")
            data = r.get_json()
            assert data["lights"] is True
            assert data["starlink"] is True
            assert data["lights_relay"] is False
            assert data["starlink_relay"] is False

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_system_running_relays_on_when_state_files_exist(self, mock_popen, tmp_path):
        lights_state = power.LIGHTS_STATE
        starlink_state = power.STARLINK_STATE
        mock_proc = MagicMock()
        mock_proc.pid = 10008
        mock_popen.return_value = mock_proc

        lights_state.write_text("2026-05-12T00:00:00")
        starlink_state.write_text("2026-05-12T00:00:00")

        # create_app clears stale files, so create app AFTER writing them
        # and re-write to simulate relay turning on after startup
        app = web_module.create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            c.post("/api/system/start", json={})
            lights_state.write_text("2026-05-12T00:00:00")
            starlink_state.write_text("2026-05-12T00:00:00")

            with patch("os.kill"):
                r = c.get("/api/system/running")
                data = r.get_json()
                assert data["lights_relay"] is True
                assert data["starlink_relay"] is True

    def test_create_app_clears_stale_relay_state_files(self, tmp_path):
        lights_state = power.LIGHTS_STATE
        starlink_state = power.STARLINK_STATE
        lights_state.write_text("2026-05-11T22:00:00")
        starlink_state.write_text("2026-05-11T22:00:00")
        assert lights_state.exists()
        assert starlink_state.exists()

        web_module.create_app()

        assert not lights_state.exists()
        assert not starlink_state.exists()

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_system_start_then_running_shows_all(self, mock_popen, client):
        mock_proc = MagicMock()
        mock_proc.pid = 10006
        mock_popen.return_value = mock_proc

        client.post("/api/system/start", json={})

        with patch("os.kill"):
            r = client.get("/api/system/running")
            data = r.get_json()
            assert data["all_running"] is True
            assert data["camera"] is True
            assert data["sensors"] is True
            assert data["lights"] is True
            assert data["starlink"] is True


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


class TestPiPowerAPI:
    def test_pi_power_page(self, client):
        r = client.get("/pi-power")
        assert r.status_code == 200
        assert b"Pi Power" in r.data

    def test_pi_status(self, client):
        r = client.get("/api/pi/status")
        data = r.get_json()
        assert "hostname" in data
        assert "uptime" in data
        assert "boot_time" in data
        assert "cpu_temp_c" in data

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_pi_shutdown(self, mock_popen, client):
        r = client.post("/api/pi/shutdown")
        data = r.get_json()
        assert data["ok"] is True
        assert "Shutting down" in data["message"]
        mock_popen.assert_called_once_with(["sudo", "shutdown", "-h", "now"])

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_pi_reboot(self, mock_popen, client):
        r = client.post("/api/pi/reboot")
        data = r.get_json()
        assert data["ok"] is True
        assert "Rebooting" in data["message"]
        mock_popen.assert_called_once_with(["sudo", "reboot"])

    @patch("salmoncv.web.app.subprocess.Popen", side_effect=Exception("permission denied"))
    def test_pi_shutdown_error(self, mock_popen, client):
        r = client.post("/api/pi/shutdown")
        assert r.status_code == 500
        data = r.get_json()
        assert data["ok"] is False
        assert "permission denied" in data["error"]

    @patch("salmoncv.web.app.subprocess.Popen", side_effect=Exception("permission denied"))
    def test_pi_reboot_error(self, mock_popen, client):
        r = client.post("/api/pi/reboot")
        assert r.status_code == 500
        data = r.get_json()
        assert data["ok"] is False

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_pi_shutdown_logs_activity(self, mock_popen, client):
        client.post("/api/pi/shutdown")
        log = web_module.WEB_LOG
        assert log.exists()
        content = log.read_text()
        assert "pi_shutdown" in content

    @patch("salmoncv.web.app.subprocess.Popen")
    def test_pi_reboot_logs_activity(self, mock_popen, client):
        client.post("/api/pi/reboot")
        log = web_module.WEB_LOG
        assert log.exists()
        content = log.read_text()
        assert "pi_reboot" in content


class TestWebLog:
    @patch("salmoncv.web.app.subprocess.run")
    def test_capture_logs_activity(self, mock_run, client, tmp_path):
        client.post("/api/camera/capture", json={})
        log = web_module.WEB_LOG
        assert log.exists()
        content = log.read_text()
        assert "capture" in content
