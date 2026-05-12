from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

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
