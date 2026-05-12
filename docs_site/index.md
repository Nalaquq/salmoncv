# SalmonCV

**Solar-powered salmon counting system for Raspberry Pi 5.**

SalmonCV captures time-lapse images, runs fish detection using a Google Coral Edge TPU, logs environmental data, and uploads results over Starlink. Designed for unattended field deployment in Quinhagak, Alaska.

## Connect to the Dashboard

| Method | Address |
|--------|---------|
| **Wi-Fi hotspot** | Connect to `SalmonCV` Wi-Fi (password: `salmon2026`), open **http://192.168.4.1** |
| **Local network** | Open **http://nalaquqpi.local** |
| **SSH** | `ssh nalaquq@nalaquqpi.local` |

The dashboard starts automatically on boot. Hit **Start Counting** to launch camera, sensors, lights, and Starlink.

## Features

- **Web Dashboard** --- Browser-based control panel accessible from phone or tablet over Wi-Fi
- **Camera** --- Time-lapse capture with manual controls (shutter, gain, white balance, exposure)
- **Lights** --- Automatic sunset/sunrise scheduling or custom times
- **Sensors** --- BME280 temperature, humidity, and pressure logging
- **Monitor** --- Estimated power draw, environmental charts, case health
- **Storage** --- Samsung T9 SSD primary with automatic SD card fallback
- **Starlink** --- Bandwidth-based upload window scheduling
- **Inference** --- On-device fish detection with Coral Edge TPU (optional)

## Hardware

- Raspberry Pi 5
- Google Coral USB Accelerator
- Raspberry Pi HQ Camera (IMX477)
- BME280 environmental sensor (inside camera case)
- Samsung T9 SSD (932GB primary storage)
- 2-channel relay board (GPIO17 = lights, GPIO27 = Starlink)
- 100W solar panel, 30A charge controller, 12V marine battery
- Starlink terminal

## Quick Links

- [Getting Started](getting-started.md) --- First-time setup
- [Web Dashboard](web-dashboard.md) --- Browser interface guide
- [Field Deployment](hotspot.md) --- Wi-Fi hotspot and auto-start
- [Troubleshooting](troubleshooting.md) --- Common issues and fixes

---

*Built by [Nalaquq, LLC](https://github.com/Nalaquq)*
