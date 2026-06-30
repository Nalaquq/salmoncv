# Wi-Fi Hotspot

The Pi broadcasts its own Wi-Fi network so you can connect a phone or tablet directly in the field --- no internet or router needed.

## How It Works

The Pi creates a Wi-Fi access point called **SalmonCV** using `hostapd` and `dnsmasq`. Your device connects to this network and accesses the dashboard at a static IP. The Pi's existing Wi-Fi connection (for Starlink) continues working simultaneously.

The setup script creates a virtual `ap0` interface on the same Wi-Fi radio as `wlan0`. The Pi 5 supports simultaneous AP + client mode, but both must share the same radio channel. The script auto-detects the channel of your current Wi-Fi connection and configures the hotspot to match.

For an overview of all connection methods (hotspot, SSH, Raspberry Pi Connect, ethernet, HDMI), see [Networking](networking.md).

## Network Details

| Setting | Value |
|---------|-------|
| SSID | SalmonCV |
| Password | salmon2026 |
| Pi IP address | 192.168.4.1 |
| DHCP range | 192.168.4.10 -- 192.168.4.50 |
| Dashboard URL | http://192.168.4.1 |

## Setup

### Step 1: Preview (dry run)

See exactly what the script will change without touching anything:

```bash
cd ~/salmoncv
sudo bash scripts/setup_hotspot.sh --dry-run
```

This prints every config file that would be created. Review it over SSH --- nothing is modified.

### Step 2: Install with safety net

```bash
sudo bash scripts/setup_hotspot.sh --safe
```

This installs the hotspot **and** schedules an automatic revert in 5 minutes. If the hotspot breaks SSH, just wait --- networking restores itself. You can set a longer window:

```bash
sudo bash scripts/setup_hotspot.sh --safe 10    # 10-minute safety net
```

The hotspot activates immediately --- no reboot required. You should see **SalmonCV** in your device's Wi-Fi list right away.

### Step 3: Verify and cancel the revert

Connect your phone or laptop to the **SalmonCV** Wi-Fi and open **http://192.168.4.1**. If it works, cancel the scheduled revert so the hotspot stays permanent:

```bash
# If using 'at':
sudo atrm $(atq | head -1 | awk '{print $1}')

# If using systemd timer:
sudo systemctl stop salmoncv-revert.timer
sudo systemctl disable salmoncv-revert.timer
```

### Step 4: Reboot and confirm persistence

```bash
sudo reboot
```

After reboot, verify **SalmonCV** still appears and you can reach the dashboard.

### Custom SSID and Password

```bash
sudo bash scripts/setup_hotspot.sh --safe "MyNetworkName" "mypassword"
```

### Reverting

If you ever want to remove the hotspot entirely:

```bash
sudo bash scripts/setup_hotspot.sh --revert
sudo reboot
```

## Connecting

1. On your phone or tablet, go to Wi-Fi settings
2. Connect to the **SalmonCV** network
3. Enter password: `salmon2026`
4. Open a browser and go to **http://192.168.4.1**

You can also SSH into the Pi over the hotspot:

```bash
ssh nalaquq@192.168.4.1
```

## What the Script Does

The setup script (`scripts/setup_hotspot.sh`):

1. Detects the channel and band of the current `wlan0` Wi-Fi connection
2. Installs `hostapd` (access point) and `dnsmasq` (DHCP server)
3. Tells NetworkManager to ignore the `ap0` interface (prevents it from stripping the static IP)
4. Creates a systemd service (`ap0.service`) that builds a virtual AP interface on boot using `iw dev wlan0 interface add ap0 type __ap`
5. Assigns a static IP (`192.168.4.1`) to the `ap0` interface
6. Configures `hostapd` with the SSID, password, and matching channel
7. Configures `dnsmasq` to assign IP addresses to connecting devices
8. Enables all services to start on boot
9. Activates the hotspot immediately (no reboot needed)

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

Check if hostapd is running:

```bash
sudo systemctl status hostapd
sudo journalctl -u hostapd --no-pager -n 20
```

Check if the `ap0` interface exists and has an IP:

```bash
ip addr show ap0
```

If `ap0` doesn't exist, restart the service:

```bash
sudo systemctl restart ap0.service
sudo systemctl restart hostapd
```

**Connected but getting a 169.254.x.x address (no DHCP)**

Check that dnsmasq is running and configured for `ap0`:

```bash
sudo systemctl status dnsmasq
cat /etc/dnsmasq.d/salmoncv.conf
```

If the config file is missing, re-run the setup script.

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

**hostapd says "ConditionFileNotEmpty not met"**

The config file is missing. Re-run the setup script:

```bash
cd ~/salmoncv
sudo bash scripts/setup_hotspot.sh --safe
```
