# Changelog

All notable changes to the SalmonCV project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- `lights.py`: new lights scheduler module — defaults to civil twilight at Quinhagak, AK (59.75°N, 161.92°W), supports manual `--on-time`/`--off-time` overrides, `--dry-run` mode, handles midnight sun and polar night
- `salmoncv-lights` CLI entry point
- `astral` dependency for solar position calculations
- `camera.py`: `--no-inference` flag to capture images without Coral TPU
- `camera.py`: `capture_log.csv` written on every run with timestamp, image path, file size, resolution, and BME280 environmental data (temperature, humidity, pressure)

### Changed
- `power.py`: switched from `gpiozero` to `pinctrl` so GPIO state persists after process exit (fixes relay resetting immediately)
- `power.py`: fixed relay polarity — relay is active-high (drive high = ON, drive low = OFF)
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
