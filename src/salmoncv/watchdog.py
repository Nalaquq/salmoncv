#!/usr/bin/env python3

import csv
from datetime import datetime
from pathlib import Path

from astral import LocationInfo
from astral.sun import sun

from salmoncv.power import (
    lights_off, starlink_off,
    LIGHTS_STATE, STARLINK_STATE,
)

DEFAULT_LAT = 59.748
DEFAULT_LON = -161.922
DEFAULT_TZ = "America/Anchorage"

STARLINK_MAX_HOURS = 3

LOG_PATH = Path.home() / "salmoncv" / "data" / "watchdog_log.csv"
LOG_FIELDNAMES = ["timestamp", "event", "relay", "on_duration_min"]


def log_event(event, relay, duration_min):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0

    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            "relay": relay,
            "on_duration_min": round(duration_min, 1),
        })


def get_max_night_hours():
    try:
        loc = LocationInfo(latitude=DEFAULT_LAT, longitude=DEFAULT_LON,
                           timezone=DEFAULT_TZ)
        today = datetime.now().date()
        s = sun(loc.observer, date=today, tzinfo=DEFAULT_TZ)
        dawn = s["dawn"]
        dusk = s["dusk"]
        daylight_hours = max(0, (dusk - dawn).total_seconds() / 3600)
        night_hours = 24 - min(daylight_hours, 24)
        return night_hours + 1  # 1 hour safety buffer
    except ValueError:
        # Midnight sun or polar night — use 24h as safe max
        return 24


def check_relay(state_file, relay_name, max_hours):
    if not state_file.exists():
        return

    try:
        on_since = datetime.fromisoformat(state_file.read_text().strip())
    except (ValueError, OSError):
        return

    elapsed = datetime.now() - on_since
    elapsed_min = elapsed.total_seconds() / 60
    elapsed_hours = elapsed.total_seconds() / 3600

    if elapsed_hours >= max_hours:
        print(
            f"WATCHDOG: {relay_name} has been on for {elapsed_min:.0f} min "
            f"(max {max_hours * 60:.0f} min). Forcing OFF."
        )
        if relay_name == "lights":
            lights_off()
        else:
            starlink_off()
        log_event("forced_off", relay_name, elapsed_min)
    else:
        remaining = max_hours * 60 - elapsed_min
        print(f"WATCHDOG: {relay_name} on for {elapsed_min:.0f} min ({remaining:.0f} min remaining)")


def main():
    print(f"Watchdog check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    max_night = get_max_night_hours()
    print(f"Lights max: {max_night:.1f}h (night duration + 1h buffer)")
    print(f"Starlink max: {STARLINK_MAX_HOURS}h")

    check_relay(LIGHTS_STATE, "lights", max_night)
    check_relay(STARLINK_STATE, "starlink", STARLINK_MAX_HOURS)

    print("Watchdog check complete.")


if __name__ == "__main__":
    main()
