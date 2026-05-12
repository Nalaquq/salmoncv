# Wi-Fi Hotspot

The Pi broadcasts its own Wi-Fi network so you can connect a phone or tablet directly in the field --- no internet or router needed.

## How It Works

The Pi creates a Wi-Fi access point called **SalmonCV** using `hostapd` and `dnsmasq`. Your device connects to this network and accesses the dashboard at a static IP. The Pi's existing Wi-Fi connection (for Starlink) continues working simultaneously.

## Network Details

| Setting | Value |
|---------|-------|
| SSID | SalmonCV |
| Password | salmon2026 |
| Pi IP address | 192.168.4.1 |
| DHCP range | 192.168.4.10 -- 192.168.4.50 |
| Dashboard URL | http://192.168.4.1 |

## Setup

!!! warning "Requires physical access"
    Run this with a monitor and keyboard connected to the Pi, in case something goes wrong with networking.

```bash
cd ~/salmoncv
sudo bash scripts/setup_hotspot.sh
sudo reboot
```

### Custom SSID and Password

```bash
sudo bash scripts/setup_hotspot.sh "MyNetworkName" "mypassword"
```

## Connecting

After the Pi reboots:

1. On your phone or tablet, go to Wi-Fi settings
2. Connect to the **SalmonCV** network
3. Enter password: `salmon2026`
4. Open a browser and go to **http://192.168.4.1**

## What the Script Does

The setup script (`scripts/setup_hotspot.sh`):

1. Installs `hostapd` (access point) and `dnsmasq` (DHCP server)
2. Creates a virtual AP interface (`ap0`)
3. Sets a static IP on the AP interface
4. Configures `hostapd` with the SSID and password
5. Configures `dnsmasq` to assign IP addresses to connecting devices
6. Enables both services to start on boot

## Changing the Password Later

Edit the hostapd config:

```bash
sudo nano /etc/hostapd/hostapd.conf
```

Change the `wpa_passphrase` line, then restart:

```bash
sudo systemctl restart hostapd
```

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
ss -tlnp | grep :80
```

If the service isn't running, start it:

```bash
sudo systemctl start salmoncv-web
```

**Pi lost internet after setup**

The hotspot should not affect the existing Wi-Fi connection. Check:

```bash
ip addr show wlan0    # should have an IP from your router
ip addr show ap0      # should have 192.168.4.1
```
