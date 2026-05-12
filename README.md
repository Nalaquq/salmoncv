# SalmonCV

SalmonCV is a solar-powered salmon counting system built on a Raspberry Pi 5. It captures time-lapse images, runs fish detection using a Google Coral Edge TPU, logs environmental data, and uploads results over Starlink.

Designed for unattended field deployment in Quinhagak, Alaska.

## What It Does

- **Camera** — Captures images on a timer and logs metadata (file size, resolution, temperature, humidity, pressure)
- **Lights** — Turns LED floodlights on at sunset and off at sunrise automatically, or on a custom schedule
- **Sensors** — Logs temperature, humidity, and barometric pressure from a BME280 sensor
- **Power** — Controls relay-switched loads (lights, Starlink) from the command line
- **Inference** — Classifies images on-device using a Coral Edge TPU (optional)

## Hardware

- Raspberry Pi 5
- Google Coral USB Accelerator
- Raspberry Pi HQ Camera (IMX477)
- BME280 environmental sensor
- 2-channel relay board (GPIO17 = lights, GPIO27 = Starlink)
- 100W solar panel, 30A charge controller, 12V marine battery
- Starlink terminal

## Quick Start

SSH into the Pi:

```bash
ssh nalaquq@nalaquqpi.local
```

Install the software:

```bash
cd ~/salmoncv
git pull
source venv/bin/activate
pip install -e .
```

Test the camera:

```bash
salmoncv-camera --no-inference --outdir ~/salmoncv/test_captures
```

Test the lights:

```bash
salmoncv-power lights-on
salmoncv-power lights-off
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
│   └── web/            Flask web dashboard
├── docs/               Setup guides and design documents
├── scripts/            Shell utilities
├── tests/              Test suite (placeholder)
├── coral_test/         Coral TPU test model and data
├── data/               Sensor and capture logs (gitignored)
└── pyproject.toml      Package configuration
```

## Web Dashboard

Access the full dashboard from a phone or tablet — no SSH required.

```bash
sudo salmoncv-web          # start on port 80
salmoncv-web --port 5000   # development mode
```

Set up the Wi-Fi hotspot so field users can connect directly: [docs/hotspot-setup.md](docs/hotspot-setup.md)

## Setup From Scratch

If you are setting up a brand new Raspberry Pi, follow these guides in order:

1. [Flash and configure the Pi](docs/flash_os_set_pi_config.txt)
2. [Install Python 3.9 and Coral TPU](docs/raspberry_pi_coral_tpu_pyenv_setup.md)
3. [Install and use SalmonCV](docs/usage-guide.md)

## License

Nalaquq, LLC
