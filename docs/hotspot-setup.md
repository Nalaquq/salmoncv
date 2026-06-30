# Wi-Fi Hotspot Setup

This guide configures the Raspberry Pi to broadcast its own Wi-Fi network so you can connect a phone or tablet directly — no internet required.

For the full networking guide (SSH, Raspberry Pi Connect, ethernet, HDMI, SD card editing), see `docs_site/networking.md`.

## How It Works

The Pi creates a Wi-Fi network called **SalmonCV**. Connect your device to it, open a browser, and type the Pi's IP address to access the dashboard. The Pi's existing Wi-Fi connection (for Starlink internet) continues working at the same time.

The setup script creates a virtual `ap0` interface using `iw dev wlan0 interface add ap0 type __ap`. The Pi 5 supports simultaneous AP + client mode, but both must share the same radio channel. The script auto-detects the channel of your current Wi-Fi connection and configures the hotspot to match.

## Requirements

- Raspberry Pi 5 (built-in Wi-Fi supports AP + client simultaneously)
- Raspberry Pi OS (Bookworm or later)

## Setup

### Safe workflow (recommended over SSH)

```bash
cd ~/salmoncv

# 1. Preview what will change (nothing is modified)
sudo bash scripts/setup_hotspot.sh --dry-run

# 2. Install with automatic revert in 5 minutes
sudo bash scripts/setup_hotspot.sh --safe

# The hotspot activates immediately — no reboot needed.
# Connect to SalmonCV Wi-Fi and test http://192.168.4.1

# 3. Cancel the revert once confirmed:
#    sudo systemctl stop salmoncv-revert.timer
#    sudo systemctl disable salmoncv-revert.timer

# 4. Reboot and verify persistence:
sudo reboot
```

If SSH breaks after reboot, just wait 5 minutes — networking reverts automatically.

### Direct install (with monitor/keyboard available)

```bash
cd ~/salmoncv
sudo bash scripts/setup_hotspot.sh
```

This installs and activates the hotspot immediately.

### Custom SSID and Password

```bash
sudo bash scripts/setup_hotspot.sh --safe "MyCustomSSID" "mypassword"
```

### Reverting

```bash
sudo bash scripts/setup_hotspot.sh --revert
sudo reboot
```

Default password is `salmon2026`.

## After Setup

Connect and test:

1. On your phone/tablet, connect to Wi-Fi network **SalmonCV**
2. Open a browser
3. Go to `http://192.168.4.1`

You can also SSH over the hotspot:

```bash
ssh nalaquq@192.168.4.1
```

## What the Script Does

The setup script (`scripts/setup_hotspot.sh`):

1. Detects wlan0's current channel and band (2.4 or 5 GHz)
2. Installs `hostapd` (access point) and `dnsmasq` (DHCP server)
3. Creates `/etc/systemd/system/ap0.service` to build the virtual AP interface on boot
4. Writes `/etc/hostapd/hostapd.conf` with SSID, password, and matching channel
5. Writes `/etc/dnsmasq.d/salmoncv.conf` for DHCP on the `ap0` interface
6. Enables services: `ap0.service`, `hostapd`, `dnsmasq`
7. Activates the hotspot immediately (no reboot needed)

## Network Details

| Setting | Value |
|---------|-------|
| SSID | SalmonCV |
| Password | salmon2026 |
| Pi IP | 192.168.4.1 |
| DHCP range | 192.168.4.10 – 192.168.4.50 |
| Web port | 80 |

## Troubleshooting

**Can't see the SalmonCV network**

```bash
sudo systemctl status hostapd
sudo journalctl -u hostapd --no-pager -n 20
ip addr show ap0
```

If `ap0` doesn't exist:

```bash
sudo systemctl restart ap0.service
sudo systemctl restart hostapd
```

**Connected but getting a 169.254.x.x address**

dnsmasq isn't serving DHCP on `ap0`:

```bash
sudo systemctl status dnsmasq
cat /etc/dnsmasq.d/salmoncv.conf
```

If the config is missing, re-run the setup script.

**Connected but can't load the page**

Make sure the dashboard is running:

```bash
sudo systemctl status salmoncv-web
ss -tlnp | grep :80
```

**Want to change the password later**

Edit `/etc/hostapd/hostapd.conf`, change the `wpa_passphrase` line, then:

```bash
sudo systemctl restart hostapd
```
