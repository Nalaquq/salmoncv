# Networking

How to connect to the Pi, manage Wi-Fi networks, and regain access when things go wrong.

## Connection Methods (in order of preference)

| Method | When to use | Requires |
|--------|-------------|----------|
| [SalmonCV hotspot](#salmoncv-hotspot) | Always works, primary field method | Hotspot set up on Pi |
| [SSH over Wi-Fi](#ssh-over-wi-fi) | Pi is on the same network as your computer | Same Wi-Fi network |
| [Raspberry Pi Connect](#raspberry-pi-connect) | Pi is online but you're on a different network | Pi connected to internet |
| [Ethernet direct](#ethernet-direct-connection) | Pi isn't on any Wi-Fi and you have a cable | Ethernet cable |
| [HDMI + keyboard](#hdmi--keyboard) | Nothing else works | Monitor, micro-HDMI cable, USB keyboard |
| [SD card edit](#changing-wi-fi-via-sd-card) | Pi is inaccessible and can't be taken apart easily | microSD card reader |

## SalmonCV Hotspot

The Pi broadcasts its own Wi-Fi network. Connect directly from a phone, tablet, or laptop --- no router or internet needed. This is the primary way to access the Pi in the field.

| Setting | Value |
|---------|-------|
| SSID | SalmonCV |
| Password | salmon2026 |
| Dashboard URL | http://192.168.4.1 |

1. On your device, go to Wi-Fi settings
2. Connect to **SalmonCV**
3. Enter password: `salmon2026`
4. Open a browser and go to **http://192.168.4.1**

See [Wi-Fi Hotspot](hotspot.md) for setup instructions.

## SSH over Wi-Fi

When the Pi and your computer are on the same Wi-Fi network:

```bash
ssh nalaquq@nalaquqpi.local
```

If the hostname doesn't resolve, find the Pi's IP address from your router's admin page or by scanning:

```powershell
# PowerShell — scan for Pi's MAC address (starts with 2c:cf:67)
arp -a
```

Then connect using the IP directly:

```bash
ssh nalaquq@192.168.1.xxx
```

### Enabling SSH

SSH should be enabled during the initial OS flash (see [Pi Setup](pi-setup.md)). If it's not running:

**From the Pi (with monitor and keyboard):**

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

**From the SD card (without access to the Pi):**

Pull the microSD card, plug it into your PC, and create an empty file called `ssh` (no file extension) on the boot partition. On Windows:

```powershell
New-Item -Path "D:\ssh" -ItemType File
```

Replace `D:` with the actual drive letter of the boot partition.

## Raspberry Pi Connect

[Raspberry Pi Connect](https://connect.raspberrypi.com) provides remote access from any browser, even when the Pi is on a different network. The Pi must be connected to the internet for this to work.

1. Go to [connect.raspberrypi.com](https://connect.raspberrypi.com)
2. Log in with your Raspberry Pi account
3. Your Pi should appear with a green status indicator
4. Click to open a remote terminal

If the Pi shows as offline (no green indicator), it's not connected to the internet. Use one of the other connection methods to get it online first.

### Setting up Raspberry Pi Connect

If you didn't set it up during the initial flash:

```bash
sudo apt install rpi-connect
sudo loginctl enable-linger nalaquq
rpi-connect signin
```

Follow the on-screen instructions to link the Pi to your Raspberry Pi account.

## Managing Wi-Fi Networks

The Pi uses NetworkManager to manage Wi-Fi. It remembers all saved networks and auto-connects to whichever is available.

### Adding a new network

```bash
sudo nmcli device wifi connect "NETWORK_NAME" password "PASSWORD"
```

### Listing saved networks

```bash
nmcli connection show
```

### Removing a saved network

```bash
sudo nmcli connection delete "NETWORK_NAME"
```

### Scanning for available networks

```bash
sudo nmcli device wifi list
```

### Switching networks

You don't need to --- NetworkManager auto-connects to whichever saved network is in range. If multiple are available, it picks the one with the strongest signal. To force a specific network:

```bash
nmcli connection up "NETWORK_NAME"
```

## Ethernet Direct Connection

If the Pi isn't on any Wi-Fi network, you can connect an ethernet cable directly from your computer to the Pi's ethernet port. This creates a link-local connection without needing a router.

1. Plug an ethernet cable from your PC (or USB-C ethernet adapter) into the Pi's RJ45 port
2. Wait 30 seconds for the link to establish
3. Try from PowerShell:

```powershell
ping nalaquqpi.local
```

If the ping succeeds:

```powershell
ssh nalaquq@nalaquqpi.local
```

If the hostname doesn't resolve, check `arp -a` for the Pi's MAC (`2c:cf:67:xx:xx:xx`) or scan the link-local range.

!!! note
    WSL cannot resolve `.local` hostnames. Use PowerShell for ping and SSH, or find the IP address first and use that in WSL.

## HDMI + Keyboard

When no network connection is available, connect a monitor and keyboard directly to the Pi.

### What you need

- **Micro-HDMI to HDMI cable** (or adapter) --- the Pi 5 uses micro-HDMI, not full-size
- **USB-A keyboard** --- plugs into the Pi's full-size USB ports
- **A monitor or TV** with an HDMI input --- your laptop's HDMI port is output-only and won't work

### Steps

1. Plug the micro-HDMI cable from the Pi (use the port closest to USB-C power) to your monitor
2. Plug a USB keyboard into any USB-A port on the Pi
3. Power on the Pi and wait for the login prompt
4. Log in:

```
Username: nalaquq
Password: Quinhagak
```

5. Add your Wi-Fi network and enable SSH:

```bash
sudo nmcli device wifi connect "YOUR_WIFI_NAME" password "YOUR_PASSWORD"
sudo systemctl enable ssh
sudo systemctl start ssh
```

6. Set up the hotspot if it's not already running:

```bash
cd ~/salmoncv
git pull
sudo bash scripts/setup_hotspot.sh --safe
sudo reboot
```

After reboot, you can disconnect the monitor and keyboard. The Pi will be accessible via SSH and the SalmonCV hotspot.

## Changing Wi-Fi via SD Card

Last resort when nothing else works and you can physically access the microSD card.

### Removing the SD card

1. **Unplug the Pi's power cable** --- never remove the card while running
2. **Locate the microSD slot** on the bottom of the Pi board (opposite the USB/Ethernet ports)
3. **Push the card in gently** --- it's spring-loaded, push and it clicks out
4. **Plug it into a USB card reader** on your PC

### Editing the Wi-Fi config

The Wi-Fi config is on the ext4 (Linux) partition, which Windows can't read natively. Use WSL to mount it.

**In PowerShell (as Administrator):**

```powershell
# Find the SD card's disk number
diskpart
# type: list disk
# find the SD card by size (e.g., 32 GB or 64 GB), note the number
# type: exit

# Mount the Linux partition in WSL (replace # with disk number)
wsl --mount \\.\PHYSICALDRIVE# --partition 2
```

**In WSL:**

```bash
# Create a NetworkManager connection file
sudo tee /mnt/wsl/PHYSICALDRIVE*/etc/NetworkManager/system-connections/wifi.nmconnection << 'EOF'
[connection]
id=wifi
type=wifi
autoconnect=true

[wifi]
ssid=YOUR_WIFI_NAME
mode=infrastructure

[wifi-security]
key-mgmt=wpa-psk
psk=YOUR_PASSWORD

[ipv4]
method=auto

[ipv6]
method=auto
EOF

# Set required permissions
sudo chmod 600 /mnt/wsl/PHYSICALDRIVE*/etc/NetworkManager/system-connections/wifi.nmconnection
```

**Unmount in PowerShell:**

```powershell
wsl --unmount \\.\PHYSICALDRIVE#
```

### Enabling SSH from the SD card

While the card is in your PC, you can also enable SSH. The boot partition shows up as a regular drive in Windows (FAT32). Create an empty file called `ssh` (no extension) on it:

```powershell
# Replace D: with the boot partition's drive letter
New-Item -Path "D:\ssh" -ItemType File
```

### Putting it back

1. Safely eject the card from Windows
2. Slide it back into the Pi until it clicks
3. Plug in power and wait 1--2 minutes
4. Try `ping nalaquqpi.local` from PowerShell

## Quick Reference

### Pi network details

| Setting | Value |
|---------|-------|
| Hostname | nalaquqpi.local |
| Username | nalaquq |
| Pi MAC address prefix | 2c:cf:67 |

### Common commands

```bash
# Check current network
nmcli device status

# Show IP addresses
ip addr show

# Check if SSH is running
sudo systemctl status ssh

# Check if hotspot is running
sudo systemctl status hostapd

# Restart networking
sudo systemctl restart NetworkManager
```
