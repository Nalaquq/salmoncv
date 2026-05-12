# SalmonCV

SalmonCV is a solar-powered salmon counting system built on a Raspberry Pi 5. It captures time-lapse images, runs fish detection using a Google Coral Edge TPU, logs environmental data, and uploads results over Starlink.

Designed for unattended field deployment in Quinhagak, Alaska.

## What It Does

- **Web Dashboard** — Browser-based control panel accessible from phone or tablet over Wi-Fi. Start/stop all services, adjust camera settings, view gallery, monitor power and environment — no SSH needed.
- **Camera** — Captures images on a timer with manual controls (shutter, gain, white balance, exposure). Logs metadata including environmental sensor data.
- **Lights** — Turns LED floodlights on at sunset and off at sunrise automatically, or on a custom schedule
- **Sensors** — Logs temperature, humidity, and barometric pressure from a BME280 sensor
- **Monitor** — Estimated power draw, environmental charts, and system health monitoring
- **Power** — Controls relay-switched loads (lights, Starlink) from the command line or browser
- **Storage** — Samsung T9 SSD as primary storage with automatic SD card fallback
- **Inference** — Classifies images on-device using a Coral Edge TPU (optional)

## Hardware

- Raspberry Pi 5
- Google Coral USB Accelerator
- Raspberry Pi HQ Camera (IMX477)
- BME280 environmental sensor (inside camera case)
- Samsung T9 SSD (932GB primary storage)
- 2-channel relay board (GPIO17 = lights, GPIO27 = Starlink)
- 100W solar panel, 30A charge controller, 12V marine battery
- Starlink terminal

## Connect to the Dashboard

| Method | Address |
|--------|---------|
| **Wi-Fi hotspot** | Connect to `SalmonCV` Wi-Fi, open **http://192.168.4.1** |
| **Local network** | Open **http://nalaquqpi.local** |
| **SSH** | `ssh nalaquq@nalaquqpi.local` |

The dashboard starts automatically on boot. Hit **Start Counting** to launch camera, sensors, lights, and Starlink.

## Quick Start (First-Time Setup)

SSH into the Pi:

```bash
ssh nalaquq@nalaquqpi.local
cd ~/salmoncv
source venv/bin/activate
git pull
pip install -e .
```

Enable auto-start on boot:

```bash
sudo bash scripts/install_service.sh
```

Set up the Wi-Fi hotspot (requires monitor access):

```bash
sudo bash scripts/setup_hotspot.sh
sudo reboot
```

See the full usage guide: [docs/usage-guide.md](docs/usage-guide.md)

## Commands

| Command | Description |
|---------|-------------|
| `salmoncv-camera` | Capture images with optional Coral TPU inference |
| `salmoncv-lights` | Schedule lights based on sunset/sunrise or custom times |
| `salmoncv-starlink` | Schedule Starlink power based on upload needs or custom times |
| `salmoncv-sensors` | Log BME280 environmental data to CSV |
| `salmoncv-power` | Turn lights and Starlink on or off |
| `salmoncv-watchdog` | Safety check — force off relays that exceed max duration |
| `salmoncv-web` | Start the web dashboard (default port 80) |
| `salmoncv-probe` | Test GPIO pins to identify relay wiring |

## Project Structure

```
salmoncv/
├── src/salmoncv/       Python package
│   ├── camera.py       Image capture and inference
│   ├── lights.py       Sunset/sunrise light scheduling
│   ├── sensors.py      BME280 environmental logging
│   ├── power.py        Relay control (lights, Starlink)
│   ├── gpio_probe.py   GPIO pin testing utility
│   ├── storage.py      Smart storage (T9 SSD / SD card fallback)
│   └── web/            Flask web dashboard
├── docs/               Setup guides and design documents
├── scripts/            Setup and install scripts
├── tests/              Test suite (placeholder)
├── coral_test/         Coral TPU test model and data
├── data/               Sensor and capture logs (gitignored)
└── pyproject.toml      Package configuration
```

## Web Dashboard

Access from phone or tablet — no SSH required. The dashboard starts on boot via systemd.

| Page | What it does |
|------|-------------|
| **Dashboard** | Start/stop all services, system overview, storage selector |
| **Camera** | Single capture with preview, time-lapse, manual settings (shutter, ISO, white balance) |
| **Gallery** | Browse/delete captured images with thumbnails and lightbox |
| **Sensors** | Live BME280 readings, history table, CSV download |
| **Monitor** | Estimated power draw, temperature/humidity/pressure charts, case health |
| **Power** | Toggle lights/Starlink, start/stop schedulers with auto or manual mode |
| **Settings** | System info, disk usage (T9 + SD), log file downloads |

Setup guides: [hotspot](docs/hotspot-setup.md) | [auto-start](docs/usage-guide.md#web-dashboard)

## Setup From Scratch

If you are setting up a brand new Raspberry Pi, follow these guides in order:

1. [Flash and configure the Pi](docs/flash_os_set_pi_config.txt)
2. [Install Python 3.9 and Coral TPU](docs/raspberry_pi_coral_tpu_pyenv_setup.md)
3. [Install and use SalmonCV](docs/usage-guide.md)

## License

Nalaquq, LLC
