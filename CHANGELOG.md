# Changelog

All notable changes to the SalmonCV project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
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
