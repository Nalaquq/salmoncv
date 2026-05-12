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
- Wi-Fi hotspot setup script
- systemd auto-start service
- MkDocs documentation site

### Changed

- Switched from `gpiozero` to `pinctrl` for persistent GPIO state
- Rewrote sensor module with CSV logging and `read_sensor()` function
- Camera BME280 reading on each capture
- Deferred Coral/PIL imports for `--no-inference` mode

## 0.1.0 --- 2026-05-11

### Added

- PEP-compliant `src` layout package structure
- CLI entry points: `salmoncv-camera`, `salmoncv-power`, `salmoncv-sensors`, `salmoncv-probe`
- Project documentation and setup guides
