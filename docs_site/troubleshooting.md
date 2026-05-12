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

Run the watchdog manually:

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

## General

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
pip install -e .
sudo systemctl restart salmoncv-web
```
