#!/usr/bin/env python3

import argparse
import csv
import math
import time
from datetime import datetime, timedelta
from pathlib import Path

from salmoncv.power import starlink_on, starlink_off

DEFAULT_CAPTURE_DIR = Path.home() / "salmoncv" / "captures"
DEFAULT_LOG = Path.home() / "salmoncv" / "data" / "starlink_log.csv"
DEFAULT_MANIFEST = Path.home() / "salmoncv" / "data" / "upload_manifest.csv"

LOG_FIELDNAMES = [
    "timestamp",
    "event",
    "new_images",
    "estimated_minutes",
    "upload_speed_mbps",
    "mode",
]


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_event(writer, logfile, event, new_images="", est_min="", speed="", mode=""):
    writer.writerow({
        "timestamp": now_str(),
        "event": event,
        "new_images": new_images,
        "estimated_minutes": est_min,
        "upload_speed_mbps": speed,
        "mode": mode,
    })
    logfile.flush()


def load_manifest(manifest_path):
    uploaded = set()
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uploaded.add(row["image_path"])
    return uploaded


def save_manifest(manifest_path, images):
    exists = manifest_path.exists() and manifest_path.stat().st_size > 0
    with open(manifest_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "marked_at"])
        if not exists:
            writer.writeheader()
        marked_at = now_str()
        for img in images:
            writer.writerow({"image_path": img, "marked_at": marked_at})


def get_new_images(capture_dir, manifest_path):
    uploaded = load_manifest(manifest_path)
    all_images = sorted(capture_dir.glob("*.jpg"))
    new = [img for img in all_images if img.name not in uploaded]
    return new


def estimate_window(images, upload_speed_mbps, boot_buffer_sec):
    if not images:
        return 0

    total_bytes = sum(img.stat().st_size for img in images)
    total_mb = total_bytes / (1024 * 1024)
    upload_sec = (total_mb * 8) / upload_speed_mbps
    safety = upload_sec * 0.10
    total = boot_buffer_sec + upload_sec + safety
    return math.ceil(total)


def main():
    parser = argparse.ArgumentParser(
        description="Schedule Starlink power based on upload needs or custom times.",
    )
    parser.add_argument(
        "--capture-dir",
        default=str(DEFAULT_CAPTURE_DIR),
        help=f"Directory to scan for images (default: {DEFAULT_CAPTURE_DIR})",
    )
    parser.add_argument(
        "--upload-speed",
        type=float,
        default=5.0,
        help="Estimated upload speed in Mbps (default: 5.0)",
    )
    parser.add_argument(
        "--boot-buffer",
        type=int,
        default=300,
        help="Seconds to wait for Starlink boot (default: 300)",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=3600,
        help="Seconds between upload checks (default: 3600)",
    )
    parser.add_argument(
        "--on-time",
        default=None,
        help="Fixed daily start time (HH:MM, 24h). Overrides auto scheduling.",
    )
    parser.add_argument(
        "--upload-time",
        type=int,
        default=None,
        help="Fixed upload window in minutes. Skips bandwidth calculation.",
    )
    parser.add_argument(
        "--logfile",
        default=str(DEFAULT_LOG),
        help=f"Path to Starlink log CSV (default: {DEFAULT_LOG})",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help=f"Path to upload manifest CSV (default: {DEFAULT_MANIFEST})",
    )
    parser.add_argument(
        "--admin-time",
        default="12:00",
        help="Daily admin window start time (HH:MM, 24h). Set to 'off' to disable. (default: 12:00)",
    )
    parser.add_argument(
        "--admin-duration",
        type=int,
        default=15,
        help="Admin window duration in minutes (default: 15)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print plan without toggling Starlink",
    )
    args = parser.parse_args()

    capture_dir = Path(args.capture_dir)
    log_path = Path(args.logfile)
    manifest_path = Path(args.manifest)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    write_header = not log_path.exists() or log_path.stat().st_size == 0
    logfile = open(log_path, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(logfile, fieldnames=LOG_FIELDNAMES)
    if write_header:
        writer.writeheader()

    mode = "manual" if args.on_time and args.upload_time else "auto"

    admin_enabled = args.admin_time.lower() != "off"
    admin_ran_today = False

    print(f"Starlink scheduler started")
    print(f"Capture dir: {capture_dir}")
    print(f"Upload speed: {args.upload_speed} Mbps")
    print(f"Boot buffer: {args.boot_buffer}s")
    print(f"Check interval: {args.check_interval}s")
    print(f"Logging to: {log_path}")
    if admin_enabled:
        print(f"Admin window: {args.admin_time} for {args.admin_duration} min daily")
    else:
        print("Admin window: disabled")
    if args.on_time:
        print(f"Fixed start time: {args.on_time}")
    if args.upload_time:
        print(f"Fixed window: {args.upload_time} minutes")
    if args.dry_run:
        print("DRY RUN — Starlink will not be toggled")
    print()

    log_event(writer, logfile, "scheduler_start", mode=mode)

    try:
        last_admin_date = None

        while True:
            now = datetime.now()
            today = now.date()

            # --- Admin window ---
            if admin_enabled and last_admin_date != today:
                admin_target = datetime.strptime(args.admin_time, "%H:%M").time()
                admin_start = datetime.combine(today, admin_target)
                admin_end = admin_start + timedelta(minutes=args.admin_duration)

                if admin_start <= now < admin_end:
                    remaining = (admin_end - now).total_seconds()
                    print(f"{now_str()} | Admin window open ({args.admin_duration} min)")
                    if not args.dry_run:
                        starlink_on()
                    log_event(writer, logfile, "admin_open",
                              est_min=args.admin_duration, mode="admin")

                    time.sleep(remaining)

                    print(f"{now_str()} | Admin window closed")
                    if not args.dry_run:
                        starlink_off()
                    log_event(writer, logfile, "admin_close",
                              est_min=args.admin_duration, mode="admin")
                    last_admin_date = today
                elif now >= admin_end:
                    last_admin_date = today

            # --- Upload window ---
            if args.on_time:
                target = datetime.strptime(args.on_time, "%H:%M").time()
                current = now.time()
                if current < target:
                    wait = (
                        datetime.combine(now.date(), target) - now
                    ).total_seconds()
                    print(f"Waiting until {args.on_time} ({int(wait / 60)} min)...")
                    time.sleep(wait)
                elif current > target:
                    tomorrow = datetime.combine(
                        now.date() + timedelta(days=1), target
                    )
                    wait = (tomorrow - now).total_seconds()
                    print(f"Past today's window. Next: tomorrow {args.on_time} ({int(wait / 3600)}h)...")
                    time.sleep(wait)

            new_images = get_new_images(capture_dir, manifest_path)

            if not new_images:
                print(f"{now_str()} | No new images to upload")
                log_event(writer, logfile, "no_new_images", new_images=0, mode=mode)
                time.sleep(args.check_interval)
                continue

            if args.upload_time:
                window_sec = args.upload_time * 60
                est_min = args.upload_time
            else:
                window_sec = estimate_window(
                    new_images, args.upload_speed, args.boot_buffer,
                )
                est_min = round(window_sec / 60, 1)

            total_mb = sum(img.stat().st_size for img in new_images) / (1024 * 1024)

            print(f"{now_str()} | {len(new_images)} new images ({total_mb:.1f} MB)")
            print(f"{now_str()} | Estimated window: {est_min} min")

            # Power on
            print(f"{now_str()} | Starlink ON")
            if not args.dry_run:
                starlink_on()
            log_event(
                writer, logfile, "window_open",
                new_images=len(new_images),
                est_min=est_min,
                speed=args.upload_speed,
                mode=mode,
            )

            # Wait for upload window
            print(f"{now_str()} | Window open for {est_min} min...")
            time.sleep(window_sec)

            # Power off
            print(f"{now_str()} | Starlink OFF")
            if not args.dry_run:
                starlink_off()
            log_event(
                writer, logfile, "window_close",
                new_images=len(new_images),
                est_min=est_min,
                speed=args.upload_speed,
                mode=mode,
            )

            # Mark images as uploaded
            image_names = [img.name for img in new_images]
            if not args.dry_run:
                save_manifest(manifest_path, image_names)
            print(f"{now_str()} | Marked {len(image_names)} images as uploaded")

            time.sleep(args.check_interval)

    except KeyboardInterrupt:
        print(f"\n{now_str()} | Shutting down — turning Starlink off.")
        if not args.dry_run:
            starlink_off()
        log_event(writer, logfile, "scheduler_stop", mode=mode)
    finally:
        logfile.close()


if __name__ == "__main__":
    main()
