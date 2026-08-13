import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from salmoncv import camera, storage
from salmoncv.camera import capture_image, load_labels


class TestLoadLabels:
    def test_loads_labels(self, tmp_path):
        labels_file = tmp_path / "labels.txt"
        labels_file.write_text("0 salmon\n1 trout\n2 steelhead\n")
        result = load_labels(str(labels_file))
        assert result == {0: "salmon", 1: "trout", 2: "steelhead"}

    def test_returns_empty_for_none(self):
        assert load_labels(None) == {}

    def test_skips_malformed_lines(self, tmp_path):
        labels_file = tmp_path / "labels.txt"
        labels_file.write_text("0 salmon\nbadline\n1 trout\n")
        result = load_labels(str(labels_file))
        assert result == {0: "salmon", 1: "trout"}


class TestCaptureImage:
    @patch("salmoncv.camera.subprocess.run")
    def test_calls_rpicam_with_defaults(self, mock_run, tmp_path):
        img = tmp_path / "test.jpg"
        capture_image("rpicam-still", img, 1920, 1080)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "rpicam-still"
        assert "-o" in cmd
        assert "--width" in cmd
        assert "--awb" in cmd
        assert "--shutter" not in cmd
        assert "--gain" not in cmd

    @patch("salmoncv.camera.subprocess.run")
    def test_includes_shutter_when_set(self, mock_run, tmp_path):
        img = tmp_path / "test.jpg"
        capture_image("rpicam-still", img, 1920, 1080, shutter=5000)
        cmd = mock_run.call_args[0][0]
        assert "--shutter" in cmd
        assert "5000" in cmd

    @patch("salmoncv.camera.subprocess.run")
    def test_includes_gain_when_set(self, mock_run, tmp_path):
        img = tmp_path / "test.jpg"
        capture_image("rpicam-still", img, 1920, 1080, gain=4.0)
        cmd = mock_run.call_args[0][0]
        assert "--gain" in cmd

    @patch("salmoncv.camera.subprocess.run")
    def test_includes_ev_when_nonzero(self, mock_run, tmp_path):
        img = tmp_path / "test.jpg"
        capture_image("rpicam-still", img, 1920, 1080, ev=-2)
        cmd = mock_run.call_args[0][0]
        assert "--ev" in cmd
        assert "-2" in cmd

    @patch("salmoncv.camera.subprocess.run")
    def test_sets_awb(self, mock_run, tmp_path):
        img = tmp_path / "test.jpg"
        capture_image("rpicam-still", img, 1920, 1080, awb="daylight")
        cmd = mock_run.call_args[0][0]
        idx = cmd.index("--awb")
        assert cmd[idx + 1] == "daylight"

    @patch("salmoncv.camera.subprocess.run")
    def test_writes_to_tmp_then_renames(self, mock_run, tmp_path):
        img = tmp_path / "test.jpg"

        def fake_capture(cmd, **kwargs):
            out = Path(cmd[cmd.index("-o") + 1])
            out.write_bytes(b"\xff\xd8jpegdata")

        mock_run.side_effect = fake_capture
        capture_image("rpicam-still", img, 1920, 1080)
        cmd = mock_run.call_args[0][0]
        assert cmd[cmd.index("-o") + 1] == str(img) + ".tmp"
        assert img.exists()
        assert not (tmp_path / "test.jpg.tmp").exists()

    @patch("salmoncv.camera.subprocess.run")
    def test_cleans_up_tmp_on_failure(self, mock_run, tmp_path):
        import subprocess

        img = tmp_path / "test.jpg"

        def fail_capture(cmd, **kwargs):
            out = Path(cmd[cmd.index("-o") + 1])
            out.write_bytes(b"\xff\xd8partial")
            raise subprocess.CalledProcessError(1, cmd)

        mock_run.side_effect = fail_capture
        with pytest.raises(subprocess.CalledProcessError):
            capture_image("rpicam-still", img, 1920, 1080)
        assert not img.exists()
        assert not (tmp_path / "test.jpg.tmp").exists()


EMPTY_ENV = {"temperature_c": "", "humidity": "", "pressure_hpa": ""}


def _run_main_until_stopped(monkeypatch, argv, capture_side_effect, max_iterations):
    """Run camera.main() to completion by having time.sleep raise
    KeyboardInterrupt after max_iterations loop passes, the same way a
    real stop signal ends the loop cleanly.
    """
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(camera, "capture_image", MagicMock(side_effect=capture_side_effect))
    monkeypatch.setattr(camera, "try_read_sensor", lambda: dict(EMPTY_ENV))

    calls = {"n": 0}

    def fake_sleep(_seconds):
        calls["n"] += 1
        if calls["n"] >= max_iterations:
            raise KeyboardInterrupt

    monkeypatch.setattr(camera.time, "sleep", fake_sleep)
    camera.main()


class TestOpenCaptureLogs:
    def test_writes_header_once(self, tmp_path):
        capture_log, capture_writer, inference_log, inference_writer = (
            camera.open_capture_logs(tmp_path, run_inference=False)
        )
        capture_log.close()
        assert inference_log is None
        content = (tmp_path / "capture_log.csv").read_text()
        assert content.count("timestamp,image_path") == 1

    def test_appending_does_not_duplicate_header(self, tmp_path):
        first, *_ = camera.open_capture_logs(tmp_path, run_inference=False)
        first.close()
        second, *_ = camera.open_capture_logs(tmp_path, run_inference=False)
        second.close()
        content = (tmp_path / "capture_log.csv").read_text()
        assert content.count("timestamp,image_path") == 1


class TestLogCameraError:
    def test_appends_timestamped_line(self, tmp_path, monkeypatch):
        monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
        camera.log_camera_error("camera hardware gone")
        log_path = tmp_path / "data" / "camera_errors.log"
        assert log_path.exists()
        assert "camera hardware gone" in log_path.read_text()


class TestMainSurvivesCaptureFailures:
    """Regression tests for the 2026-07-30 outage: an uncaught exception in
    the capture loop used to kill the whole process silently. The loop must
    now log the failure and keep running instead of exiting.
    """

    def test_keeps_looping_after_repeated_exceptions(self, tmp_path, monkeypatch, capsys):
        outdir = tmp_path / "captures"

        def always_fail(*args, **kwargs):
            raise RuntimeError("camera hardware gone")

        argv = [
            "salmoncv-camera", "--no-inference",
            "--outdir", str(outdir), "--interval", "0",
        ]
        _run_main_until_stopped(monkeypatch, argv, always_fail, max_iterations=3)

        out = capsys.readouterr().out
        assert out.count("capture iteration failed") == 3

    def test_logs_each_failure_to_camera_errors_log(self, tmp_path, monkeypatch):
        outdir = tmp_path / "captures"
        monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")

        def always_fail(*args, **kwargs):
            raise RuntimeError("camera hardware gone")

        argv = [
            "salmoncv-camera", "--no-inference",
            "--outdir", str(outdir), "--interval", "0",
        ]
        _run_main_until_stopped(monkeypatch, argv, always_fail, max_iterations=3)

        error_log = (tmp_path / "data" / "camera_errors.log").read_text()
        assert error_log.count("camera hardware gone") == 3

    def test_recovers_once_capture_succeeds_again(self, tmp_path, monkeypatch):
        outdir = tmp_path / "captures"
        calls = {"n": 0}

        def fail_then_succeed(command, image_path, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("transient failure")
            Path(image_path).write_bytes(b"\xff\xd8\xff")

        argv = [
            "salmoncv-camera", "--no-inference",
            "--outdir", str(outdir), "--interval", "0",
        ]
        _run_main_until_stopped(monkeypatch, argv, fail_then_succeed, max_iterations=3)

        assert list(outdir.glob("*.jpg"))


class TestMainReResolvesStorage:
    """Regression test for the actual 2026-07-30 crash: the capture
    destination (SD vs T9) used to be resolved once at startup, so the T9
    drive disappearing mid-run crashed the process on its next write. The
    loop must now re-resolve storage every iteration and switch over
    cleanly instead of dying.
    """

    def test_switches_output_dir_when_storage_target_changes(self, tmp_path, monkeypatch):
        dir_a = tmp_path / "t9"
        dir_b = tmp_path / "sd"
        dir_a.mkdir()
        dir_b.mkdir()

        targets = iter([dir_a, dir_a, dir_b, dir_b, dir_b])
        monkeypatch.setattr(storage, "get_capture_dir", lambda: next(targets))
        monkeypatch.setattr(storage, "get_storage_info", lambda: {"drive": "Test"})

        def fake_capture(command, image_path, *args, **kwargs):
            Path(image_path).write_bytes(b"\xff\xd8\xff")

        argv = ["salmoncv-camera", "--no-inference", "--interval", "0"]
        _run_main_until_stopped(monkeypatch, argv, fake_capture, max_iterations=3)

        assert list(dir_a.glob("*.jpg")), "expected an image while T9 was still resolving"
        assert list(dir_b.glob("*.jpg")), "expected capture to continue on SD after the switch"
