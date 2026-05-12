# Power & Watchdog

SalmonCV controls two relay channels via GPIO to manage power to external devices:

| Relay | GPIO Pin | Controls |
|-------|----------|----------|
| Channel 1 | GPIO 17 | LED floodlights |
| Channel 2 | GPIO 27 | Starlink terminal |

## Relay Control (CLI)

```bash
salmoncv-power lights-on
salmoncv-power lights-off
salmoncv-power starlink-on
salmoncv-power starlink-off
salmoncv-power all-off
```

### Test Relays

Toggle each relay for 5 seconds to verify wiring:

```bash
salmoncv-power test
```

### Identify Wiring

If you're unsure which GPIO pin controls which relay:

```bash
salmoncv-probe
```

This cycles through GPIO pins one at a time so you can observe which relay clicks.

## How It Works

Relays are controlled using `pinctrl` (built into Raspberry Pi 5). The pin is driven high to activate the relay and low to deactivate. State files track when each relay was turned on:

- `~/salmoncv/data/.lights_on_since` --- ISO timestamp when lights were turned on
- `~/salmoncv/data/.starlink_on_since` --- ISO timestamp when Starlink was turned on

These files are created when a relay turns on and deleted when it turns off.

## Hardware Setup

The relay board connects to the Pi's GPIO header:

| Relay Board | Pi Pin |
|-------------|--------|
| VCC | 5V (pin 2) |
| GND | Ground (pin 9) |
| IN1 (lights) | GPIO 17 (pin 11) |
| IN2 (Starlink) | GPIO 27 (pin 13) |

The relay board drives automotive relays that switch the 12V loads (lights and Starlink).

## Watchdog

The watchdog is a safety check that forces relays off if they've been on too long. This protects against scheduler crashes or bugs that could drain the battery.

### Limits

| Relay | Max Duration | How Calculated |
|-------|-------------|----------------|
| Lights | Night length + 1 hour | Civil twilight for Quinhagak, recalculated daily |
| Starlink | 3 hours | Fixed limit |

### Run Manually

```bash
salmoncv-watchdog
```

### Automatic (Cron)

Add to crontab to run every 30 minutes:

```bash
crontab -e
```

```
*/30 * * * * /home/nalaquq/salmoncv/venv/bin/salmoncv-watchdog >> /home/nalaquq/salmoncv/data/watchdog_cron.log 2>&1
```

### Watchdog Log

Forced shutoffs are logged to `~/salmoncv/data/watchdog_log.csv`:

| Column | Description |
|--------|-------------|
| timestamp | When the check ran |
| event | forced_off |
| relay | lights or starlink |
| on_duration_min | How long the relay had been on |

## Web Dashboard

The [Power page](web-dashboard.md#power) provides browser-based control:

- Toggle lights and Starlink on/off
- Start/stop lights and Starlink schedulers
- Configure auto (civil twilight / bandwidth) or manual mode
- View current dawn/dusk times and upload queue

## CLI Reference

```
salmoncv-power COMMAND

  lights-on       Turn lights on
  lights-off      Turn lights off
  starlink-on     Turn Starlink on
  starlink-off    Turn Starlink off
  all-on          Turn both on
  all-off         Turn both off
  test            Toggle each relay for 5 seconds

salmoncv-watchdog
  Checks relay durations and forces off if exceeded
```
