# Wi-Fi Hotspot Setup

This guide configures the Raspberry Pi to broadcast its own Wi-Fi network so you can connect a phone or tablet directly — no internet required.

## How It Works

The Pi creates a Wi-Fi network called **SalmonCV**. Connect your device to it, open a browser, and type the Pi's IP address to access the dashboard. The Pi's existing Wi-Fi connection (for Starlink internet) continues working at the same time.

## Requirements

- Raspberry Pi 5 (built-in Wi-Fi supports AP + client simultaneously)
- Raspberry Pi OS (Bookworm or later)

## Setup

Run the setup script once:

```bash
cd ~/salmoncv
sudo bash scripts/setup_hotspot.sh
```

This installs and configures `hostapd` (access point) and `dnsmasq` (DHCP server), then enables them to start on boot.

### Custom SSID and Password

```bash
sudo bash scripts/setup_hotspot.sh "MyCustomSSID" "mypassword"
```

Default password is `salmon2026`.

## After Setup

Reboot the Pi:

```bash
sudo reboot
```

Then:

1. On your phone/tablet, connect to Wi-Fi network **SalmonCV**
2. Open a browser
3. Go to `http://192.168.4.1`

## Starting the Dashboard

The web dashboard must be running for the browser interface to work:

```bash
sudo salmoncv-web
```

To run it in the background so it survives logout:

```bash
tmux new -d -s web 'sudo salmoncv-web'
```

To make it start automatically on boot, add a systemd service (see below).

## Auto-Start on Boot (Optional)

Create a systemd service:

```bash
sudo tee /etc/systemd/system/salmoncv-web.service <<EOF
[Unit]
Description=SalmonCV Web Dashboard
After=network.target

[Service]
Type=simple
ExecStart=/home/nalaquq/salmoncv/venv/bin/salmoncv-web
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable salmoncv-web
sudo systemctl start salmoncv-web
```

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
```

**Connected but can't load the page**

Make sure the dashboard is running:

```bash
sudo systemctl status salmoncv-web
# or check if anything is on port 80:
ss -tlnp | grep :80
```

**Want to change the password later**

Edit `/etc/hostapd/hostapd.conf`, change the `wpa_passphrase` line, then:

```bash
sudo systemctl restart hostapd
```
