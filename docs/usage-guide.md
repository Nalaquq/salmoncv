# SalmonCV Usage Guide

This guide explains how to install and use each SalmonCV command on the Raspberry Pi. No programming experience is needed.

---

## Installation

Every time you start a new terminal session on the Pi, activate the Python environment first:

```bash
cd ~/salmoncv
source venv/bin/activate
```

If this is your first time (or after pulling new code from GitHub), install the package:

```bash
pip install -e .
```

You only need to run `pip install -e .` once after each code update. The `source venv/bin/activate` step is needed every time you open a new terminal.

To get the latest code from GitHub:

```bash
cd ~/salmoncv
git pull
source venv/bin/activate
pip install -e .
```

---

## Camera

The camera command captures images on a timer and saves them to a folder. Each image is logged in a CSV file with its timestamp, file size, and environmental sensor data (if a BME280 sensor is connected).

### Capture images (no fish detection)

```bash
salmoncv-camera --no-inference --outdir ~/salmoncv/test_captures
```

This saves a photo every 3 seconds to `~/salmoncv/test_captures/`. Press **Ctrl+C** to stop.

### Change the capture interval

Take a photo every 10 seconds:

```bash
salmoncv-camera --no-inference --outdir ~/salmoncv/captures --interval 10
```

### Change the image resolution

```bash
salmoncv-camera --no-inference --outdir ~/salmoncv/captures --width 2028 --height 1520
```

The default is 4056x3040 (full resolution of the HQ camera). Smaller images save disk space and upload faster.

### Capture with fish detection

To run Coral TPU inference on each image, provide a model file:

```bash
salmoncv-camera \
  --model ~/salmoncv/coral_test/mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite \
  --labels ~/salmoncv/coral_test/inat_bird_labels.txt \
  --outdir ~/salmoncv/captures
```

This creates two log files in the output folder:

- **capture_log.csv** — one row per image with timestamp, file size, resolution, and sensor data
- **inference_log.csv** — one row per detection result with class, label, and confidence score

### All camera options

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | none | Path to Edge TPU model file |
| `--labels` | none | Path to labels file |
| `--outdir` | `captures` | Folder to save images and logs |
| `--interval` | `3.0` | Seconds between captures |
| `--width` | `4056` | Image width in pixels |
| `--height` | `3040` | Image height in pixels |
| `--no-inference` | off | Skip Coral TPU, capture only |
| `--top_k` | `3` | Number of top results to log |
| `--threshold` | `0.05` | Minimum confidence to log |
| `--camera-command` | `rpicam-still` | Camera capture command |

---

## Lights

The lights command controls LED floodlights on a schedule. By default, it calculates civil sunset and sunrise for Quinhagak, Alaska and turns the lights on at dusk and off at dawn.

### Automatic mode (sunset/sunrise)

```bash
salmoncv-lights
```

This runs continuously. It checks every 60 seconds whether the lights should be on or off based on the current time and the sun's position. Press **Ctrl+C** to stop (lights will be turned off).

### Custom schedule

Turn lights on at 8:00 PM and off at 6:30 AM:

```bash
salmoncv-lights --on-time 20:00 --off-time 06:30
```

Times are in 24-hour format.

### Override just one time

Use automatic sunrise but turn on at a fixed time:

```bash
salmoncv-lights --on-time 21:00
```

Use automatic sunset but turn off at a fixed time:

```bash
salmoncv-lights --off-time 05:00
```

### Test without turning lights on

See what the schedule would be without actually toggling the relay:

```bash
salmoncv-lights --dry-run
```

### Different location

If deploying somewhere other than Quinhagak:

```bash
salmoncv-lights --lat 61.22 --lon -149.90 --timezone America/Anchorage
```

### All lights options

| Option | Default | Description |
|--------|---------|-------------|
| `--lat` | `59.748` | Latitude (Quinhagak) |
| `--lon` | `-161.922` | Longitude (Quinhagak) |
| `--timezone` | `America/Anchorage` | Timezone |
| `--on-time` | auto (dusk) | Lights-on time (HH:MM) |
| `--off-time` | auto (dawn) | Lights-off time (HH:MM) |
| `--check-interval` | `60` | Seconds between checks |
| `--dry-run` | off | Print schedule only |

### About midnight sun

In summer, Quinhagak has very long days. If there is no civil twilight (the sun doesn't go far enough below the horizon), the lights scheduler will print a message and keep the lights in their current state until the next day.

---

## Sensors

The sensors command reads temperature, humidity, and barometric pressure from a BME280 sensor and logs the data to a CSV file.

### Start logging

```bash
salmoncv-sensors
```

This logs a reading every 2 seconds to `~/salmoncv/data/sensor_log.csv`. Press **Ctrl+C** to stop.

### Change the log file location

```bash
salmoncv-sensors --logfile ~/salmoncv/data/weather.csv
```

### Change the reading interval

Log every 30 seconds:

```bash
salmoncv-sensors --interval 30
```

### All sensor options

| Option | Default | Description |
|--------|---------|-------------|
| `--logfile` | `~/salmoncv/data/sensor_log.csv` | Path to log file |
| `--interval` | `2.0` | Seconds between readings |

### Log file format

The CSV file contains one row per reading:

```
timestamp,temperature_c,temperature_f,humidity,pressure_hpa
2026-05-11 14:30:00,18.45,65.21,72.31,1013.25
```

The log file is appended to — it keeps growing across runs. It will not overwrite previous data.

---

## Starlink

The Starlink scheduler manages when the Starlink terminal powers on and off. By default, it calculates how long the upload window needs to be based on the number of new images captured since the last upload and an estimated upload speed.

### Automatic mode

```bash
salmoncv-starlink
```

This checks every hour for new images in `~/salmoncv/captures/`. When new images are found, it:

1. Calculates the upload window based on image count and file sizes
2. Adds 5 minutes for Starlink boot time
3. Powers on Starlink
4. Waits for the upload window to finish
5. Powers off Starlink
6. Marks the images as uploaded so they are not counted again

### Fixed daily schedule

Turn Starlink on at 2 AM for 30 minutes:

```bash
salmoncv-starlink --on-time 02:00 --upload-time 30
```

### Fixed window, auto timing

Skip the bandwidth calculation and use a 45-minute window whenever new images are found:

```bash
salmoncv-starlink --upload-time 45
```

### Adjust upload speed estimate

If your Starlink connection is faster or slower than 5 Mbps:

```bash
salmoncv-starlink --upload-speed 10
```

### Check without toggling

```bash
salmoncv-starlink --dry-run
```

### Admin window

By default, Starlink powers on every day at 12:00 PM for 15 minutes so you can SSH in, push code updates, or check settings. This happens automatically even if there are no images to upload.

Change the admin time:

```bash
salmoncv-starlink --admin-time 08:00 --admin-duration 20
```

Disable the admin window:

```bash
salmoncv-starlink --admin-time off
```

### All Starlink options

| Option | Default | Description |
|--------|---------|-------------|
| `--capture-dir` | `~/salmoncv/captures` | Directory to scan for images |
| `--upload-speed` | `5.0` | Estimated upload speed in Mbps |
| `--boot-buffer` | `300` | Seconds for Starlink to boot (5 min) |
| `--check-interval` | `3600` | Seconds between checks (1 hour) |
| `--on-time` | auto | Fixed daily start time (HH:MM) |
| `--upload-time` | auto | Fixed window in minutes |
| `--admin-time` | `12:00` | Daily admin window start (HH:MM, or "off") |
| `--admin-duration` | `15` | Admin window length in minutes |
| `--logfile` | `~/salmoncv/data/starlink_log.csv` | Log file path |
| `--manifest` | `~/salmoncv/data/upload_manifest.csv` | Upload tracking file |
| `--dry-run` | off | Print plan without toggling |

### Log files

The Starlink scheduler creates two files:

- **`~/salmoncv/data/starlink_log.csv`** — Every event: scheduler start/stop, window open/close, no new images
- **`~/salmoncv/data/upload_manifest.csv`** — Tracks which images have been "uploaded" so they are not counted again

### Important note

The scheduler manages the **power window** — it does not perform the actual file upload. A future upload script will handle transferring files to a remote server during the window.

---

## Power

The power command turns lights and Starlink on or off immediately. Use this for manual control and testing.

### Turn lights on and off

```bash
salmoncv-power lights-on
salmoncv-power lights-off
```

### Turn Starlink on and off

```bash
salmoncv-power starlink-on
salmoncv-power starlink-off
```

### Turn everything on or off

```bash
salmoncv-power all-on
salmoncv-power all-off
```

### Test relays

This turns the lights on for 5 seconds, then the Starlink for 5 seconds:

```bash
salmoncv-power test
```

### Timed control

Turn lights on in 3 minutes, keep them on for 1 minute, then turn off:

```bash
sleep 180 && salmoncv-power lights-on && sleep 60 && salmoncv-power lights-off
```

### GPIO pin assignments

| Pin | Relay | Load |
|-----|-------|------|
| GPIO17 | IN1 | LED lights |
| GPIO27 | IN2 | Starlink |

---

## Watchdog

The watchdog is a safety check that prevents lights or Starlink from draining the battery if the scheduler crashes or someone forgets to turn a relay off.

It enforces two rules:

- **Lights**: cannot stay on longer than the night duration plus a 1-hour buffer (calculated daily from civil twilight for Quinhagak)
- **Starlink**: cannot stay on longer than 3 hours

### Run manually

```bash
salmoncv-watchdog
```

This checks both relays and forces them off if they have been on too long.

### Set up automatic checks with cron

To run the watchdog every 15 minutes automatically, add a cron entry:

```bash
crontab -e
```

Add this line:

```
*/15 * * * * /home/nalaquq/salmoncv/venv/bin/salmoncv-watchdog >> /home/nalaquq/salmoncv/data/watchdog_cron.log 2>&1
```

Save and exit. The watchdog will now run every 15 minutes in the background.

### What happens when the watchdog forces a relay off

It logs the event to `~/salmoncv/data/watchdog_log.csv` with the relay name and how long it was on. You can review this file to see if anything went wrong.

### When does the watchdog help?

- Scheduler crashes while a relay is on
- You run `salmoncv-power starlink-on` and forget to turn it off
- The tmux session dies during an upload window
- Any unexpected situation where a relay stays on too long

### When does the watchdog NOT help?

- The Pi reboots — GPIO pins reset to LOW automatically, so relays turn off on their own
- The Pi loses power completely — no power means no relay

---

## GPIO Probe

If you are wiring a new relay board and need to figure out which GPIO pin controls which relay, use the probe tool:

```bash
salmoncv-probe
```

It tests each common GPIO pin one at a time. Press Enter to test each pin and listen for the relay click.

---

## Running Commands in the Background

If your SSH or Raspberry Pi Connect session drops, any running command will stop. To keep commands running after you disconnect, use `tmux`:

### Start a background session

```bash
tmux new -s camera
salmoncv-camera --no-inference --outdir ~/salmoncv/captures
```

Press **Ctrl+B** then **D** to detach (the command keeps running).

### Reconnect to a session

```bash
tmux attach -t camera
```

### List running sessions

```bash
tmux ls
```

### Run multiple services

```bash
tmux new -s camera -d "salmoncv-camera --no-inference --outdir ~/salmoncv/captures"
tmux new -s lights -d "salmoncv-lights"
tmux new -s sensors -d "salmoncv-sensors --interval 30"
tmux new -s starlink -d "salmoncv-starlink"
```

---

## Viewing Log Files

### Sensor log

```bash
cat ~/salmoncv/data/sensor_log.csv
```

Or view just the last 10 lines:

```bash
tail ~/salmoncv/data/sensor_log.csv
```

### Capture log

```bash
cat ~/salmoncv/captures/capture_log.csv
```

### Count how many images have been captured

```bash
ls ~/salmoncv/captures/*.jpg | wc -l
```

### Check disk space

```bash
df -h
```

---

## Troubleshooting

### "command not found" when running salmoncv-camera (or any command)

You need to activate the virtual environment and install the package:

```bash
cd ~/salmoncv
source venv/bin/activate
pip install -e .
```

### Camera error: "Pipeline handler in use by another process"

Something else is using the camera. Find and stop it:

```bash
ps aux | grep -i cam
sudo pkill -f rpicam
```

If that does not work, reboot:

```bash
sudo reboot
```

### BME280 sensor not detected

Check that the sensor is wired to the I2C bus:

```bash
sudo i2cdetect -y 1
```

You should see `76` or `77` in the grid. If the grid is empty, check your wiring.

### Lights turn on but turn off immediately

Make sure you have the latest code:

```bash
cd ~/salmoncv
git pull
pip install -e .
```

Older versions used `gpiozero` which resets GPIO pins when the process exits. The current version uses `pinctrl` which keeps the state.

### Coral TPU not detected

Unplug and replug the Coral USB Accelerator, then check:

```bash
lsusb
```

You should see a Google device listed. If not, try a different USB port or reboot.

### How to check if services are still running

```bash
tmux ls
```

This shows all running tmux sessions. If a session is missing, the service inside it crashed or was stopped.

---

## Web Dashboard

The web dashboard lets you control everything from a phone or tablet browser — no terminal needed.

### Start the dashboard

```bash
sudo salmoncv-web
```

This starts the web server on port 80. Open a browser and go to the Pi's IP address (e.g., `http://192.168.4.1` if using the hotspot, or `http://nalaquqpi.local` on local Wi-Fi).

### Development mode

```bash
salmoncv-web --port 5000 --debug
```

### Dashboard pages

| Page | What it shows |
|------|---------------|
| **Dashboard** | At-a-glance status of camera, sensors, lights, Starlink, and system |
| **Camera** | Take a single photo with live preview, start/stop time-lapse, set interval and resolution |
| **Gallery** | Browse captured images as thumbnails, click to view full size |
| **Sensors** | Live temperature, humidity, and pressure readings (updates every 5 seconds), history table |
| **Power** | Toggle lights and Starlink on/off, view schedules, check upload queue |
| **Settings** | System info (hostname, uptime, CPU temp), disk usage, download log files |

### Wi-Fi hotspot

To let field users connect directly to the Pi without an existing Wi-Fi network, set up the hotspot:

```bash
sudo bash scripts/setup_hotspot.sh
sudo reboot
```

After reboot, connect your phone to the **SalmonCV** Wi-Fi network, then open `http://192.168.4.1` in a browser.

See [hotspot-setup.md](hotspot-setup.md) for full details.

### Run in the background

```bash
tmux new -d -s web 'sudo salmoncv-web'
```

---

## Quick Reference Card

```
# Activate environment (do this first every time)
cd ~/salmoncv && source venv/bin/activate

# Camera
salmoncv-camera --no-inference --outdir ~/salmoncv/captures
salmoncv-camera --no-inference --outdir ~/salmoncv/captures --interval 10

# Lights
salmoncv-lights                          # auto sunset/sunrise
salmoncv-lights --on-time 20:00 --off-time 06:30   # custom schedule
salmoncv-lights --dry-run                # test without toggling

# Starlink
salmoncv-starlink                        # auto window based on images
salmoncv-starlink --on-time 02:00 --upload-time 30  # daily at 2 AM
salmoncv-starlink --dry-run              # test without toggling

# Sensors
salmoncv-sensors                         # log every 2s
salmoncv-sensors --interval 30           # log every 30s

# Power (immediate on/off)
salmoncv-power lights-on
salmoncv-power lights-off
salmoncv-power starlink-on
salmoncv-power starlink-off
salmoncv-power test

# Watchdog (run manually or via cron)
salmoncv-watchdog                        # check and enforce max durations

# Background sessions
tmux new -s camera    # start session
Ctrl+B then D         # detach
tmux attach -t camera # reconnect
tmux ls               # list sessions
```
