import json
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def tmp_data(tmp_path):
    """Provide a temporary data directory with salmoncv layout."""
    data = tmp_path / "data"
    data.mkdir()
    captures = tmp_path / "captures"
    captures.mkdir()
    return tmp_path


@pytest.fixture
def sample_images(tmp_path):
    """Create fake JPEG files in a captures directory."""
    captures = tmp_path / "captures"
    captures.mkdir(exist_ok=True)
    files = []
    for i in range(5):
        f = captures / f"capture_20260511_{100000 + i}.jpg"
        f.write_bytes(b"\xff\xd8\xff" + b"\x00" * (1024 * (i + 1)))
        files.append(f)
    return captures, files
