#!/usr/bin/env python3

import argparse
import time
from datetime import datetime, timedelta

from astral import LocationInfo
from astral.sun import sun

# Quinhagak, Alaska
DEFAULT_LAT = 59.748
DEFAULT_LON = -161.922
DEFAULT_TZ = "America/Anchorage"

LIGHTS_PIN = 17


def get_civil_twilight(lat, lon, timezone, date=None):
    loc = LocationInfo(latitude=lat, longitude=lon, timezone=timezone)
    s = sun(loc.observer, date=date or datetime.now().date(), tzinfo=timezone)
    return s["dawn"], s["dusk"]


def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M").time()


def main():
    parser = argparse.ArgumentParser(
        description="Schedule lights based on civil twilight or custom times.",
    )
    parser.add_argument("--lat", type=float, default=DEFAULT_LAT)
    parser.add_argument("--lon", type=float, default=DEFAULT_LON)
    parser.add_argument("--timezone", default=DEFAULT_TZ)
    parser.add_argument(
        "--on-time",
        default=None,
        help="Manual lights-on time (HH:MM, 24h). Overrides sunset.",
    )
    parser.add_argument(
        "--off-time",
        default=None,
        help="Manual lights-off time (HH:MM, 24h). Overrides sunrise.",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=60,
        help="Seconds between schedule checks (default: 60)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print schedule without toggling GPIO",
    )
    args = parser.parse_args()

    from gpiozero import OutputDevice

    relay = None
    if not args.dry_run:
        relay = OutputDevice(LIGHTS_PIN, active_high=False, initial_value=False)

    lights_are_on = False
    last_schedule_date = None

    print(f"Lights scheduler started ({args.lat}, {args.lon})")
    print(f"Check interval: {args.check_interval}s")
    if args.on_time:
        print(f"Manual on-time: {args.on_time}")
    if args.off_time:
        print(f"Manual off-time: {args.off_time}")
    if args.dry_run:
        print("DRY RUN — GPIO will not be toggled")
    print()

    try:
        while True:
            now = datetime.now()
            today = now.date()

            if last_schedule_date != today:
                if args.on_time and args.off_time:
                    on_time = parse_time(args.on_time)
                    off_time = parse_time(args.off_time)
                    print(f"{today} | Manual schedule: ON {on_time} / OFF {off_time}")
                else:
                    try:
                        dawn, dusk = get_civil_twilight(
                            args.lat, args.lon, args.timezone, today,
                        )
                        on_time = dusk.time()
                        off_time = dawn.time()
                        if args.on_time:
                            on_time = parse_time(args.on_time)
                        if args.off_time:
                            off_time = parse_time(args.off_time)
                        print(
                            f"{today} | Civil twilight: "
                            f"dawn {dawn.strftime('%H:%M')} / "
                            f"dusk {dusk.strftime('%H:%M')}"
                        )
                        print(f"{today} | Schedule: ON {on_time} / OFF {off_time}")
                    except ValueError as e:
                        print(
                            f"{today} | No civil twilight (midnight sun or polar night): {e}"
                        )
                        print(f"{today} | Lights will remain {'on' if lights_are_on else 'off'}")
                        last_schedule_date = today
                        time.sleep(args.check_interval)
                        continue

                last_schedule_date = today

            current_time = now.time()

            if off_time < on_time:
                should_be_on = current_time >= on_time or current_time < off_time
            else:
                should_be_on = on_time <= current_time < off_time

            if should_be_on and not lights_are_on:
                print(f"{now.strftime('%H:%M:%S')} | Lights ON")
                if relay:
                    relay.on()
                lights_are_on = True
            elif not should_be_on and lights_are_on:
                print(f"{now.strftime('%H:%M:%S')} | Lights OFF")
                if relay:
                    relay.off()
                lights_are_on = False

            time.sleep(args.check_interval)

    except KeyboardInterrupt:
        print("\nShutting down — turning lights off.")
        if relay:
            relay.off()


if __name__ == "__main__":
    main()
