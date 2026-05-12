from datetime import datetime, time

import pytest

from salmoncv.lights import get_civil_twilight, parse_time


class TestParseTime:
    def test_parses_hhmm(self):
        assert parse_time("14:30") == time(14, 30)

    def test_parses_midnight(self):
        assert parse_time("00:00") == time(0, 0)

    def test_parses_end_of_day(self):
        assert parse_time("23:59") == time(23, 59)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_time("not a time")


class TestGetCivilTwilight:
    def test_returns_dawn_and_dusk(self):
        dawn, dusk = get_civil_twilight(59.748, -161.922, "America/Anchorage")
        assert dawn is not None
        assert dusk is not None

    def test_dawn_before_dusk(self):
        dawn, dusk = get_civil_twilight(
            59.748, -161.922, "America/Anchorage",
            date=datetime(2026, 3, 21).date(),
        )
        assert dawn < dusk

    def test_different_location(self):
        dawn_ak, dusk_ak = get_civil_twilight(
            59.748, -161.922, "America/Anchorage",
            date=datetime(2026, 3, 21).date(),
        )
        dawn_ny, dusk_ny = get_civil_twilight(
            40.7128, -74.0060, "America/New_York",
            date=datetime(2026, 3, 21).date(),
        )
        assert dawn_ak != dawn_ny
