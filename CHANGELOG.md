# Changelog

All notable changes to the SalmonCV project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- `docs/screenshots/` directory with naming convention for app screenshots
- App screenshots embedded across docs_site pages (web-dashboard, camera, sensors, power, lights, starlink, storage, getting-started, index), docs/usage-guide.md, and README.md

### Changed
- Added gitignored `context/` directory for extra project context files; moved `prompt.txt` (running chat log) there and removed it from git tracking
- Reworked screenshot integration for readability: README now opens with a dashboard hero image and shows a 2x2 grid of Camera/Gallery/Monitor/Power in the Web Dashboard section; usage-guide's Dashboard pages section rewritten from a table plus 8-image dump into per-page subsections, each with its own description and screenshot (including the previously missing Pi Power page); moved screenshots in lights, starlink, and power docs_site pages below their bullet lists so they no longer interrupt sentences; added the Settings screenshot to storage.md's Checking Storage section
- Compressed `salmoncv_gallery.png` from 2.2 MB to 296 KB (resized 3777px → 1920px, quantized to 256 colors) in both `docs/screenshots/` and `docs_site/img/`
- Live Focus stream on the Camera page — starts a low-res (640x480 @ 15fps) MJPEG feed from `rpicam-vid` so you can manually adjust lens focus from the browser

### Fixed
- **Camera silently stopped capturing for 12 days (2026-07-30 to 2026-08-11) and gave no indication anything was wrong**: the timelapse process resolved its output directory (SD card vs. Samsung T9) once at startup and never rechecked it. When the T9 drive was unplugged mid-run, the next write raised an uncaught exception that killed the process — and since it was launched with `stderr=DEVNULL`, the crash left no trace anywhere. The web dashboard and sensor logging are separate processes and kept running/reporting normally the whole time, so the system looked healthy on every remote check even though nothing was being captured.
  - `salmoncv-camera` now re-resolves the storage target every loop iteration instead of once at startup, so unplugging/replugging the T9 is picked up live instead of crashing the process.
  - The capture loop now catches per-iteration exceptions, logs them to `data/camera_errors.log`, and keeps running instead of exiting.
  - `/api/camera/start` and `/api/system/start` no longer pin `--outdir` at launch (that's what froze the storage target), and now log the subprocess's stderr to `data/camera_stderr.log` instead of discarding it.
  - `/api/camera/status` now reports `stale: true` when the process is alive but hasn't written a new image in 5+ minutes, and the Camera and Dashboard pages show a "Stalled" badge instead of a healthy-looking "Running" badge in that case.
- Broken thumbnails in the Gallery caused by partially written capture files. Captures (CLI time-lapse and web Quick Capture) now write to a `.tmp` name and rename to `.jpg` when complete, so the gallery never lists an in-progress file; interrupted captures no longer leave corrupt `.jpg` files behind. The thumbnail endpoint now serves an "unreadable image" SVG placeholder for undecodable files (instead of the corrupt original) so they can still be selected and deleted, and no longer caches partial thumbnails. Added 5 tests (118 total).
- Swap lights and Starlink relay GPIO pins (17 ↔ 27) to match physical wiring

### Added
- Networking guide (`docs_site/networking.md`) — comprehensive page covering all connection methods: SalmonCV hotspot, SSH, Raspberry Pi Connect, ethernet direct, HDMI + keyboard, SD card Wi-Fi editing via WSL. Includes Wi-Fi management with nmcli, SSH troubleshooting, and quick reference
- Wi-Fi / Network troubleshooting section in `docs_site/troubleshooting.md` with escalation ladder linking to the networking guide
- Raspberry Pi Connect setup instructions in `docs_site/pi-setup.md`
- Cross-references to networking guide from hotspot, getting-started, troubleshooting, and usage-guide docs
- MkDocs documentation site with Material theme — 18 pages covering every component, setup guides, troubleshooting, and reference docs
- GitHub Actions workflow (`.github/workflows/docs.yml`) for automatic deployment to GitHub Pages on push to main
- GitHub Actions test workflow (`.github/workflows/tests.yml`) — runs 87 tests on push/PR across Python 3.9–3.12
- `scripts/revert_hotspot.sh` — reverts all hotspot changes, restoring default networking
- `setup_hotspot.sh` rewritten with `--dry-run`, `--safe`, and `--revert` flags for safe remote setup over SSH

- Pi Power page (`/pi-power`) — shut down or reboot the Raspberry Pi from the dashboard with confirmation dialogs. Shows hostname, boot time, uptime, and CPU temperature.

### Fixed
- **Hotspot setup script failed on Bookworm**: `setup_hotspot.sh` used VLAN netdev and `/etc/network/interfaces.d/` to create `ap0`, neither of which exist on Raspberry Pi OS Bookworm with NetworkManager. Script now creates `ap0` using `iw dev wlan0 interface add ap0 type __ap` with a persistent systemd service (`ap0.service`). Also auto-detects wlan0's channel and band so the hotspot shares the same radio channel (required for simultaneous AP + client on Pi 5). Config file directories are created if missing. Hotspot activates immediately without requiring a reboot.
- **Hotspot revert script didn't clean up ap0.service**: `revert_hotspot.sh` now removes the `ap0.service` systemd unit and safety timer files.
- **Start Counting broken after boot**: subprocess calls used bare command names (`salmoncv-camera`, etc.) which weren't on PATH when Flask ran via systemd. Now uses full venv binary paths resolved at runtime via `sys.executable`.
- **Dashboard showed both relays as "on" when only one was energized**: `/api/system/running` only checked scheduler PID files, not actual relay state. Now returns separate `lights_relay` and `starlink_relay` fields that check the GPIO state files. Dashboard distinguishes "Sched" (scheduler running) from relay "ON/OFF".
- **Dashboard showed relays as "on" after reboot when they were physically off**: Relay state files (`.lights_on_since`, `.starlink_on_since`) persisted across reboots but GPIO pins reset to LOW on power cycle. Flask app now clears stale state files on startup.
- **"Stop All" didn't turn off lights/Starlink relays**: The stop endpoint only killed scheduler processes but left relays energized. Now also calls `lights_off()` and `starlink_off()` if the relays are on.

### Changed
- Hardware-only dependencies (pycoral, tflite-runtime, RPi.bme280, smbus2) moved to `[project.optional-dependencies.pi]`; install with `pip install -e ".[pi]"` on the Pi
- `docs_site/` directory with all documentation source files
- `mkdocs.yml` configuration with Material theme, dark mode toggle, search, and code copy

- Flask web dashboard (`src/salmoncv/web/`) — mobile-first browser UI accessible from phone or tablet over Wi-Fi
  - Dashboard page: at-a-glance status for camera, sensors, lights, Starlink, and system
  - Camera page: single capture with live preview, time-lapse start/stop with configurable interval and resolution
  - Gallery page: paginated thumbnail grid with full-size lightbox viewer
  - Sensors page: live BME280 readings (auto-refresh every 5s), recent history table, CSV download
  - Power page: toggle lights and Starlink on/off, view relay state and elapsed time, light schedule (dawn/dusk), Starlink upload queue
  - Settings page: hostname, uptime, CPU temp, disk usage with progress bar, log file downloads
- `salmoncv-web` CLI entry point (default port 80, `--host`, `--port`, `--debug`)
- `flask` dependency in pyproject.toml
- REST API: `/api/camera/*`, `/api/gallery/*`, `/api/sensors/*`, `/api/power/*`, `/api/schedule/*`, `/api/system`, `/api/logs/*`
- `scripts/setup_hotspot.sh` — one-time Wi-Fi hotspot setup (SSID: SalmonCV, IP: 192.168.4.1)
- `docs/hotspot-setup.md` — non-expert hotspot setup and troubleshooting guide
- Web activity log (`~/salmoncv/data/web_log.csv`) — records every action taken through the dashboard: captures, time-lapse start/stop, power toggles, with timestamp and client IP
- Camera manual controls: shutter speed, gain (ISO), white balance, and exposure compensation — available in both CLI (`--shutter`, `--gain`, `--awb`, `--ev`) and web dashboard (auto/manual mode toggle)
- Samsung T9 external drive as primary storage with automatic SD card fallback — `storage.py` module checks T9 availability (mounted, writable, >100MB free) on every capture; falls back to SD card if T9 is missing, full, or corrupted
- Settings page shows both Samsung T9 and SD Card storage with usage bars
- Dashboard storage card with drive selector: Auto (T9 first), Samsung T9 only, or SD Card only — preference persists in `~/salmoncv/data/storage_config.json`
- `/api/storage` and `/api/storage/set` endpoints for viewing and changing storage mode
- Lights and Starlink scheduler controls on Power page — start/stop schedulers, switch between auto (civil twilight / bandwidth calc) and manual mode with custom times, all from the browser
- Scheduler configs saved to JSON files in `~/salmoncv/data/` so settings persist across restarts
- New API endpoints: `/api/scheduler/lights/config|start|stop`, `/api/scheduler/starlink/config|start|stop`
- **Start Counting** master button on dashboard — launches camera, sensors, lights scheduler, and Starlink scheduler in one click with configurable capture and sensor intervals
- **Stop All** button to shut down all services at once
- `/api/system/start`, `/api/system/stop`, `/api/system/running` endpoints for full system control
- Live service status indicators on dashboard showing which services are running
- **Monitor** page — estimated power draw table with color-coded bar (Pi, camera, lights, Starlink), case temperature/humidity health check, and interactive line charts for temperature, humidity, and pressure history with configurable data range
- `/api/sensors/chart` endpoint returning arrays for chart rendering, `/api/power/draw` endpoint with estimated wattage per component
- Gallery select mode: tap Select to enter selection mode, select individual images or Select All, then Delete to remove them. Confirmation dialog prevents accidental deletion. Thumbnails also cleaned up on delete.
- `scripts/install_service.sh` — one-time setup to run `salmoncv-web` as a systemd service that starts automatically on boot
- `lights.py`: new lights scheduler module — defaults to civil twilight at Quinhagak, AK (59.75°N, 161.92°W), supports manual `--on-time`/`--off-time` overrides, `--dry-run` mode, handles midnight sun and polar night
- `salmoncv-lights` CLI entry point
- `astral` dependency for solar position calculations
- `camera.py`: `--no-inference` flag to capture images without Coral TPU
- `camera.py`: `capture_log.csv` written on every run with timestamp, image path, file size, resolution, and BME280 environmental data (temperature, humidity, pressure)

### Changed
- `power.py`: switched from `gpiozero` to `pinctrl` so GPIO state persists after process exit (fixes relay resetting immediately)
- `power.py`: fixed relay polarity — relay is active-high (drive high = ON, drive low = OFF)
- `starlink.py`: new Starlink power scheduler — calculates upload window from new image count and estimated bandwidth (5 Mbps default), tracks uploaded images via manifest, supports `--on-time`/`--upload-time` manual overrides, CSV event logging, `--dry-run` mode
- `starlink.py`: daily admin window (default 12:00 PM, 15 min) for SSH access and pushing updates; disable with `--admin-time off`
- `watchdog.py`: safety watchdog that enforces max on-durations — lights max = night duration + 1h buffer (calculated daily from civil twilight), Starlink max = 3 hours. Forces relays off and logs to `~/salmoncv/data/watchdog_log.csv`
- `salmoncv-watchdog` CLI entry point
- `power.py`: state files (`.lights_on_since`, `.starlink_on_since`) written/cleared on every relay toggle for watchdog tracking
- `salmoncv-starlink` CLI entry point
- `lights.py`: CSV log at `~/salmoncv/data/lights_log.csv` tracking every on/off event, schedule changes, scheduler start/stop, and midnight sun events
- Added `README.md` with project overview, quick start, command reference, and project structure
- Added `docs/usage-guide.md` with detailed instructions for every command, troubleshooting, and quick reference card — written for non-expert users
- `lights.py`: now reuses `lights_on()`/`lights_off()` from `power.py` instead of managing GPIO directly
- `camera.py`: Coral/PIL imports deferred to only load when inference is enabled; `--model` no longer required with `--no-inference`
- `camera.py`: BME280 sensor reading attempted automatically each capture; columns left blank if sensor unavailable
- Removed `gpiozero` from project dependencies (`pinctrl` is built into Pi 5)
- `sensors.py`: rewrote to log BME280 data to CSV with timestamps, configurable interval and log file path via CLI args (`--logfile`, `--interval`), extracted `read_sensor()` function for reuse
- `sensors.py`: default log path set to `~/salmoncv/data/sensor_log.csv`
- `.gitignore`: added `data/` directory

---

## [0.1.0] - 2026-05-11

### Added
- PEP-compliant `src` layout package structure with `pyproject.toml` (PEP 621, hatchling backend)
- `src/salmoncv/__init__.py` with version 0.1.0
- CLI entry points: `salmoncv-camera`, `salmoncv-power`, `salmoncv-sensors`, `salmoncv-probe`
- `tests/` directory placeholder
- `docs/` directory with all project documentation
- `scripts/` directory for shell utilities

### Changed
- `coral_timelapse_cli_camera.py` renamed to `src/salmoncv/camera.py`
- `control_power.py` renamed to `src/salmoncv/power.py`
- `temp.py` renamed to `src/salmoncv/sensors.py` (wrapped in `main()` function)
- `gpio_probe.py` moved to `src/salmoncv/gpio_probe.py`
- `snapshot.sh` moved to `scripts/`
- Setup docs moved to `docs/`
- `.gitignore` updated with `dist/`, `build/`, `*.egg-info/`

### Removed
- `gpio_probe.py.save` (stale backup file)
