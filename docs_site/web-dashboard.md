# Web Dashboard

The web dashboard lets you control everything from a phone or tablet browser --- no SSH or terminal needed.

## Connecting

| Method | Address |
|--------|---------|
| **Wi-Fi hotspot** | Connect to `SalmonCV`, open **http://192.168.4.1** |
| **Local network** | Open **http://nalaquqpi.local** |

The dashboard starts automatically on boot.

## Pages

### Dashboard

The main landing page with:

- **Start Counting** --- one button to launch camera, sensors, lights, and Starlink all at once
- **Stop All** --- shut down all services
- Live status badges for each service
- Configurable capture interval and sensor interval
- Storage selector (Auto / Samsung T9 / SD Card) with usage bars

### Camera

- **Quick Capture** --- take a single photo and preview it in the browser
- **Time-Lapse** --- start/stop continuous capture with configurable interval and resolution
- **Auto/Manual toggle** for camera settings:
    - **Shutter speed** (microseconds) --- freeze fast-moving fish
    - **Gain / ISO** --- control noise in low light
    - **White balance** --- auto, daylight, cloudy, tungsten, fluorescent, incandescent, indoor
    - **Exposure compensation** --- +/- stops to brighten or darken

### Gallery

- Thumbnail grid of all captured images (newest first)
- Click any thumbnail to view full-size in a lightbox
- **Select mode** --- tap images to select, then delete individually or in bulk
- **Select All** / **Select None** for batch operations
- Pagination (50 images per page)

### Sensors

- Live temperature (°F/°C), humidity (%), and pressure (hPa) --- updates every 5 seconds
- Recent history table from sensor_log.csv
- Download CSV button for the full sensor log

### Monitor

- **Power Draw** --- estimated watts per component (Pi, camera, lights, Starlink, SSD) with color-coded bar
- **Environmental Charts** --- temperature, humidity, and pressure plotted over time with threshold lines
- **Case Health** --- CPU temp and case temp/humidity side by side to detect overheating or seal failure
- Configurable history range: last 50 to 1000 data points

### Power

- **Relay Control** --- toggle lights and Starlink on/off immediately
- **Lights Scheduler** --- start/stop with auto (civil twilight) or manual on/off times
- **Starlink Scheduler** --- start/stop with auto (bandwidth calculation) or manual daily time
- Configurable upload speed, admin window time and duration
- Current dawn/dusk times and pending upload queue

### Settings

- System info: hostname, uptime, CPU temperature
- Storage: Samsung T9 and SD card usage with progress bars
- Active storage drive and capture directory
- Download all log files (sensor, lights, Starlink, watchdog, capture, web activity)

## Activity Logging

Every action taken through the dashboard is logged to `~/salmoncv/data/web_log.csv`:

- Photo captures and time-lapse start/stop
- Power toggles (lights, Starlink)
- Scheduler start/stop
- Storage mode changes
- Image deletions

The log includes timestamps and client IP addresses for field troubleshooting.
