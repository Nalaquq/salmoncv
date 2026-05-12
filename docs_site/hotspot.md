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

### Step 3: Reboot and verify

```bash
sudo reboot
```

After reboot, verify you can still SSH in:

```bash
ssh nalaquq@nalaquqpi.local
```

Then connect your phone to the **SalmonCV** Wi-Fi and open **http://192.168.4.1**.

### Step 4: Cancel the revert

Once everything works, cancel the scheduled revert so the hotspot stays permanent:

```bash
# If using 'at':
sudo atrm $(atq | head -1 | awk '{print $1}')

# If using systemd timer:
sudo systemctl stop salmoncv-revert.timer
sudo systemctl disable salmoncv-revert.timer
```

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
