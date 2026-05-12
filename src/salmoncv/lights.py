#!/usr/bin/env python3

import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

from astral import LocationInfo
from astral.sun import sun

from salmoncv.power import lights_on, lights_off

# Quinhagak, Alaska
DEFAULT_LAT = 59.748
DEFAULT_LON = -161.922
DEFAULT_TZ = "America/Anchorage"

LOG_FIELDNAMES = [
    "timestamp",
    "event",
    "scheduled_on",
    "scheduled_off",
    "mode",
]


def get_civil_twilight(lat, lon, timezone, date=None):
    loc = LocationInfo(latitude=lat, longitude=lon, timezone=timezone)
    s = sun(loc.observer, date=date or datetime.now().date(), tzinfo=timezone)
    return s["dawn"], s["dusk"]


def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M").time()


def log_event(writer, logfile, event, on_time, off_time, mode):
    writer.writerow({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "scheduled_on": str(on_time),
        "scheduled_off": str(off_time),
        "mode": mode,
    })
    logfile.flush()


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
    default_log = Path.home() / "salmoncv" / "data" / "lights_log.csv"
    parser.add_argument(
        "--logfile",
        default=str(default_log),
        help=f"Path to the lights log CSV (default: {default_log})",
    )
    args = parser.parse_args()

    log_path = Path(args.logfile)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    write_header = not log_path.exists() or log_path.stat().st_size == 0
    logfile = open(log_path, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(logfile, fieldnames=LOG_FIELDNAMES)
    if write_header:
        writer.writeheader()

    lights_are_on = False
    last_schedule_date = None
    on_time = None
    off_time = None
    mode = "auto"

    print(f"Lights scheduler started ({args.lat}, {args.lon})")
    print(f"Logging to {log_path}")
    print(f"Check interval: {args.check_interval}s")
    if args.on_time:
        print(f"Manual on-time: {args.on_time}")
    if args.off_time:
        print(f"Manual off-time: {args.off_time}")
    if args.dry_run:
        print("DRY RUN — GPIO will not be toggled")
    print()

    log_event(writer, logfile, "scheduler_start", "", "", "")

    try:
        while True:
            now = datetime.now()
            today = now.date()

            if last_schedule_date != today:
                if args.on_time and args.off_time:
                    on_time = parse_time(args.on_time)
                    off_time = parse_time(args.off_time)
                    mode = "manual"
                    print(f"{today} | Manual schedule: ON {on_time} / OFF {off_time}")
                    log_event(writer, logfile, "schedule_set", on_time, off_time, mode)
                else:
                    try:
                        dawn, dusk = get_civil_twilight(
                            args.lat, args.lon, args.timezone, today,
                        )
                        on_time = dusk.time()
                        off_time = dawn.time()
                        mode = "auto"
                        if args.on_time:
                            on_time = parse_time(args.on_time)
                            mode = "mixed"
                        if args.off_time:
                            off_time = parse_time(args.off_time)
                            mode = "mixed"
                        print(
                            f"{today} | Civil twilight: "
                            f"dawn {dawn.strftime('%H:%M')} / "
                            f"dusk {dusk.strftime('%H:%M')}"
                        )
                        print(f"{today} | Schedule: ON {on_time} / OFF {off_time}")
                        log_event(writer, logfile, "schedule_set", on_time, off_time, mode)
                    except ValueError as e:
                        print(
                            f"{today} | No civil twilight (midnight sun or polar night): {e}"
                        )
                        print(f"{today} | Lights will remain {'on' if lights_are_on else 'off'}")
                        log_event(writer, logfile, "no_twilight", "", "", "auto")
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
                if not args.dry_run:
                    lights_on()
                log_event(writer, logfile, "lights_on", on_time, off_time, mode)
                lights_are_on = True
            elif not should_be_on and lights_are_on:
                print(f"{now.strftime('%H:%M:%S')} | Lights OFF")
                if not args.dry_run:
                    lights_off()
                log_event(writer, logfile, "lights_off", on_time, off_time, mode)
                lights_are_on = False

            time.sleep(args.check_interval)

    except KeyboardInterrupt:
        print("\nShutting down — turning lights off.")
        if not args.dry_run:
            lights_off()
        log_event(writer, logfile, "scheduler_stop", on_time or "", off_time or "", mode)
    finally:
        logfile.close()


if __name__ == "__main__":
    main()
