# Changelog

All notable changes to the SalmonCV project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

For the complete changelog with full details, see [CHANGELOG.md](https://github.com/Nalaquq/salmoncv/blob/main/CHANGELOG.md) in the repository.

## Unreleased

### Added

- Flask web dashboard with mobile-first browser UI
    - Dashboard, Camera, Gallery, Sensors, Monitor, Power, Settings pages
    - REST API for all operations
    - Web activity logging
- Camera manual controls (shutter, gain, white balance, exposure)
- Samsung T9 SSD primary storage with SD card fallback
- Lights scheduler (civil twilight at Quinhagak, AK)
- Starlink scheduler (bandwidth-based upload windows with admin window)
- Safety watchdog with relay duration limits
- Wi-Fi hotspot setup script with `--dry-run`, `--safe`, and `--revert` modes
- Networking guide --- all connection methods: hotspot, SSH, Pi Connect, ethernet, HDMI, SD card
- systemd auto-start service
- MkDocs documentation site with GitHub Pages deployment
- GitHub Actions CI --- test suite runs on push/PR across Python 3.9--3.12
- Test suite --- 101 tests covering camera, lights, starlink, storage, watchdog, and web app

### Fixed

- **Camera silently stopped capturing for 12 days** --- the timelapse process resolved its storage drive (T9 vs. SD) once at startup and crashed with no logged error when the T9 was unplugged mid-run, while the dashboard and sensors kept reporting normally the whole time. The camera process now re-checks storage every capture, retries instead of dying on error, and logs failures to `camera_errors.log`/`camera_stderr.log`. The dashboard now shows a **Stalled** badge if the process is alive but hasn't produced a new image in 5+ minutes. See [Storage troubleshooting](storage.md#troubleshooting).
- **Hotspot setup failed on Bookworm** --- script used VLAN netdev and ifupdown, which don't exist on Bookworm. Now uses `iw` to create `ap0` with a persistent systemd service, auto-detects wlan0's channel for simultaneous AP + client.
- **Start Counting broken after boot** --- subprocess calls used bare command names not on PATH when running via systemd. Now uses full venv binary paths.
- **Watchdog midnight sun bug** --- `get_max_night_hours()` could return >25h near midnight sun. Now clamps daylight to valid range.

### Changed

- Switched from `gpiozero` to `pinctrl` for persistent GPIO state
- Rewrote sensor module with CSV logging and `read_sensor()` function
- Camera BME280 reading on each capture
- Deferred Coral/PIL imports for `--no-inference` mode
- Hardware-only dependencies moved to optional `[pi]` extra --- install with `pip install -e ".[pi]"` on the Pi

## 0.1.0 --- 2026-05-11

### Added

- PEP-compliant `src` layout package structure
- CLI entry points: `salmoncv-camera`, `salmoncv-power`, `salmoncv-sensors`, `salmoncv-probe`
- Project documentation and setup guides
