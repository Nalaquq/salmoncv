# Lights

SalmonCV controls 12V LED floodlights through a relay on GPIO pin 17. The lights scheduler automatically turns lights on at dusk and off at dawn based on civil twilight calculations for Quinhagak, Alaska.

## How It Works

The scheduler calculates civil twilight (dawn and dusk) for Quinhagak each day using the `astral` library. Lights turn on at dusk and off at dawn. During midnight sun (summer), the scheduler detects that no twilight exists and keeps lights off.

## Quick Control (CLI)

Turn lights on or off immediately:

```bash
salmoncv-power lights-on
salmoncv-power lights-off
```

## Automatic Scheduling

Start the lights scheduler with default settings (civil twilight at Quinhagak):

```bash
salmoncv-lights
```

The scheduler:

1. Calculates dawn and dusk for today
2. Turns lights on at dusk
3. Turns lights off at dawn
4. Recalculates daily

### Custom Location

```bash
salmoncv-lights --lat 60.5 --lon -160.3 --timezone America/Anchorage
```

### Manual Times

Override sunset/sunrise with fixed times:

```bash
salmoncv-lights --on-time 20:00 --off-time 06:00
```

You can also override just one:

```bash
salmoncv-lights --on-time 19:30  # manual on, auto off at dawn
```

### Dry Run

Preview the schedule without toggling the relay:

```bash
salmoncv-lights --dry-run
```

## Web Dashboard Controls

The [Power page](web-dashboard.md#power) lets you:

- Toggle lights on/off immediately
- Start/stop the lights scheduler
- Switch between Auto (civil twilight) and Manual mode
- Set custom on/off times

## Lights Log

All events are logged to `~/salmoncv/data/lights_log.csv`:

| Column | Description |
|--------|-------------|
| timestamp | When the event occurred |
| event | scheduler_start, schedule_set, lights_on, lights_off, no_twilight, scheduler_stop |
| scheduled_on | Scheduled on time |
| scheduled_off | Scheduled off time |
| mode | auto, manual, or mixed |

## Safety Watchdog

The [watchdog](power.md#watchdog) enforces a maximum on-duration for lights based on night length plus a 1-hour buffer. If the scheduler crashes and leaves lights on, the watchdog will force them off.

## CLI Reference

```
salmoncv-lights [OPTIONS]

  --lat FLOAT          Latitude (default: 59.748 — Quinhagak)
  --lon FLOAT          Longitude (default: -161.922)
  --timezone STRING    Timezone (default: America/Anchorage)
  --on-time HH:MM     Manual lights-on time (overrides dusk)
  --off-time HH:MM    Manual lights-off time (overrides dawn)
  --check-interval SEC Seconds between checks (default: 60)
  --logfile PATH       Log file path
  --dry-run            Preview without toggling GPIO
```
