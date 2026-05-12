# Starlink

SalmonCV controls Starlink power through a relay on GPIO pin 27. The scheduler calculates how long to keep Starlink on based on how many new images need uploading, then powers it down to save energy.

## How It Works

1. Scans the capture directory for new images (not yet in the upload manifest)
2. Estimates total upload time based on file sizes and upload speed
3. Powers on Starlink for the calculated window (plus boot buffer and 10% safety margin)
4. Records uploaded images in the manifest so they aren't re-uploaded
5. Powers off Starlink

## Quick Control (CLI)

Turn Starlink on or off immediately:

```bash
salmoncv-power starlink-on
salmoncv-power starlink-off
```

## Automatic Scheduling

Start the bandwidth-based scheduler:

```bash
salmoncv-starlink
```

### Upload Speed

Default assumes 5 Mbps. Adjust based on your Starlink plan and location:

```bash
salmoncv-starlink --upload-speed 10
```

### Boot Buffer

Starlink takes about 5 minutes to boot and acquire a connection. The default 300-second buffer accounts for this:

```bash
salmoncv-starlink --boot-buffer 300
```

### Fixed Schedule

For a predictable daily window instead of bandwidth calculation:

```bash
salmoncv-starlink --on-time 14:00 --upload-time 30
```

This powers Starlink on at 2:00 PM for exactly 30 minutes.

## Admin Window

A daily admin window (default 12:00 PM, 15 minutes) keeps Starlink on so you can SSH in, push code updates, or check on the system:

```bash
salmoncv-starlink --admin-time 12:00 --admin-duration 15
```

Disable it with:

```bash
salmoncv-starlink --admin-time off
```

## Web Dashboard Controls

The [Power page](web-dashboard.md#power) lets you:

- Toggle Starlink on/off immediately
- Start/stop the Starlink scheduler
- Switch between Auto (bandwidth calculation) and Manual mode
- Set upload speed, admin window time and duration

## Upload Manifest

Uploaded images are tracked in `~/salmoncv/data/upload_manifest.csv` so images aren't counted twice. The manifest records each image filename and the time it was marked as uploaded.

## Starlink Log

All events are logged to `~/salmoncv/data/starlink_log.csv`:

| Column | Description |
|--------|-------------|
| timestamp | When the event occurred |
| event | scheduler_start, window_open, window_close, admin_open, admin_close, no_new_images, scheduler_stop |
| new_images | Number of images to upload |
| estimated_minutes | Calculated window length |
| upload_speed_mbps | Upload speed used for calculation |
| mode | auto or manual |

## Safety Watchdog

The [watchdog](power.md#watchdog) enforces a 3-hour maximum on-duration for Starlink. If the scheduler crashes and leaves Starlink on, the watchdog will force it off.

## CLI Reference

```
salmoncv-starlink [OPTIONS]

  --capture-dir PATH     Image directory to scan
  --upload-speed MBPS    Estimated upload speed (default: 5.0)
  --boot-buffer SEC      Starlink boot time buffer (default: 300)
  --check-interval SEC   Seconds between checks (default: 3600)
  --on-time HH:MM        Fixed daily start time
  --upload-time MINUTES   Fixed window length (skips bandwidth calc)
  --admin-time HH:MM     Admin window time (default: 12:00, 'off' to disable)
  --admin-duration MIN    Admin window length (default: 15)
  --logfile PATH         Log file path
  --manifest PATH        Upload manifest path
  --dry-run              Preview without toggling Starlink
```
