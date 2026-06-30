# Troubleshooting

Common issues and fixes for SalmonCV.

## Web Dashboard

### Can't access the dashboard

1. Make sure the service is running:
    ```bash
    sudo systemctl status salmoncv-web
    ```
2. If stopped, start it:
    ```bash
    sudo systemctl start salmoncv-web
    ```
3. Check which address to use:
    - **Wi-Fi hotspot**: http://192.168.4.1
    - **Local network**: http://nalaquqpi.local

### Start Counting doesn't work after boot

If "Start Counting" works when you run `salmoncv-web` from the terminal but not after a reboot (via systemd), make sure you're running the latest version:

```bash
cd ~/salmoncv
source venv/bin/activate
git pull
pip install -e ".[pi]"
sudo systemctl restart salmoncv-web
```

This was a known bug (fixed) where subprocess commands weren't using full venv paths, so systemd couldn't find them.

### Dashboard is slow or unresponsive

The dashboard uses threaded mode and AJAX timeouts to stay responsive. If pages freeze:

- Refresh the browser
- Navigate back to the Dashboard page
- Check if the sensor is causing I2C hangs (see [Sensor Issues](#sensor-issues))

### "salmoncv-web: command not found" with sudo

`sudo` doesn't see virtual environment commands. Use the full path:

```bash
sudo /home/nalaquq/salmoncv/venv/bin/salmoncv-web
```

Or use the systemd service (recommended):

```bash
sudo systemctl start salmoncv-web
```

## Camera

### "rpicam-still: command not found"

Make sure you're on Raspberry Pi OS Bookworm or later. Older versions use `raspistill` instead.

### Black or overexposed images

Try manual camera settings:

- **Too dark**: increase gain (`--gain 8`) or use longer shutter (`--shutter 50000`)
- **Too bright**: decrease gain, shorter shutter, or negative EV (`--ev -2`)
- **Color cast**: try a different white balance (`--awb daylight`)

### Camera page shows "failed to capture"

- Check the camera cable connection
- Test from the command line:
    ```bash
    rpicam-still -o test.jpg
    ```

## Sensor Issues

### "Sensor not available" in the dashboard

Run the I2C detection tool:

```bash
sudo i2cdetect -y 1
```

- If `76` appears: the sensor is connected. The issue may be a temporary I2C glitch --- restart the service.
- If the grid is empty: the sensor is not detected. Check wiring.

### [Errno 121] Remote I/O error

The sensor is not responding on the I2C bus. Almost always a loose wire:

1. Power off the Pi
2. Reseat all four BME280 wires (VIN, GND, SCL, SDA)
3. Power back on
4. Run `sudo i2cdetect -y 1`

### I2C not enabled

```bash
sudo raspi-config
```

Navigate to **Interface Options > I2C** and enable it. Reboot.

## Power / Relays

### Relay not clicking

- Check 5V power to the relay board
- Verify GPIO wiring matches the expected pins (GPIO 17 = lights, GPIO 27 = Starlink)
- Test with the probe tool:
    ```bash
    salmoncv-probe
    ```

### Lights or Starlink won't turn off

The easiest fix is to click **Stop All** on the dashboard --- it stops all services and turns off both relays.

From the command line, run the watchdog:

```bash
salmoncv-watchdog
```

Or force everything off:

```bash
salmoncv-power all-off
```

## Storage

### Images saving to SD card instead of T9

See [Storage Troubleshooting](storage.md#troubleshooting).

## Starlink

### Scheduler not powering on Starlink

- Check if there are new images to upload:
    ```bash
    ls ~/salmoncv/captures/*.jpg | wc -l
    ```
- Check the upload manifest --- images already in the manifest won't be re-uploaded:
    ```bash
    wc -l ~/salmoncv/data/upload_manifest.csv
    ```
- Try manual mode with a fixed window:
    ```bash
    salmoncv-starlink --on-time 14:00 --upload-time 30
    ```

## Wi-Fi / Network

For the full networking guide, see [Networking](networking.md).

### Pi not showing up on your Wi-Fi

If you can't reach the Pi via `ping nalaquqpi.local` or SSH, work through these options in order:

1. **SalmonCV hotspot** --- connect your phone/tablet to SSID **SalmonCV** (password: `salmon2026`) and open **http://192.168.4.1**
2. **Raspberry Pi Connect** --- go to [connect.raspberrypi.com](https://connect.raspberrypi.com) and open a remote terminal (Pi must be online)
3. **Ethernet cable** --- plug directly from your PC to the Pi's ethernet port
4. **HDMI + keyboard** --- connect a monitor and USB keyboard to the Pi
5. **SD card edit** --- pull the microSD card and edit the Wi-Fi config from your PC

Each method is documented in full at [Networking](networking.md).

### Adding a new Wi-Fi network

Once you can access the Pi:

```bash
sudo nmcli device wifi connect "NETWORK_NAME" password "PASSWORD"
```

NetworkManager remembers all saved networks and auto-connects to whichever is available.

### SSH connection refused

SSH may not be enabled. From the Pi (with monitor and keyboard):

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

Or enable it from the SD card by creating an empty file called `ssh` on the boot partition. See [Networking --- Enabling SSH](networking.md#enabling-ssh).

## General

### How to shut down or reboot the Pi

Use the **Pi Power** page in the dashboard. Click **Shut Down Pi** or **Reboot Pi** and confirm. After a shutdown, you must press the physical power button on the Pi to turn it back on.

From the command line:

```bash
sudo shutdown -h now   # power off
sudo reboot            # restart
```

### How to restart everything

```bash
sudo systemctl restart salmoncv-web
```

### How to check logs

```bash
# Web dashboard service logs
sudo journalctl -u salmoncv-web --no-pager -n 50

# Application logs
ls ~/salmoncv/data/*.csv
```

### How to update the software

```bash
cd ~/salmoncv
source venv/bin/activate
git pull
pip install -e ".[pi]"
sudo systemctl restart salmoncv-web
```
