import csv
from pathlib import Path

import pytest

from salmoncv.starlink import (
    estimate_window,
    get_new_images,
    load_manifest,
    save_manifest,
)


@pytest.fixture
def captures(tmp_path):
    d = tmp_path / "captures"
    d.mkdir()
    for i in range(3):
        f = d / f"img_{i}.jpg"
        f.write_bytes(b"\x00" * 1024 * 1024)  # 1 MB each
    return d


@pytest.fixture
def manifest(tmp_path):
    return tmp_path / "manifest.csv"


class TestLoadManifest:
    def test_empty_when_no_file(self, manifest):
        assert load_manifest(manifest) == set()

    def test_reads_uploaded_names(self, manifest):
        manifest.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["image_path", "marked_at"])
            w.writeheader()
            w.writerow({"image_path": "img_0.jpg", "marked_at": "2026-05-11"})
        result = load_manifest(manifest)
        assert "img_0.jpg" in result


class TestSaveManifest:
    def test_creates_file(self, manifest):
        save_manifest(manifest, ["a.jpg", "b.jpg"])
        assert manifest.exists()
        content = manifest.read_text()
        assert "a.jpg" in content
        assert "b.jpg" in content

    def test_appends_to_existing(self, manifest):
        save_manifest(manifest, ["a.jpg"])
        save_manifest(manifest, ["b.jpg"])
        uploaded = load_manifest(manifest)
        assert uploaded == {"a.jpg", "b.jpg"}


class TestGetNewImages:
    def test_all_new_when_no_manifest(self, captures, manifest):
        new = get_new_images(captures, manifest)
        assert len(new) == 3

    def test_excludes_uploaded(self, captures, manifest):
        save_manifest(manifest, ["img_0.jpg"])
        new = get_new_images(captures, manifest)
        names = [img.name for img in new]
        assert "img_0.jpg" not in names
        assert len(new) == 2

    def test_empty_when_all_uploaded(self, captures, manifest):
        save_manifest(manifest, ["img_0.jpg", "img_1.jpg", "img_2.jpg"])
        new = get_new_images(captures, manifest)
        assert len(new) == 0


class TestEstimateWindow:
    def test_zero_for_no_images(self):
        assert estimate_window([], 5.0, 300) == 0

    def test_positive_for_images(self, captures):
        images = sorted(captures.glob("*.jpg"))
        window = estimate_window(images, 5.0, 300)
        assert window > 0

    def test_includes_boot_buffer(self, captures):
        images = sorted(captures.glob("*.jpg"))
        short_boot = estimate_window(images, 5.0, 0)
        long_boot = estimate_window(images, 5.0, 600)
        assert long_boot > short_boot

    def test_slower_speed_longer_window(self, captures):
        images = sorted(captures.glob("*.jpg"))
        fast = estimate_window(images, 10.0, 300)
        slow = estimate_window(images, 1.0, 300)
        assert slow > fast
