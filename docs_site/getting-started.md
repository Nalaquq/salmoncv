# Getting Started

## Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS (Bookworm)
- Python 3.9 via pyenv (required for Coral TPU compatibility)
- All hardware connected (camera, sensor, relay board, SSD)

If setting up from scratch, follow these guides first:

1. [Pi Setup](pi-setup.md) --- Flash OS and configure the Pi
2. [Coral TPU Setup](coral-tpu-setup.md) --- Install Python 3.9 and Coral libraries

## Install SalmonCV

```bash
ssh nalaquq@nalaquqpi.local
cd ~/salmoncv
source venv/bin/activate
git pull
pip install -e .
```

## Enable Auto-Start

Run once to make the web dashboard start on every boot:

```bash
sudo bash scripts/install_service.sh
```

## Test It

Open a browser and go to **http://nalaquqpi.local**. You should see the SalmonCV dashboard.

Test the camera:

```bash
salmoncv-camera --no-inference --outdir ~/salmoncv/test_captures
```

Test the lights:

```bash
salmoncv-power lights-on
salmoncv-power lights-off
```

## Set Up Wi-Fi Hotspot (Optional)

!!! warning "Requires physical access"
    Only do this with a monitor and keyboard connected to the Pi, in case something goes wrong with networking.

```bash
sudo bash scripts/setup_hotspot.sh
sudo reboot
```

After reboot, connect your phone to the **SalmonCV** Wi-Fi network (password: `salmon2026`) and open **http://192.168.4.1**.

See [Wi-Fi Hotspot](hotspot.md) for full details.

## Update Software

After pushing new code to GitHub:

```bash
cd ~/salmoncv
source venv/bin/activate
git pull
pip install -e .
sudo systemctl restart salmoncv-web
```

## CLI Commands

All commands require the virtual environment to be active:

```bash
cd ~/salmoncv && source venv/bin/activate
```

| Command | Description |
|---------|-------------|
| `salmoncv-camera` | Capture images with optional Coral TPU inference |
| `salmoncv-lights` | Schedule lights based on sunset/sunrise or custom times |
| `salmoncv-starlink` | Schedule Starlink power based on upload needs |
| `salmoncv-sensors` | Log BME280 environmental data to CSV |
| `salmoncv-power` | Turn lights and Starlink on or off |
| `salmoncv-watchdog` | Safety check --- force off relays past max duration |
| `salmoncv-web` | Start the web dashboard (default port 80) |
| `salmoncv-probe` | Test GPIO pins to identify relay wiring |
