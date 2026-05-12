from datetime import datetime

import pytest

from salmoncv.watchdog import get_max_night_hours


class TestGetMaxNightHours:
    def test_returns_positive_hours(self):
        result = get_max_night_hours()
        assert result > 0

    def test_includes_buffer(self):
        result = get_max_night_hours()
        assert result >= 1  # at minimum the 1-hour buffer

    def test_reasonable_range(self):
        result = get_max_night_hours()
        assert 1 <= result <= 25  # max 24h night + 1h buffer
