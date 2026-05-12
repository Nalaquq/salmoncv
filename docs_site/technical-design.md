# Technical Design

!!! note
    This is a summary of the full technical design document. The complete version is at `docs/salmoncv_technical_design_document.md` in the repository.

## System Overview

SalmonCV is a solar-powered, edge-computing platform for automated salmon detection and counting. It uses a Raspberry Pi 5, Google Coral Edge TPU, and environmental sensors deployed in Quinhagak, Alaska.

## Architecture

```text
Solar Panel -> Charge Controller -> 12V Battery -> Fuses/Bus Bars
                                             |
                                             +-> Buck Converter (5V) -> Raspberry Pi 5
                                             |                          |
                                             |                          +-> Camera (IMX477)
                                             |                          +-> Coral USB TPU
                                             |                          +-> BME280 Sensor
                                             |                          +-> Flask Web App
                                             |
                                             +-> Relay Board -> Automotive Relays
                                                                 |-> LED Lights (GPIO 17)
                                                                 |-> Starlink (GPIO 27)
```

## Software Components

| Module | File | Purpose |
|--------|------|---------|
| Camera | `camera.py` | Time-lapse capture with optional Coral TPU inference |
| Lights | `lights.py` | Civil twilight scheduling for LED floodlights |
| Starlink | `starlink.py` | Bandwidth-based upload window scheduling |
| Sensors | `sensors.py` | BME280 environmental data logging |
| Power | `power.py` | GPIO relay control via `pinctrl` |
| Watchdog | `watchdog.py` | Safety limits on relay on-durations |
| Storage | `storage.py` | Samsung T9 SSD primary with SD card fallback |
| Web | `web/app.py` | Flask dashboard for browser-based control |

## Data Flow

1. Camera captures images at a configurable interval
2. Each image is logged with metadata and sensor readings to `capture_log.csv`
3. Optional: Coral TPU runs inference, results logged to `inference_log.csv`
4. Starlink scheduler calculates upload window from pending image count
5. During upload window, images are transferred and marked in the manifest

## Power Budget

| Component | Draw | Duty Cycle |
|-----------|------|------------|
| Raspberry Pi 5 | ~5W | Continuous |
| Camera | ~1.5W | During captures |
| Samsung T9 SSD | ~0.5W | Continuous |
| Coral USB TPU | ~2.5W | During inference |
| LED Lights | ~50W | Dusk to dawn |
| Starlink | ~50W | Upload windows only |

The 100W solar panel and 12V marine battery provide enough stored energy for continuous Pi operation. Lights and Starlink are power-managed by the scheduler to avoid draining the battery.

## Design Decisions

- **`pinctrl` over `gpiozero`**: GPIO state persists after the Python process exits, preventing relays from resetting
- **PID files for subprocess management**: Camera, sensors, and schedulers run as background processes tracked by PID files
- **CSV over databases**: No SQLite or PostgreSQL --- all logs are plain CSV files, easy to inspect and download
- **No JavaScript frameworks**: Vanilla HTML/CSS/JS to minimize payload and avoid build tooling
- **Threaded Flask**: `threaded=True` prevents slow I2C sensor reads from blocking the web interface
