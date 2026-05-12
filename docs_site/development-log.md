# Development Log

!!! note
    This is a summary of the full development log. The complete chronological log is at `docs/salmoncv_chronological_development_log.md` in the repository.

## Timeline

### Phase 1: Hardware Platform

- Selected Raspberry Pi 5 as the computing platform
- Chose Google Coral USB Accelerator for edge inference
- Designed power system: 100W solar panel, 30A charge controller, 12V marine battery
- Built waterproof camera enclosure with 38mm viewing port and polarizing filter

### Phase 2: Core Software

- Created PEP-compliant Python package structure (`src/salmoncv/`)
- Built camera module with `rpicam-still` integration and capture logging
- Built sensor module for BME280 environmental data logging
- Built power module using `pinctrl` for GPIO relay control
- Added lights scheduler with civil twilight calculation via `astral`
- Added Starlink scheduler with bandwidth-based upload windows
- Added safety watchdog with duration limits

### Phase 3: Web Dashboard

- Built Flask web application with mobile-first design
- Dashboard page: master Start/Stop controls, service status badges
- Camera page: single capture, time-lapse, manual exposure controls
- Gallery page: thumbnails, lightbox viewer, select and delete
- Sensors page: live readings, history table, CSV download
- Monitor page: power draw estimates, environmental charts
- Power page: relay toggles, lights/Starlink scheduler controls
- Settings page: system info, storage details, log downloads
- Added Samsung T9 SSD storage module with automatic SD card fallback
- Added web activity logging to CSV
- Added systemd auto-start service

### Phase 4: Documentation

- Set up MkDocs with Material theme
- Created documentation site hosted on GitHub Pages
- Wrote guides for every component: camera, lights, Starlink, sensors, power, storage
- Added troubleshooting guide based on real field issues
- Added setup guides for Pi flashing and Coral TPU installation

## Lessons Learned

- **I2C reliability**: The BME280 sensor can cause I2C hangs that freeze the entire web interface. Solved with threaded sensor reads and 3-second timeouts.
- **GPIO persistence**: `gpiozero` resets GPIO pins when the process exits, turning off relays immediately. Switched to `pinctrl` which sets pin state at the hardware level.
- **Single-threaded Flask**: Default Flask blocks on slow requests. `threaded=True` was essential for responsiveness.
- **sudo and venvs**: `sudo` doesn't see virtual environment binaries. The systemd service uses the full venv path.
